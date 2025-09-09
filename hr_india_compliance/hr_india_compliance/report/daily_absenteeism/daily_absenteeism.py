import frappe
from datetime import timedelta
import datetime as dt
from frappe.utils.data import get_time, getdate, today, now_datetime

def execute(filters=None):
    columns = get_columns(filters)
    data = get_data(filters)
    # chart = get_chart_data(data)
    filters['shift'] = filters.get('shift', "")
    filters['employee_status'] = filters.get('employee_status', "")
    return columns, data #,None, chart

def get_columns(filters):
    columns = [
        {
            "fieldname": "department_name",
            "label": "Department",
            "fieldtype": "Data",
            "width": 170
        },
        {
            "fieldname": "emp_code",
            "label": "Employee",
            "fieldtype": "Link",
            "options": "Employee",
            "width": 170
        },
        {
            "fieldname": "payroll_cost_center",
            "label": "Payroll Cost Center",
            "fieldtype": "Link",
            "options": "Employee",
            "width": 170
        },
        {
            "fieldname": "emp_name",
            "label": "Employee Name",
            "fieldtype": "Data",
            "width": 170
        },
        {
            "fieldname": "emp_father",
            "label": "Employee Father's Name",
            "fieldtype": "Data",
            "width": 170
        },
        {
            "fieldname": "emp_designation",
            "label": "Designation",
            "fieldtype": "Link",
            "options": "Designation",
            "width": 170
        },
        {
            "fieldname": "status",
            "label": "Status",
            "fieldtype": "Data",
            "width": 170
        },
        {
            "fieldname": "shift",
            "label": "Shift",
            "fieldtype": "Link",
            "options": "Shift Type",
            "width": 170
        },
        {
            "fieldname": "attendance_device_id",
            "label": "Biometric ID",
            "fieldtype": "Data",
            "width": 170
        },
        {
            "fieldname": "time",
            "label": "Employee Checkin (Time)",
            "fieldtype": "Datetime",
            "width": 170
        },
        {
            "fieldname": "remarks",
            "label": "Remarks",
            "fieldtype": "Data",
            "width": 170
        },
    ]
    return columns

def get_condition(filters):
    conditions = ""
    if filters.get("plant"):
        conditions += " AND e.branch ='%s'" % filters.get('plant')
    if filters.get("department"):
        conditions += " AND e.department ='%s'" % filters.get('department')
    if filters.get("date"):
        conditions += " AND DATE(ec.time) ='%s'" % filters.get('date')
    return conditions

def get_dept_conditions(filters):
    dept_conditions = ""
    if filters.get("plant"):
        dept_conditions += " AND e.branch ='%s'" % filters.get('plant')
    if filters.get("department"):
        dept_conditions += " AND e.department ='%s'" % filters.get('department')
    if filters.get("shift"):
        dept_conditions += " AND e.default_shift ='%s'" % filters.get('shift')
    return dept_conditions

