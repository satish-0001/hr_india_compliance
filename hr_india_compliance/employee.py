

from datetime import timedelta
import frappe
from frappe.utils.data import flt, getdate

def retierment_cal(self,method):
    hr=frappe.get_doc("HR Settings")
    if self.employment_type:
        empt=frappe.get_doc("Employment Type",self.employment_type)
        if hr.retirement_age and self.date_of_birth and not empt.custom_retainer:
            # print(hr.retirement_age * 365)
            try:
                date= getdate(self.date_of_birth) + timedelta(days=int(flt(hr.retirement_age) * 365)) + timedelta(days=int(flt(hr.retirement_age) / 4))  # Account for leap years
                next_month = date.replace(day=28) + timedelta(days=4)
                # print(getdate(next_month - timedelta(days=next_month.day)))
                self.db_set("date_of_retirement",getdate(next_month - timedelta(days=next_month.day)))
                                                        
            except ValueError:
                date= getdate(self.date_of_birth) + (timedelta(days=366) if (getdate(self.date_of_birth).month == 2 and getdate(self.date_of_birth).day == 29) else timedelta(days=365))
                next_month = date.replace(day=28) + timedelta(days=4)
                self.db_set("date_of_retirement",getdate(next_month - timedelta(days=next_month.day)))