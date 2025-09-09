
import frappe
from frappe.utils.data import add_days, add_months, flt, get_datetime, get_link_to_form, get_time,getdate,getdate,add_years,get_first_day, get_last_day
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from hrms.hr.doctype.shift_type.shift_type import process_auto_attendance_for_all_shifts
from hrms.hr.utils import get_holiday_dates_for_employee, get_leave_allocations, get_monthly_earned_leave, round_earned_leaves
from frappe.utils import formatdate
from frappe.utils.background_jobs import enqueue


def update_season_details():
    attendance = frappe.db.sql("""SELECT a.attendance_date,a.plant,a.name
                FROM `tabAttendance` as a 
                LEFT JOIN `tabShift Type` as s on a.shift = s.name
                WHERE a.attendance_date IS NOT NULL
                AND a.attendance_date BETWEEN s.process_attendance_after AND DATE(s.last_sync_of_checkin)
                AND a.custom_season IS NULL
                AND a.status != "Absent" 
        """,as_dict=1)
    
    for att in attendance:
        get_season_data = get_season_details(att.plant)
        doc= frappe.get_doc("Attendance",att.name)
        if get_season_data:
            for season in get_season_data:
                if season:
                    attendance_date = getdate(att.attendance_date)
                    year_start_date = getdate(season.year_start_date)
                    year_end_date = getdate(season.year_end_date)
                    
                    if year_start_date <= attendance_date <= year_end_date:
                        doc.db_set("custom_season","Season")
                        # frappe.db.set_value("Attendance", att.name, "custom_season", "Season")
                    else:
                        doc.db_set("custom_season"," Off Season")
                        # frappe.db.set_value("Attendance", att.name, "custom_season", "Off Season")
                else:
                    doc.db_set("custom_season","Off Season")
                    # frappe.db.set_value("Attendance", att.name, "custom_season", "Off Season")
        else:
            doc.db_set("custom_season","Off Season")
            # frappe.db.set_value("Attendance", att.name, "custom_season", "Off Season")

                
    
def update_short_leave():
    get_att_data = get_att_data_for_update_short_leave()
    if get_att_data:
        for update_slc in get_att_data:
            if update_slc.shift and update_slc.in_time and update_slc.out_time and update_slc.attendance_date and update_slc.working_hours:

                shift = frappe.get_doc("Shift Type", update_slc.shift)

                emp = frappe.get_doc("Employee",update_slc.employee)
                actual_shift_hours = ((shift.end_time - shift.start_time).total_seconds()) / 3600

                shift_start_time = (datetime.min + shift.start_time).time()
                shift_end_time = (datetime.min + shift.end_time).time()
                shift_start_datetime = datetime.combine(getdate(update_slc.in_time), shift_start_time)
                shift_end_datetime = datetime.combine(getdate(update_slc.out_time), shift_end_time)
                
                in_time = get_time(update_slc.in_time)
                out_time = get_time(update_slc.out_time)
                in_time = max(in_time, shift_start_datetime.time())
                out_time = min(out_time, shift_end_datetime.time())
                
                time_difference = datetime.combine(getdate(update_slc.out_time), out_time) - datetime.combine(getdate(update_slc.in_time), in_time)
                emp_working_hours = round(time_difference.total_seconds() / 3600, 2)
                
                frappe.db.set_value("Attendance", update_slc.name, "custom_actual_working_hours",emp_working_hours)

                if shift.custom_threshold_for_short_leave:
                    threshold_time = float(shift.custom_threshold_for_short_leave) if float(shift.custom_threshold_for_short_leave) else 0.0
                    allowed_short_leave_time1 =actual_shift_hours-threshold_time
                    total_working_hours = float(update_slc.working_hours)

                    p_detail = get_plant_details(update_slc.plant)
                    if p_detail:
                        for plant_details in p_detail:
                            if plant_details: 
                                if emp.designation == update_slc.custom_designation == plant_details.designation:                    
                                    if plant_details.season_type == update_slc.custom_season:                         
                                        if plant_details.sw == "Yes" or plant_details.cpl == "Yes":                         
                                            if emp_working_hours <= allowed_short_leave_time1:                              
                                                frappe.db.set_value("Attendance", update_slc.name, "custom_short_leave", 1)
                                        if plant_details.sw == "No" and plant_details.cpl == "No":     
                                            if total_working_hours<=allowed_short_leave_time1:
                                                frappe.db.set_value("Attendance", update_slc.name, "custom_short_leave", 1)
                            if not plant_details:     
                                if total_working_hours<=allowed_short_leave_time1:
                                    frappe.db.set_value("Attendance", update_slc.name, "custom_short_leave", 1)
                    if not p_detail:
                        if total_working_hours<=allowed_short_leave_time1:
                            frappe.db.set_value("Attendance", update_slc.name, "custom_short_leave", 1)
                               
    
