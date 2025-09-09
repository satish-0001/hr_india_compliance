import frappe
from datetime import datetime, timedelta
import itertools
from frappe.model.document import Document
from frappe.utils import cint, create_batch, get_datetime, get_time, getdate
from erpnext.setup.doctype.employee.employee import get_holiday_list_for_employee
from erpnext.setup.doctype.holiday_list.holiday_list import is_holiday
from frappe.utils.data import add_months, get_first_day, get_last_day, today
from hrms.hr.doctype.attendance.attendance import mark_attendance
from hrms.hr.doctype.employee_checkin.employee_checkin import (
	calculate_working_hours,
	mark_attendance_and_link_log,
)
from hrms.hr.doctype.shift_assignment.shift_assignment import get_employee_shift, get_shift_details
from hrms.payroll.doctype.salary_slip.salary_slip import HOLIDAYS_BETWEEN_DATES
from hrms.utils import get_date_range
from hrms.utils.holiday_list import get_holiday_dates_between
EMPLOYEE_CHUNK_SIZE = 50


@frappe.whitelist()
def plant_wise_attendance(shift_type_name,plant):
    doc=frappe.get_doc("Shift Type",shift_type_name)
    if (
        not cint(doc.enable_auto_attendance)
        or not doc.process_attendance_after
        or not doc.last_sync_of_checkin
    ):
        
        return
    
    logs = get_employee_checkins_plant_wise(doc,plant)
    # p = [item['plant'] for item in logs]
    # plants_map = list(map(lambda item: item['plant'], logs))
    # print("plant_wise vvvvvvvvvvvvvvvv",plants_map)
    

    for key, group in itertools.groupby(logs, key=lambda x: (x["employee"], x["shift_start"])):
        single_shift_logs = list(group)
        attendance_date = key[1].date()
        employee = key[0]

        if not should_mark_attendance(doc,employee, attendance_date):
            continue

        (
            attendance_status,
            working_hours,
            late_entry,
            early_exit,
            in_time,
            out_time,
        ) = get_attendance(doc,single_shift_logs)

        mark_attendance_and_link_log(
            single_shift_logs,
            attendance_status,
            attendance_date,
            working_hours,
            late_entry,
            early_exit,
            in_time,
            out_time,
            doc.name,
        )

    # commit after processing checkin logs to avoid losing progress
    frappe.db.commit()  # nosemgrep

    assigned_employees = get_assigned_employees_plant_wise(doc,plant,doc.process_attendance_after, True)
    print("hhhhhhhhhhhhhhhhhh",assigned_employees)
    # mark absent in batches & commit to avoid losing progress since this tries to process remaining attendance
    # right from "Process Attendance After" to "Last Sync of Checkin"
    for batch in create_batch(assigned_employees, EMPLOYEE_CHUNK_SIZE):
        for employee in batch:
            mark_absent_for_dates_with_no_attendance(doc,employee)

        frappe.db.commit()  # nosemgrep

def get_employee_checkins_plant_wise(doc,plant) -> list[dict]:
    return frappe.get_all(
        "Employee Checkin",
        fields=[
            "name",
            "employee",
            "log_type",
            "time",
            "shift",
            "shift_start",
            "shift_end",
            "shift_actual_start",
            "shift_actual_end",
            "device_id",
            "plant"
        ],
        filters={
            "skip_auto_attendance": 0,
            "attendance": ("is", "not set"),
            "time": (">=", doc.process_attendance_after),
            "shift_actual_end": ("<=", doc.last_sync_of_checkin),
            "shift": doc.name,
            "plant":plant
        },
        order_by="employee,time",
    )
def get_assigned_employees_plant_wise(doc,plant, from_date=None, consider_default_shift=False) -> list[str]:
    filters = {"shift_type": doc.name,"custom_plant":plant, "docstatus": "1", "status": "Active"}
    print("filter-----",filters)
    if from_date:
        filters["start_date"] = (">=", from_date)

    assigned_employees = frappe.get_all("Shift Assignment", filters=filters, pluck="employee")

    if consider_default_shift:
        default_shift_employees =get_employees_with_default_shift_plant_wise(doc,plant,filters)
        assigned_employees = set(assigned_employees + default_shift_employees)

    # exclude inactive employees
    inactive_employees = frappe.db.get_all("Employee", {"status": "Inactive","branch":plant}, pluck="name")
    print("************",list(set(assigned_employees) - set(inactive_employees)))
    return list(set(assigned_employees) - set(inactive_employees))

