# Copyright (c) 2023, Dexciss Technology Pvt Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import datetime, timedelta
from frappe.utils.data import getdate

class ShiftRotation(Document):

    @frappe.whitelist()
    def get_data(self):
        employees = frappe.db.sql("""
                                    SELECT e.*
                                    FROM `tabEmployee` e
                                    LEFT JOIN `tabShift Type` s ON e.default_shift = s.name
                                    WHERE e.status = 'Active'
                                    AND e.branch = '{0}'
                                    AND e.default_shift is not NULL
                                    AND s.custom_is_shift_rotation = 1
                                """.format(self.plant), as_dict=True)

        self.shift_rotation_details = []

        for emp in employees:
            print("emp------->", emp.name)
            self.append("shift_rotation_details", {
                "employee": emp.name,
                "employee_name": emp.employee_name,
                "default_shift": emp.default_shift
            })

    def before_submit(self):
        # Convert from_date and to_date to datetime objects
        from_date = datetime.strptime(self.from_date, "%Y-%m-%d")
        to_date = datetime.strptime(self.to_date, "%Y-%m-%d")

        branch_doc = frappe.get_doc("Branch", self.plant)
        custom_shift_rotation_day = branch_doc.custom_shift_rotation_day

        day_name_to_int = {
            "Sunday": 0,
            "Monday": 1,
            "Tuesday": 2,
            "Wednesday": 3,
            "Thursday": 4,
            "Friday": 5,
            "Saturday": 6
        }
        day_name = from_date.strftime("%A")
        # Calculate the next valid start date based on the selected day
        days_to_next_start_day = (day_name_to_int[custom_shift_rotation_day] - from_date.weekday() + 6) % 7
        if day_name != custom_shift_rotation_day:
            next_start_date = from_date + timedelta(days=days_to_next_start_day)
        if day_name == custom_shift_rotation_day:
            next_start_date = from_date +timedelta(days=7)

        #for creating shift assignment till Next Start Day
        while from_date < next_start_date:
            for emp in self.shift_rotation_details:
                __emp = frappe.get_doc("Employee", {"employee": emp.employee})
                doc = frappe.new_doc("Shift Assignment")
                doc.employee = emp.employee
                doc.shift_type = emp.default_shift
                doc.company = __emp.company
                doc.start_date = getdate(from_date)
                doc.end_date = getdate(next_start_date - timedelta(days=1))
                doc.custom_shift_rotation = self.name = self.name
                doc.save(ignore_permissions=True)
                doc.submit()
            from_date += timedelta(days=7)

        rotational_dates = {}
        rotation = []
        slice_number = 1
        current_date = next_start_date

        while current_date <= to_date:
            end_date = min(current_date + timedelta(days=6), to_date)

            rotational_dates = {
                "start_date": getdate(current_date),
                "end_date": getdate(end_date)
            }

            rotation.append(rotational_dates)
            current_date = end_date + timedelta(days=1)
            slice_number += 1

        for emp in self.shift_rotation_details:
            new_shift = emp.default_shift

            _emp = frappe.get_doc("Employee", {"employee": emp.employee})
            _branch = frappe.get_doc("Branch", {"branch": _emp.branch})

            for p in rotation:
                for child in _branch.custom_holiday_wise_shift_rotation:
                    if new_shift == child.column_a:
                        new_shift = child.column_b
                    elif new_shift == child.column_b:
                        new_shift = child.column_c
                    elif new_shift == child.column_c:
                        new_shift = child.column_a
                doc = frappe.new_doc("Shift Assignment")
                doc.employee = emp.employee
                doc.shift_type = new_shift
                doc.company = _emp.company
                doc.start_date = p.get("start_date")
                doc.end_date = p.get("end_date")
                doc.custom_shift_rotation = self.name
                doc.save(ignore_permissions=True)
                doc.submit()