def get_season_details(branch):
    return frappe.get_all(
        "Season",
        filters={
            "plant":branch,
            "disabled":["!=",1]
        },
        fields=["year_start_date","year_end_date","name","disabled"]
    )



def get_plant_details(branch):
    return frappe.db.sql("""SELECT b.custom_allowed_short_leave,b.branch,
            s.designation,s.grade,grade_name,s.season_type,s.sw,s.cpl,s.fw
            FROM `tabBranch` as b
            INNER JOIN `tabSpecial Wages Details` as s on b.branch = s.parent
            WHERE b.branch = "{0}"
        """.format(branch),as_dict=1)



def get_att_data_for_update_short_leave():
    return frappe.db.sql("""SELECT a.employee,a.attendance_date,a.status,a.custom_designation,a.working_hours,
            a.department,a.custom_season,a.shift,a.late_entry,a.plant,a.early_exit,
            a.custom_short_leave,a.in_time,a.out_time,a.name,a.custom_actual_working_hours,
            s.name as shift_name,s.enable_auto_attendance,
            s.process_attendance_after,DATE(s.last_sync_of_checkin) as last_sync_date
            FROM `tabAttendance` as a 
            LEFT JOIN `tabShift Type` as s on a.shift = s.name
            WHERE a.custom_short_leave != 1
            AND a.status = "Present"
            AND a.attendance_date IS NOT NULL
            AND a.custom_actual_working_hours IS NULL
            AND a.shift IS NOT NULL
            AND a.attendance_date BETWEEN s.process_attendance_after AND DATE(s.last_sync_of_checkin)
        """,as_dict=1)



"****************************************************Custom Leave Allocation**************************************************************************"



def calculate_monthly_attendance(employee, period_start_date, period_end_date):
    holiday_count = 0.0
    full_day_count = 0.0
    half_day_count = 0.0
    work_from_home = 0.0
    emp = frappe.get_doc("Employee",employee)

    attendance_count = frappe.db.sql("""
		SELECT
			SUM(CASE WHEN status = 'present' THEN 1 ELSE 0 END) AS full_day_count,
			SUM(CASE WHEN status = 'Half Day' THEN 1 ELSE 0 END) AS half_day_count,
			SUM(CASE WHEN status = 'Work From Home' THEN 1 ELSE 0 END) AS work_from_home
							
		FROM `tabAttendance`
		WHERE employee = "{0}"
		AND attendance_date BETWEEN "{1}" AND "{2}"
        AND docstatus = 1
	""".format(employee, period_start_date, period_end_date), as_dict=1)

    holidays = frappe.db.sql("""select COUNT(holiday_date) as count 
                            FROM `tabHoliday` 
                            WHERE parent = "{0}" 
                            AND holiday_date BETWEEN "{1}" and "{2}" 
                        """.format(emp.holiday_list,period_start_date,period_end_date),as_dict=1)
    
    holiday_count = flt(holidays[0]["count"]) if flt(holidays[0]["count"]) else 0.0
    for att_count in attendance_count:
        full_day_count = att_count.full_day_count if att_count.full_day_count else 0.0
        half_day_count = att_count.half_day_count if att_count.half_day_count else 0.0
        work_from_home = att_count.work_from_home if att_count.work_from_home else 0.0

    return full_day_count, half_day_count, work_from_home,holiday_count