def get_employees_with_default_shift_plant_wise(doc,plant ,filters: dict) -> list:
    default_shift_employees = frappe.get_all(
        "Employee", filters={"default_shift": doc.name, "status": "Active","branch":plant}, pluck="name"
    )

    if not default_shift_employees:
        return []

    # exclude employees from default shift list if any other valid shift assignment exists
    del filters["shift_type"]
    filters["employee"] = ("in", default_shift_employees)

    active_shift_assignments = frappe.get_all(
        "Shift Assignment",
        filters=filters,
        pluck="employee",
    )

    return list(set(default_shift_employees) - set(active_shift_assignments))
# --------------------------------------------------------------------------------------------

@frappe.whitelist()
def process_auto_attendance_employee_wise(shift_type_name,selected_employee):
    doc=frappe.get_doc("Shift Type",shift_type_name)
    if (
        not cint(doc.enable_auto_attendance)
        or not doc.process_attendance_after
        or not doc.last_sync_of_checkin
    ):
        return
    
    logs = get_employee_checkins(doc,selected_employee)
    print("Employee Checkin Logs:--->",logs)
    

    for key, group in itertools.groupby(logs, key=lambda x: (x["employee"], x["shift_start"])):
        single_shift_logs = list(group)
        attendance_date = key[1].date()
        employee = key[0]

        if not should_mark_attendance(doc,employee, attendance_date):
            continue

        (
            attendance_status,
            working_hours,
            late_entry,
            early_exit,
            in_time,
            out_time,
        ) = get_attendance(doc,single_shift_logs)

        mark_attendance_and_link_log(
            single_shift_logs,
            attendance_status,
            attendance_date,
            working_hours,
            late_entry,
            early_exit,
            in_time,
            out_time,
            doc.name,
        )

    # commit after processing checkin logs to avoid losing progress
    frappe.db.commit()  # nosemgrep

    assigned_employees = get_assigned_employees_normally(doc,selected_employee,doc.process_attendance_after, True)
    print("Assigned employees:---------------->",assigned_employees)
    # mark absent in batches & commit to avoid losing progress since this tries to process remaining attendance
    # right from "Process Attendance After" to "Last Sync of Checkin"
    for batch in create_batch(assigned_employees, EMPLOYEE_CHUNK_SIZE):
        print("batch:----------->",batch)
        for employee in batch:
            mark_absent_for_dates_with_no_attendance(doc,employee)

        frappe.db.commit()  # nosemgrep

def get_employee_checkins(doc,selected_employee) -> list[dict]:
    return frappe.get_all(
        "Employee Checkin",
        fields=[
            "name",
            "employee",
            "log_type",
            "time",
            "shift",
            "shift_start",
            "shift_end",
            "shift_actual_start",
            "shift_actual_end",
            "device_id",
        ],
        filters={
            "skip_auto_attendance": 0,
            "attendance": ("is", "not set"),
            "time": (">=", doc.process_attendance_after),
            "shift_actual_end": ("<=", doc.last_sync_of_checkin),
            "shift": doc.name,
            "employee": selected_employee,
            
        },
        order_by="employee,time",
    )

# --------------------------------------------------------------------------------------------------------------

def get_attendance(doc, logs):
    """Return attendance_status, working_hours, late_entry, early_exit, in_time, out_time
    for a set of logs belonging to a single shift.
    Assumptions:
    1. These logs belongs to a single shift, single employee and it's not in a holiday date.
    2. Logs are in chronological order
    """
    late_entry = early_exit = False
    total_working_hours, in_time, out_time = calculate_working_hours(
        logs, doc.determine_check_in_and_check_out, doc.working_hours_calculation_based_on
    )
    if (
        cint(doc.enable_entry_grace_period)
        and in_time
        and in_time > logs[0].shift_start + timedelta(minutes=cint(doc.late_entry_grace_period))
    ):
        late_entry = True

    if (
        cint(doc.enable_exit_grace_period)
        and out_time
        and out_time < logs[0].shift_end - timedelta(minutes=cint(doc.early_exit_grace_period))
    ):
        early_exit = True

    if (
        doc.working_hours_threshold_for_absent
        and total_working_hours < doc.working_hours_threshold_for_absent
    ):
        return "Absent", total_working_hours, late_entry, early_exit, in_time, out_time

    if (
        doc.working_hours_threshold_for_half_day
        and total_working_hours < doc.working_hours_threshold_for_half_day
    ):
        return "Half Day", total_working_hours, late_entry, early_exit, in_time, out_time

    return "Present", total_working_hours, late_entry, early_exit, in_time, out_time

