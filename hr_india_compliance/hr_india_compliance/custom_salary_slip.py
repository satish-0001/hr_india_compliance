import frappe
def update_pf_checkbox(self,method):
    # pass
    for d in self.deductions:
        if d.salary_component == "Employee Provident Fund":
            d.custom_pf_12_per = 1