@frappe.whitelist()
def run_leave_allocation_method(MANUAL_RUN=None,FROM_DATE=None,TO_DATE=None):
    enqueue('hr_india_compliance.hr_india_compliance_utils.custom_leave_allocation_based_on_attendance',
            MANUAL_RUN=MANUAL_RUN,
            FROM_DATE=FROM_DATE,
            TO_DATE=TO_DATE,
            timeout=30000,
            queue="long"
        )

def custom_leave_allocation_based_on_attendance(MANUAL_RUN=None,FROM_DATE=None,TO_DATE=None):
    today = frappe.flags.current_date or getdate()
    print("today:---->",today)
    e_leave_types = get_earned_leaves()
    for e_leaave_type in e_leave_types:
        leave_allocations = get_leave_allocations(today,e_leaave_type.name)
        for allocation in leave_allocations:
            if not allocation.leave_policy_assignment and not allocation.leave_policy:
                continue
            leave_policy = (
                allocation.leave_policy 
                if allocation.leave_policy
                else frappe.db.get_value(
                    "Leave Policy Assignment",allocation.leave_policy_assignment,["leave_policy"]
                )
            )
            annual_allocation = frappe.db.get_value(
                "Leave Policy Detail",
                filters={"parent":leave_policy,"leave_type":e_leaave_type.name},
                fieldname=["annual_allocation"],
            )
            date_of_joining = frappe.db.get_value("Employee",allocation.employee,"date_of_joining")
            from_date = allocation.from_date
            if e_leaave_type.allocate_on_day == "Date Of Joining":
                from_date = date_of_joining
            if check_effective_date(
                from_date,today,e_leaave_type.earned_leave_frequency,e_leaave_type.allocate_on_day
            ):
                update_leave_allocation_based_on_attendance(
                    allocation,
                    annual_allocation,
                    e_leaave_type,
                    date_of_joining
                )
            else:
                if MANUAL_RUN == "True":
                    update_leave_allocation_based_on_attendance(
                        allocation,
                        annual_allocation,
                        e_leaave_type,
                        date_of_joining,
                        MANUAL_RUN="True",
                        FROM_DATE=FROM_DATE,
                        TO_DATE=TO_DATE
                    )

