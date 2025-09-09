import frappe
from frappe.utils.data import getdate

def validate_leave_application(self,method):
    emp=frappe.get_doc("Employee",self.employee)
    leave_combination = get_combinaction_data(employee=emp.employee)
    for combination in leave_combination:
        existing_past_record = get_existing_past_record(employee=self.employee,leave_type=combination.leave_type,from_date=self.from_date)
        if existing_past_record:
            for record in existing_past_record:
                if record.leave_type == combination.leave_type and self.leave_type ==combination.combination_leave_type:
                    frappe.throw(f"You are not allowed to take {self.leave_type} just after {combination.leave_type} beacause it doesn't meet the Leave Combination Criteria.")
        else:
            one_day_before = frappe.utils.add_days(self.from_date,-1)
            weekly_off_days = get_weekly_off_holidays(emp.holiday_list)
            while any(holiday.weekly_off and getdate(holiday.holiday_date) == getdate(one_day_before) for holiday in weekly_off_days):
                one_day_before = frappe.utils.add_days(one_day_before, -1)
            if one_day_before:
                non_weekly_off_day_leave_application = frappe.get_all("Leave Application",{
                    "employee":self.employee,
                    "leave_type":combination.leave_type,
                    "docstatus":["!=",2],
                    "to_date":one_day_before
                },
                ["leave_type","to_date","employee"])
                if non_weekly_off_day_leave_application:
                    for application in non_weekly_off_day_leave_application:
                        if application.leave_type == combination.leave_type and self.leave_type == combination.combination_leave_type:
                            frappe.throw(title=" Error : Leave Application Found Before Weekly Off Day",
                                        msg=f"You are not allowed to take {self.leave_type} just after {application.leave_type} beacause it doesn't meet the Leave Combination Criteria.")
        
        
        existsting_future_record = get_existing_future_record(emp.employee,combination.combination_leave_type,self.from_date)
        if existsting_future_record:
            for record in existsting_future_record:
                if record.leave_type == combination.combination_leave_type and self.leave_type ==combination.leave_type:
                    frappe.throw(f"You are not allowed to take {self.leave_type},You have taken {combination.combination_leave_type} on date '{record.to_date}' and it doesn't meet the Leave Combination Criteria.")
        else:
            ond_day_after = frappe.utils.add_days(self.to_date,1)
            weekly_off_days = get_weekly_off_holidays(emp.holiday_list)
            while any(holiday.weekly_off and getdate(holiday.holiday_date) == getdate(ond_day_after) for holiday in weekly_off_days):
                ond_day_after = frappe.utils.add_days(ond_day_after, 1)
            if ond_day_after:
                non_weekly_off_day_leave_application = frappe.get_all("Leave Application",{
                    "employee":self.employee,
                    "leave_type":combination.combination_leave_type,
                    "docstatus":["!=",2],
                    "to_date":ond_day_after
                },
                ["leave_type","to_date","employee"])
                if non_weekly_off_day_leave_application:
                    for application in non_weekly_off_day_leave_application:
                        if application.leave_type == combination.combination_leave_type and self.leave_type == combination.leave_type:
                            frappe.throw(title=" Error : Leave Application Found After Weekly Off Day",
                                        msg=f"You are not allowed to take {self.leave_type}, You have taken {application.leave_type} on date '{getdate(application.to_date)}' and it doesn't meet the Leave Combination Criteria.")

def get_existing_past_record(employee,leave_type,from_date):
    return frappe.get_all(
        "Leave Application",
        filters={
            "employee": employee,
            "leave_type": leave_type,
            "docstatus":["!=",2],
            "to_date": frappe.utils.add_days(from_date, -1),
        },
        fields = ["leave_type","employee","to_date"],
        limit=1,
    )

def get_existing_future_record(employee,leave_type,from_date):
    return frappe.db.get_all(
        "Leave Application",
        filters={
            "employee": employee,
            "leave_type": leave_type,
            "docstatus":["!=",2],
            "to_date": frappe.utils.add_days(from_date, 1),
        },
        fields = ["leave_type","employee","to_date"],
        limit=1,
    )

def get_weekly_off_holidays(holiday_list_name):
    return frappe.get_all(
        "Holiday",
        filters={
            "parent": holiday_list_name,
            "weekly_off": 1
        },
        fields=["parent", "holiday_date", "weekly_off"],
    )

def get_combinaction_data(employee):
    return frappe.db.sql("""
        SELECT p.name, e.name, e.branch,e.holiday_list, 
        lcd.parent,lcd.leave_type,lcd.combination_leave_type,lcd.disabled
        FROM `tabEmployee` as e
        LEFT JOIN `tabBranch` as p ON e.branch = p.name
        INNER JOIN `tabLeave Combination Details` as lcd ON p.name = lcd.parent
        WHERE e.employee = "{0}"
        AND lcd.disabled !=1
    """.format(employee), as_dict=1)