def mark_absent_for_dates_with_no_attendance(doc, employee: str):
    """Marks Absents for the given employee on working days in this shift that have no attendance marked.
    The Absent status is marked starting from 'process_attendance_after' or employee creation date.
    """
    start_time = get_time(doc.start_time)
    dates = get_dates_for_attendance(doc,employee)

    for date in dates:
        timestamp = datetime.combine(date, start_time)
        shift_details = get_employee_shift(employee, timestamp, True)

        if shift_details and shift_details.shift_type.name == doc.name:
            attendance = mark_attendance(employee, date, "Absent", doc.name)

            if not attendance:
                continue

            frappe.get_doc(
                {
                    "doctype": "Comment",
                    "comment_type": "Comment",
                    "reference_doctype": "Attendance",
                    "reference_name": attendance,
                    "content": frappe._("Employee was marked Absent due to missing Employee Checkins."),
                }
            ).insert(ignore_permissions=True)

def get_dates_for_attendance(doc, employee: str) -> list[str]:
    start_date, end_date = get_start_and_end_dates(doc,employee)

    # no shift assignment found, no need to process absent attendance records
    if start_date is None:
        return []

    date_range = get_date_range(start_date, end_date)

    # skip marking absent on holidays
    holiday_list = get_holiday_list(doc,employee)
    holiday_dates = get_holiday_dates_between(holiday_list, start_date, end_date)

    if frappe.db.get_single_value("Payroll Settings","custom_consider_holidays_from_shift_assignment"):
        shift_assignment_holidays = get_holidays_from_shift_assignment(
            employee=employee,
            start_date=start_date,
            end_date=end_date,
            existing_holiday_list=holiday_dates
        )

        if shift_assignment_holidays:

            # skip dates with attendance
            marked_attendance_dates = get_marked_attendance_dates_between(doc,
                employee, start_date, end_date
            )

            return sorted(set(date_range) - set(shift_assignment_holidays) - set(marked_attendance_dates))
        
        else:
            # skip dates with attendance
            marked_attendance_dates = get_marked_attendance_dates_between(doc,
                employee, start_date, end_date
            )

            return sorted(set(date_range) - set(holiday_dates) - set(marked_attendance_dates))
    else:
        # skip dates with attendance
        marked_attendance_dates = get_marked_attendance_dates_between(doc,
            employee, start_date, end_date
        )

        return sorted(set(date_range) - set(holiday_dates) - set(marked_attendance_dates))


def get_holidays_from_shift_assignment(employee, start_date, end_date, existing_holiday_list=None):
    if existing_holiday_list is None:
        existing_holiday_list = []

    shift_type_holiday = frappe.get_all("Shift Assignment", {
        "employee": employee,
        "docstatus": 1,
        "start_date": ["<=", end_date],
        "end_date": [">=", start_date]
    }, ["name", "holiday", "start_date", "end_date"])

    shift_holidays = []
    for holiday in shift_type_holiday:
        key = f"{holiday.get('holiday')}:{holiday.start_date}:{holiday.end_date}"
        holiday_dates = frappe.cache().hget(HOLIDAYS_BETWEEN_DATES, key)

        if not holiday_dates:
            holiday_dates = get_holiday_dates_between(holiday.get('holiday'), holiday.start_date, holiday.end_date)
            frappe.cache().hset(HOLIDAYS_BETWEEN_DATES, key, holiday_dates)
        

        existing_holiday_list = [
            x for x in existing_holiday_list 
            if not (getdate(x) >= getdate(holiday.get('start_date')) and getdate(x) <= getdate(holiday.get('end_date')))
        ]
        
        shift_holidays.extend(holiday_dates)

    shift_holidays.extend(existing_holiday_list)
    if shift_holidays:
        return set(shift_holidays)