def update_leave_allocation_based_on_attendance(allocation,annual_allocation,e_leave_type,date_of_joining,MANUAL_RUN=None,FROM_DATE=None,TO_DATE=None):
    allocation = frappe.get_doc("Leave Allocation",allocation.name)
    annual_allocation = flt(annual_allocation, allocation.precision("total_leaves_allocated"))
    earned_leaves = get_monthly_earned_leave(
        date_of_joining,
        annual_allocation,
        e_leave_type.earned_leave_frequency,
        e_leave_type.rounding
    )

    if earned_leaves:
        new_allocation = flt(allocation.total_leaves_allocated) + flt(earned_leaves)
        new_allocation_without_cf = flt(
            flt(allocation.get_existing_leave_count()) + flt(earned_leaves),
            allocation.precision("total_leaves_allocated"),
        )

        if new_allocation > e_leave_type.max_leaves_allowed and e_leave_type.max_leaves_allowed > 0:
            new_allocation = e_leave_type.max_leaves_allowed

        if (
            new_allocation != allocation.total_leaves_allocated
            and new_allocation_without_cf <= annual_allocation
        ):
            today = frappe.flags.current_date or getdate()
            if e_leave_type.earned_leave_frequency == "Monthly":
                if MANUAL_RUN == "True":
                    period_start_date = getdate(FROM_DATE)
                    period_end_date = getdate(TO_DATE)
                    required_days = e_leave_type.custom_minimum_required_days*1
                else:
                    period_end_date = get_last_day(add_months(today,-1))
                    period_start_date = get_first_day(add_months(today,-1))
                    required_days = e_leave_type.custom_minimum_required_days*1
                print("Period Start Date:--->",period_start_date)
                print("Period End Date:--->",period_end_date)

            if e_leave_type.earned_leave_frequency == "Yearly":
                period_start_date = get_first_day(add_years(allocation.from_date, -1))
                period_end_date = get_last_day(add_years(allocation.to_date, -1))
                required_days=e_leave_type.custom_minimum_required_days*12

            if e_leave_type.earned_leave_frequency == "Half-Yearly":
                required_days= e_leave_type.custom_minimum_required_days*6
                period_start_date = get_first_day(add_months(today, -6))
                period_end_date = get_last_day(today)
            
            if e_leave_type.earned_leave_frequency == "Quarterly":
                required_days = e_leave_type.custom_minimum_required_days*3
                period_start_date = get_first_day(add_months(today, -3))
                period_end_date = get_last_day(today)

            (full_day_count,
            half_day_count, 
            work_from_home_count, 
            holiday_count) = calculate_monthly_attendance(allocation.employee,period_start_date,period_end_date)

            att_count = 0.0
            adjusted_leaves = 0.0

            if e_leave_type.custom_attendance_count_based_on == "Attendance":
                att_count = full_day_count + (0.5 * half_day_count) + work_from_home_count

            if e_leave_type.custom_attendance_count_based_on == "Leaves And Attendance":
                multiselect_leave_type = ""
                get_cond_det = frappe.db.sql(f"""
                                    SELECT leave_type 
                                    FROM `tabLeave Types For Attendance Count` 
                                    WHERE parent = '{allocation.leave_type}'
                                """, as_dict=1)

                if get_cond_det:
                    multiselect_leave_type = get_cond_det[0].get("leave_type")
                    condictional_count=0.0
                    leave_att_count = frappe.db.sql("""SELECT 
                                SUM(CASE WHEN leave_type = '{0}' THEN 1 ELSE 0 END) AS leave_type_att_count
                                FROM `tabAttendance` 
                                where employee = "{1}"
                                AND attendance_date BETWEEN "{2}" AND "{3}"
                                AND docstatus = 1
                            """.format(multiselect_leave_type,allocation.employee, period_start_date, period_end_date), as_dict=1)
                    
                    condictional_count = leave_att_count[0].get('leave_type_att_count') if leave_att_count[0].get('leave_type_att_count') else 0.0
                    att_count = full_day_count + (0.5 * half_day_count) + work_from_home_count + holiday_count + condictional_count

            if att_count >= flt(required_days):
                adjusted_leaves = earned_leaves - earned_leaves
   
            elif att_count >= flt(required_days / 2):
                adjusted_leaves = -earned_leaves / 2

            else:
                adjusted_leaves = -earned_leaves

            if not adjusted_leaves==0:
                new_leaves_allocated = allocation.new_leaves_allocated + adjusted_leaves
                new_leaves_allocated = round_earned_leaves(new_leaves_allocated,e_leave_type.rounding)
                new_total_leaves_allocated = allocation.total_leaves_allocated + adjusted_leaves
                new_total_leaves_allocated = round_earned_leaves(new_total_leaves_allocated,e_leave_type.rounding)
                allocation.db_set("new_leaves_allocated",new_leaves_allocated)
                allocation.db_set("total_leaves_allocated",new_total_leaves_allocated)
                            
                today_date = frappe.flags.current_date or getdate()
                if e_leave_type.allocate_on_day:
                    text = frappe._(
                        "Allocated {0} leave(s) via scheduler on {1} based on {2}"
                    ).format(
                        frappe.bold(round_earned_leaves(adjusted_leaves,e_leave_type.rounding)), frappe.bold(formatdate(today_date)), frappe.bold("Leave policy based on attendance")
                    )

                allocation.add_comment(comment_type="Info", text=text)
                allocation.save("Submit")
                create_leave_ledger_entry(allocation,adjusted_leaves,e_leave_type)

