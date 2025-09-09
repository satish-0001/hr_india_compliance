# Copyright (c) 2023, Dexciss Technology Pvt Ltd and contributors
# For license information, please see license.txt

# import frappe
# def set_data(self,method):
    
#     days = ["Monday", "Tuesday" , "Wednesday","Thursday" , "Friday" , "Saturday","Sunday"]
#     for day in days:
#         if len(self.custom_holiday_wise_shift_rotation) < 7:
#             if self.custom_no_of_shift:
#                 self.append("custom_holiday_wise_shift_rotation",{
#                     "weekly_off_day":day
#                 })
        
# import frappe

# @frappe.whitelist()
# def set_data(self, method):
#     days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
#     no_of_shift = self.custom_no_of_shift
#     if self.custom_allow_shift_rotation_:
#         if no_of_shift is not 0 and isinstance(no_of_shift, int):
#             self.custom_holiday_wise_shift_rotation = []
#             for i in range(no_of_shift):
#                 for day in days:
#                     self.append("custom_holiday_wise_shift_rotation", {
#                         "weekly_off_day": day
#                     })
#         else:
#             frappe.throw("Invalid value for No Of Shift. It must be a greater than 0.")