def get_start_and_end_dates(doc, employee):
    """Returns start and end dates for checking attendance and marking absent
    return: start date = max of `process_attendance_after` and DOJ
    return: end date = min of shift before `last_sync_of_checkin` and Relieving Date
    """
    date_of_joining, relieving_date, employee_creation = frappe.get_cached_value(
        "Employee", employee, ["date_of_joining", "relieving_date", "creation"]
    )

    if not date_of_joining:
        date_of_joining = employee_creation.date()

    start_date = max(getdate(doc.process_attendance_after), date_of_joining)
    end_date = None

    shift_details = get_shift_details(doc.name, get_datetime(doc.last_sync_of_checkin))
    last_shift_time = (
        shift_details.actual_end if shift_details else get_datetime(doc.last_sync_of_checkin)
    )

    # check if shift is found for 1 day before the last sync of checkin
    # absentees are auto-marked 1 day after the shift to wait for any manual attendance records
    prev_shift = get_employee_shift(employee, last_shift_time - timedelta(days=1), True, "reverse")
    if prev_shift and prev_shift.shift_type.name == doc.name:
        end_date = (
            min(prev_shift.start_datetime.date(), relieving_date)
            if relieving_date
            else prev_shift.start_datetime.date()
        )
    else:
        # no shift found
        return None, None
    return start_date, end_date

def get_marked_attendance_dates_between(
    doc, employee: str, start_date: str, end_date: str
) -> list[str]:
    Attendance = frappe.qb.DocType("Attendance")
    return (
        frappe.qb.from_(Attendance)
        .select(Attendance.attendance_date)
        .where(
            (Attendance.employee == employee)
            & (Attendance.docstatus < 2)
            & (Attendance.attendance_date.between(start_date, end_date))
            & ((Attendance.shift.isnull()) | (Attendance.shift == doc.name))
        )
    ).run(pluck=True)


def get_assigned_employees_normally(doc,selected_employee, from_date=None, consider_default_shift=False) -> list[str]:
    filters = {"shift_type": doc.name, "docstatus": "1", "status": "Active","employee":selected_employee}
    if from_date:
        filters["start_date"] = (">=", from_date)

    assigned_employees = frappe.get_all("Shift Assignment", filters=filters, pluck="employee")

    

    if consider_default_shift:
        default_shift_employees =get_employees_with_default_shift_normally(doc,selected_employee,filters)
        assigned_employees = set(assigned_employees + default_shift_employees)
    

    # exclude inactive employees
    inactive_employees = frappe.db.get_all("Employee", {"status": "Inactive","employee":selected_employee}, pluck="name")

    return list(set(assigned_employees) - set(inactive_employees))

def get_employees_with_default_shift_normally(doc,selected_employee,filters: dict) -> list:
    default_shift_employees = frappe.get_all(
        "Employee", filters={"default_shift": doc.name, "status": "Active","employee":selected_employee}, pluck="name"
    )

    if not default_shift_employees:
        return []

    # exclude employees from default shift list if any other valid shift assignment exists
    del filters["shift_type"]
    filters["employee"] = ("in", default_shift_employees)

    active_shift_assignments = frappe.get_all(
        "Shift Assignment",
        filters=filters,
        pluck="employee",
    )

    return list(set(default_shift_employees) - set(active_shift_assignments))


def get_holiday_list(doc, employee: str) -> str:
    holiday_list_name = doc.holiday_list or get_holiday_list_for_employee(employee, False)
    return holiday_list_name

def should_mark_attendance(doc, employee: str, attendance_date: str) -> bool:
    """Determines whether attendance should be marked on holidays or not"""
    if doc.mark_auto_attendance_on_holidays:
        # no need to check if date is a holiday or not
        # since attendance should be marked on all days
        return True

    holiday_list = get_holiday_list(doc,employee)
    if is_holiday(holiday_list, attendance_date):
        return False
    return True


@frappe.whitelist()
def update_process_attendance_after():
    today = frappe.flags.current_date or getdate()
    month_first_date = get_first_day(add_months(today,0))
    last_month_last_date = get_last_day(add_months(today,-1))
    if today != month_first_date:
        shift_types = frappe.db.get_all("Shift Type",{"enable_auto_attendance":1}) 
        for shift in shift_types:
            frappe.set_value("Shift Type",shift.name,"process_attendance_after",getdate(last_month_last_date))