def create_leave_ledger_entry(allocation,adjusted_leaves,e_leave_type):
    ledger_entry = frappe.new_doc("Leave Ledger Entry")
    ledger_entry.employee = allocation.employee
    ledger_entry.employee_name = allocation.employee_name
    ledger_entry.leave_type = allocation.leave_type
    ledger_entry.transaction_type = "Leave Allocation"
    ledger_entry.transaction_name = allocation.name
    ledger_entry.company = allocation.company
    ledger_entry.leaves = round_earned_leaves(adjusted_leaves,e_leave_type.rounding)
    ledger_entry.from_date = allocation.from_date
    ledger_entry.to_date = allocation.to_date
    ledger_entry.is_expired = allocation.expired
    ledger_entry.custom_leaves_updated_based_on_attendance = 1
    ledger_entry.save(ignore_permissions=True)
    ledger_entry.submit()

def get_leave_allocations(date, leave_type):
	return frappe.db.sql(
		"""select name, employee, from_date, to_date, leave_policy_assignment, leave_policy, leave_type, new_leaves_allocated, total_leaves_allocated
		from `tabLeave Allocation`
		where
			%s between from_date and to_date and docstatus=1
			and leave_type=%s""",
		(date, leave_type),
		as_dict=1,
	)

def get_earned_leaves():
	return frappe.get_all(
		"Leave Type",
		fields=[
			"name",
			"max_leaves_allowed",
			"earned_leave_frequency",
			"rounding",
			"allocate_on_day",
            "custom_minimum_required_days",
            "custom_attendance_count_based_on"
		],
		filters={"is_earned_leave": 1,"custom_enable_leave_allocation_based_on_attendance":1},
	)


def check_effective_date(from_date, today, frequency, allocate_on_day):
    from dateutil import relativedelta

    from_date = get_datetime(from_date)
    today = frappe.flags.current_date or get_datetime(today)
    rd = relativedelta.relativedelta(today, from_date)

    expected_date = {
        "First Day": get_first_day(today),
        "Last Day": get_last_day(today),
        "Date of Joining": from_date,
    }[allocate_on_day]

    if allocate_on_day == "First Day":
        expected_date += relativedelta.relativedelta(days=1)
    elif allocate_on_day == "Last Day":
        expected_date += relativedelta.relativedelta(days=1)

    if allocate_on_day == "Date of Joining":
        expected_date += relativedelta.relativedelta(days=1)
    
    if expected_date.day == today.day:
        if frequency == "Monthly":
            return True
        elif frequency == "Quarterly" and rd.months % 3:
            return True
        elif frequency == "Half-Yearly" and rd.months % 6:
            return True
        elif frequency == "Yearly" and rd.months % 12:
            return True

    return False
    
# -----------------------------------------------------------------------------------------------------------------------------------------------------------------

def custom_attendance_request(self,method):
    if self.half_day and self.from_date == self.to_date:
        is_half_day_attendance_exist = frappe.db.sql("""SELECT name
                                                        FROM `tabAttendance`
                                                        WHERE employee = '{0}' 
                                                        AND attendance_date = '{1}' 
                                                        AND status = 'Half Day' 
                                                        AND leave_type is null 
                                                        and attendance_request is null 
                                                    """.format(self.employee,self.half_day_date),as_dict=1)
        if is_half_day_attendance_exist:
            att = frappe.get_cached_doc("Attendance",is_half_day_attendance_exist[0]["name"])
            att.db_set("attendance_request",self.name)
            att.db_set("status","Present")
            if att.docstatus == 0:
                att.save()
            else:
                att.save("Submit")
            
            frappe.msgprint(
                title="Existing attenance found",
                indicator="orange",
                alert=True,
                realtime=True,
                msg="Attendance status changed into Present for existing attendance '{0}' ".format(get_link_to_form("Attendance",att.name))
            )

import frappe
from frappe.utils import getdate
from datetime import timedelta

@frappe.whitelist()
def run_deputation_attendance_request(FROM_DATE, TO_DATE, MANUAL_RUN = None):
    enqueue('hr_india_compliance.hr_india_compliance_utils.deputation_attendance_request',
            MANUAL_RUN = MANUAL_RUN,
            FROM_DATE = FROM_DATE,
            TO_DATE = TO_DATE,
            timeout = 30000,
            queue="long")
    
