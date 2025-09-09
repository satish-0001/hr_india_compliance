__version__ = '0.0.1'

import frappe
from frappe.utils.data import date_diff, format_date, getdate
from hrms.hr.doctype.staffing_plan.staffing_plan import StaffingPlan
from hrms.hr.doctype.compensatory_leave_request.compensatory_leave_request import CompensatoryLeaveRequest
from hrms.hr.utils import get_holiday_dates_for_employee


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
