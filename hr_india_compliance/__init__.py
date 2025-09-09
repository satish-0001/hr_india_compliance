__version__ = "15.0.1"

import frappe
from frappe.utils.data import add_months, get_first_day, get_last_day, getdate
from hrms.hr.doctype.staffing_plan.staffing_plan import StaffingPlan
from hrms.hr.doctype.compensatory_leave_request.compensatory_leave_request import CompensatoryLeaveRequest
from hrms.utils import get_date_range


@frappe.whitelist()
def set_job_requisitions(self, job_reqs):
    if job_reqs:
        requisitions = frappe.db.get_list(
            "Job Requisition",
            filters={"name": ["in", job_reqs]},
            fields=["designation", "no_of_positions", "expected_compensation","custom_employment_type"],
        )

        self.staffing_details = []
        for req in requisitions:
            print("hello",req)
            self.append(
                "staffing_details",
                {
                    "designation": req.designation,
                    "vacancies": req.no_of_positions,
                    "estimated_cost_per_position": req.expected_compensation,
                    "custom_employment_type":req.custom_employment_type
                },
            )

    return self
setattr(StaffingPlan,"set_job_requisitions",set_job_requisitions)


def validate_attendance(self):
    pass
def validate_holidays(self):
   pass

setattr(CompensatoryLeaveRequest,"validate_attendance",validate_attendance)
setattr(CompensatoryLeaveRequest,"validate_holidays",validate_holidays)



"""auto repeat modification for Leave Allocation"""
from frappe.automation.doctype.auto_repeat.auto_repeat import AutoRepeat

def custom_make_new_document(self):
    reference_doc = frappe.get_doc(self.reference_doctype, self.reference_document)
    new_doc = frappe.copy_doc(reference_doc, ignore_no_copy=False)
    if self.get("reference_doctype") == "Leave Allocation":
        today = frappe.flags.current_date or getdate()
        month_start_date = get_first_day(add_months(today,-1))
        month_end_date = get_last_day(add_months(today,-1))
        new_doc.set("from_date",month_start_date)
        new_doc.set("to_date",month_end_date)
    
        
    self.update_doc(new_doc, reference_doc)
    new_doc.insert(ignore_permissions=True)

    if self.submit_on_creation:
        new_doc.submit()

    return new_doc

setattr(AutoRepeat,"make_new_document",custom_make_new_document)

from erpnext.setup.doctype.employee.employee import get_holiday_list_for_employee
import frappe
from hrms.payroll.doctype.salary_slip.salary_slip import HOLIDAYS_BETWEEN_DATES, SalarySlip
from hrms.utils.holiday_list import get_holiday_dates_between

def custom_get_holidays_for_employee(self, start_date, end_date):
    holiday_list = get_holiday_list_for_employee(self.employee)
    key = f"{holiday_list}:{start_date}:{end_date}"
    holiday_dates = frappe.cache().hget(HOLIDAYS_BETWEEN_DATES, key)

    if frappe.db.get_single_value("Payroll Settings", "custom_consider_holidays_from_shift_assignment"):
        if not holiday_dates:
            holiday_dates = get_holiday_dates_between(holiday_list, start_date, end_date)
            frappe.cache().hset(HOLIDAYS_BETWEEN_DATES, key, holiday_dates)

        new_holidays_data = get_holidays_from_shift_assignment(self, start_date, end_date,existing_holiday_list=holiday_dates)
        
        if new_holidays_data:
            return new_holidays_data
        else:
            return holiday_dates
    else:
        if not holiday_dates:
            holiday_dates = get_holiday_dates_between(holiday_list, start_date, end_date)
            frappe.cache().hset(HOLIDAYS_BETWEEN_DATES, key, holiday_dates)

        return holiday_dates
    


def get_holidays_from_shift_assignment(self, start_date, end_date, existing_holiday_list=None):
    if existing_holiday_list is None:
        existing_holiday_list = []

    shift_type_holiday = frappe.get_all("Shift Assignment", {
        "employee": self.employee,
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

setattr(SalarySlip,"get_holidays_for_employee",custom_get_holidays_for_employee)


from hrms.hr.doctype.shift_type.shift_type import ShiftType

def custom_get_dates_for_attendance(self, employee: str) -> list[str]:
    start_date, end_date = self.get_start_and_end_dates(employee)

    # no shift assignment found, no need to process absent attendance records
    if start_date is None:
        return []

    date_range = get_date_range(start_date, end_date)

    # skip marking absent on holidays
    holiday_list = self.get_holiday_list(employee)
    holiday_dates = get_holiday_dates_between(holiday_list, start_date, end_date)

    if frappe.db.get_single_value("Payroll Settings", "custom_consider_holidays_from_shift_assignment"):
        shift_assignment_holidays = get_holidays_from_shift_assignment_for_attendance(
            employee=employee,
            start_date=start_date,
            end_date=end_date,
            existing_holiday_list=holiday_dates
        )

        if shift_assignment_holidays:

            # skip dates with attendance
            marked_attendance_dates = self.get_marked_attendance_dates_between(
                employee, start_date, end_date
            )

            return sorted(set(date_range) - set(shift_assignment_holidays) - set(marked_attendance_dates))
        
        else:
            # skip dates with attendance
            marked_attendance_dates = self.get_marked_attendance_dates_between(
                employee, start_date, end_date
            )

            return sorted(set(date_range) - set(holiday_dates) - set(marked_attendance_dates))
    else:
        # skip dates with attendance
        marked_attendance_dates = self.get_marked_attendance_dates_between(
            employee, start_date, end_date
        )

        return sorted(set(date_range) - set(holiday_dates) - set(marked_attendance_dates))
    
setattr(ShiftType,"get_dates_for_attendance",custom_get_dates_for_attendance)

def get_holidays_from_shift_assignment_for_attendance(employee, start_date, end_date, existing_holiday_list=None):
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