def deputation_attendance_request(FROM_DATE, TO_DATE, MANUAL_RUN = None):
    if FROM_DATE and TO_DATE:
        from_date = getdate(FROM_DATE)
        to_date = getdate(TO_DATE)
        

        deputation_requests = frappe.db.sql("""
            SELECT * 
            FROM `tabDeputation Request` 
            WHERE docstatus = 1 
              AND from_date <= %s 
              AND to_date >= %s
        """, (from_date, to_date), as_dict=1)

        current_date = from_date
        dates = []
        while current_date <= to_date:
            dates.append(current_date)
            current_date += timedelta(days=1)
        
        for request in deputation_requests:
            employee_id = request.get("employee")
            employee_status, relieving_date = frappe.get_value(
                "Employee", employee_id, ["status", "relieving_date"])
            
            if employee_status == "Active":
                for date in dates:
                    if not relieving_date or getdate(relieving_date) >= date:
                        holiday_dates = get_holiday_dates_for_employee(employee_id, date, date)
                        if date not in holiday_dates:
                            attendance_request = frappe.db.get_value(
                                "Attendance Request", 
                                {"from_date": ["<=", date], "to_date": [">=", date], "employee": employee_id, "docstatus": ["!=", 2]}, 
                                ["name"]
                            )
                            if not attendance_request:
                                print("employee: ",employee_id)
                                print("date :",date)
                                doc = frappe.new_doc("Attendance Request")
                                doc.employee = employee_id
                                doc.company = request.get("company")
                                doc.from_date = date
                                doc.to_date = date
                                doc.reason = "On Duty"
                                doc.deputation_request = request.get("name")
                                doc.save(ignore_permissions=True)

@frappe.whitelist()
def run_employee_paid_off_leave_application_method(FROM_DATE, TO_DATE, MANUAL_RUN = None):
    enqueue('hr_india_compliance.hr_india_compliance_utils.employee_paid_off_leave_application',
            FROM_DATE = FROM_DATE,
            TO_DATE = TO_DATE,
            MANUAL_RUN = MANUAL_RUN,
            timeout=30000,
            queue='long')
    

def employee_paid_off_leave_application(FROM_DATE, TO_DATE, MANUAL_RUN = None):
    if FROM_DATE and TO_DATE:
        from_date = getdate(FROM_DATE)
        to_date = getdate(TO_DATE)
        pos = frappe.get_cached_doc("Paid Off Settings")
        if pos.is_paid_off_leave_application_required:
            data= frappe.db.sql("""SELECT DISTINCT(ed.employee), pod.from_date, pod.to_date, pod.paid_off_days, ep.name
                        FROM `tabEmployee Paid Off Details` ed
                        LEFT JOIN `tabEmployee Paid Off` ep on ed.parent = ep.name
                        LEFT JOIN `tabPaid Off Details` pod on ed.employee = pod.parent
                        LEFT JOIN `tabEmployee` emp on ed.employee = emp.employee
                        WHERE emp.custom_paid_off_status = "Paid Off"
                        AND emp.status = "Left"
                        AND ep.docstatus = 1
                        GROUP BY ed.employee
                    """,as_dict=1)
            
            current_date = from_date
            dates = []
            while current_date <= to_date:
                dates.append(current_date)
                current_date += timedelta(days=1)

            for d in data:
                for date in dates:
                    ho = get_holiday_dates_for_employee(d.get("employee"), date, date)
                    if date not in ho:
                        at= frappe.db.get_value("Attendance",{"attendance_date":getdate(date),"employee":d.employee,"docstatus":["!=",2]},["name"])
                        if not at:
                            dc=frappe.db.get_value("Leave Application",{"from_date":["<=",date],"to_date":[">=",date],"employee":d.get("employee"),"docstatus":["!=",2]},["name"])
                            if not dc:
                                doc = frappe.new_doc("Leave Application")
                                doc.employee = d.employee
                                doc.from_date = getdate(date)
                                doc.to_date = getdate(date)
                                doc.posting_date = getdate(date)
                                doc.leave_type = pos.paid_off_leave_type
                                doc.description = "Marked Paid Off Leave"
                                doc.status = "Approved"
                                doc.custom_employee_paid_off=d.name
                                doc.save(ignore_permissions=True)
                                doc.submit()