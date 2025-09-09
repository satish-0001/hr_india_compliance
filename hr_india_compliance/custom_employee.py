import frappe
from frappe.utils import get_first_day , get_last_day ,date_diff 
from datetime import datetime

from hrms.hr.utils import round_earned_leaves

@frappe.whitelist()

def create_leave_allocation(self, method):

    

    leave_and_attendence_data=frappe.get_single("Leave And Attendance Settings")

    if not leave_and_attendence_data.default_short_leave_type or not leave_and_attendence_data.number_of_leave_allocation:
        return 
   
   
    leave_allocation = frappe.new_doc("Leave Allocation")  

    leave_allocation.employee = self.name
    leave_allocation.employee_name = self.employee_name
    leave_allocation.leave_type =leave_and_attendence_data.default_short_leave_type    
    leave_allocation.from_date=get_first_day(self.date_of_joining)
    leave_allocation.to_date=get_last_day(self.date_of_joining)    
    difference = date_diff(get_last_day(self.date_of_joining),self.date_of_joining)
    allocated_leave = round_earned_leaves(
        earned_leaves=leave_and_attendence_data.number_of_leave_allocation,
        rounding=frappe.db.get_value("Leave Type",leave_and_attendence_data.default_short_leave_type,'rounding')
    )
    if difference <= 15 and difference >=10:
        leave_allocation.new_leaves_allocated = allocated_leave/2
    elif difference >15:
        leave_allocation.new_leaves_allocated= allocated_leave
    leave_allocation.save()
    leave_allocation.submit()

def custom_before_save(self,method):
    status = self.status
    if status != 'Active':
        print("iiiiiiiiii")
        leave_allocations = frappe.get_list(
            "Leave Allocation",
            filters={
                "employee": self.name,
                "leave_type": "Short Leave",
                "auto_repeat": ["is", "set"]
            },
            limit=1
        )
        if leave_allocations:
            leave_allocation = frappe.get_doc("Leave Allocation", leave_allocations[0].name)
            auto = frappe.get_doc("Auto Repeat", leave_allocation.auto_repeat)
            auto.disabled = 1
            auto.save()
    

    
    
         

