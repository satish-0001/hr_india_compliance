import frappe
from hrms.hr.doctype.leave_application.leave_application import AttendanceAlreadyMarkedError, LeaveApplication
from frappe.utils import (
	formatdate,
	get_link_to_form,

)

class CustomLeaveApplication(LeaveApplication):
    def validate_attendance(self):
        attendance_dates = frappe.get_all(
            "Attendance",
            filters={
                "employee": self.employee,
                "attendance_date": ("between", [self.from_date, self.to_date]),
                "status": ("in", ["Present", "Work From Home"]), # original ("in", ["Present", "Half Day", "Work From Home"])
                "docstatus": 1,
            },
            fields=["name", "attendance_date"],
            order_by="attendance_date",
        )
        if attendance_dates:
            frappe.throw(
                frappe._("Attendance for employee {0} is already marked for the following dates: {1}").format(
                    self.employee,
                    (
                        "<br><ul><li>"
                        + "</li><li>".join(
                            get_link_to_form("Attendance", a.name, label=formatdate(a.attendance_date))
                            for a in attendance_dates
                        )
                        + "</li></ul>"
                    ),
                ),
                AttendanceAlreadyMarkedError,
            )