def get_data(filters):
    conditions = get_condition(filters)
    dept_conditions = get_dept_conditions(filters)

    departments = frappe.db.sql("""
        SELECT DISTINCT(e.department) as department
        FROM `tabEmployee` e
        WHERE e.status = "Active" {dept_conditions}
    """.format(dept_conditions=dept_conditions), as_dict=True)
    
    department_data = []
    for dept in departments:
        employees = frappe.db.sql("""
            SELECT e.name as emp_code, e.employee_name as emp_name, e.payroll_cost_center,
            e.f_h_name as emp_father, e.designation as emp_designation, e.branch, e.department,
            e.default_shift, e.attendance_device_id, e.holiday_list
            FROM `tabEmployee` e
            WHERE e.status = "Active" {dept_conditions} AND e.department='{0}'
        """.format(dept.department, dept_conditions=dept_conditions), as_dict=True)

        if dept.department:
            department_data.append({
                "department_name": "<b>{0}</b>".format(dept.department),
                "emp_code": "",
                "payroll_cost_center": "",
                "emp_name": "",
                "emp_father": "",
                "emp_designation": "",
                "status": "",
                "shift": "",
                "attendance_device_id": "",
                "time": "",
                "remarks": "",
                "indent": 0
            })

        for employee in employees:
            attendance_record = frappe.db.sql("""
                SELECT status FROM `tabAttendance`
                WHERE employee = '{0}' AND attendance_date = '{1}' AND status != 'Absent'
            """.format(employee.emp_code, filters.get("date")), as_dict=True)

            if attendance_record:
                continue

            checkin_data = frappe.db.sql("""
                SELECT ec.employee as emp_code, e.employee_name as emp_name, e.f_h_name as emp_father,
                ec.log_type, ec.time as checkin_time, e.default_shift, ec.shift_start as shift_start,
                ec.shift_end as shift_end, ec.shift, e.designation as emp_designation, e.branch,
                e.department, e.payroll_cost_center, e.attendance_device_id
                FROM `tabEmployee Checkin` ec
                JOIN `tabEmployee` e ON ec.employee = e.name
                WHERE e.status = 'Active' {conditions} AND e.department = '{0}' AND ec.employee = '{1}'
                ORDER BY ec.creation ASC LIMIT 1
            """.format(dept.department, employee.emp_code, conditions=conditions), as_dict=True)

            if not checkin_data:
                status = "Absent"
                holidays = frappe.db.sql("""
                    SELECT holiday_date, weekly_off FROM `tabHoliday`
                    WHERE holiday_date = '{0}' AND parent = '{1}'
                """.format(filters.get("date"), employee.holiday_list), as_dict=True)
                
                if holidays:
                    for holiday in holidays:
                        if holiday.weekly_off == 1:
                            status = "Weekly Off"
                        elif holiday.weekly_off == 0:
                            status = "Holiday"
                
                department_data.append({
                    "department_name": "",
                    "emp_code": employee.emp_code,
                    "payroll_cost_center": employee.payroll_cost_center,
                    "emp_name": employee.emp_name,
                    "emp_father": employee.emp_father,
                    "branch": employee.branch,
                    "status": status,
                    "emp_designation": employee.emp_designation,
                    "department": employee.department,
                    "attendance_device_id": employee.attendance_device_id,
                    "shift": employee.default_shift,
                    "time": "",
                    "remarks": "",
                    "indent": 1,
                    "indicator": "green" if status in ["Present", "Weekly Off", "Holiday"] else "red"
                })
            else:
                for row in checkin_data:
                    assigned_shift = get_assigned_shift(row.emp_code, filters.get("date"))
                    row.shift = assigned_shift if assigned_shift else row.default_shift

                    if row.default_shift:
                        shift_time = frappe.get_doc("Shift Type", row.default_shift)
                        shift_start_time = dt.datetime.combine(getdate(filters.get("date")), get_time(shift_time.start_time))
                        grace_period_time = shift_start_time + timedelta(minutes=shift_time.late_entry_grace_period)

                        if grace_period_time <= row.checkin_time:
                            late_time = row.checkin_time - shift_start_time
                            row.status = "Late"
                            row.time = row.checkin_time
                            row.remarks = f"Late by {late_time.seconds // 60} minutes"
                            row.indent = 1
                            row.indicator = "orange"
                            department_data.append(row)

    return department_data

def get_assigned_shift(emp_code, date):
    shift_assign = frappe.get_all(
        "Shift Assignment",
        filters={"employee": emp_code, "start_date": ("<=", date), "end_date": (">=", date)},
        fields=["shift_type"],
        order_by="creation desc",
        limit=1,
    )
    if shift_assign:
        return shift_assign[0].shift_type


# def get_chart_data(data):
#     chart_data = {
#         "data": {
#             "labels": [],
#             "datasets": []
#         },
#         "type": "pie"  # or "line", "pie", etc.
#     }
    
#     # Initialize status count
#     status_count = {"Absent": 0, "Late": 0, "Holiday": 0, "Weekly Off": 0}
    
#     # Iterate over data to count statuses
#     for row in data:
#         status = row.get("status")
#         if status and status in status_count:
#             status_count[status] += 1
    
#     chart_data["data"]["labels"] = list(status_count.keys())
#     chart_data["data"]["datasets"].append({
#         "name": "Employee Status",
#         "values": list(status_count.values())
#     })
    
#     return chart_data




