import frappe
from frappe.utils.data import cint, flt, get_datetime, rounded
from hrms.payroll.doctype.payroll_period.payroll_period import get_payroll_period
from hrms.payroll.doctype.salary_slip.salary_slip import _safe_eval, throw_error_message
from hrms.payroll.utils import sanitize_expression
from frappe.utils import (
	ceil,
	floor,
	getdate,
)
from hr_india_compliance.hr_india_compliance.doctype.Custom_statistical_component_log import get_data
def execute():
    create_statical_component()


def create_statical_component():
    data = frappe.db.sql("""SELECT name FROM `tabSalary Slip` where docstatus = 1""", as_dict=1)
    print("data:----------->",data)
    try:

        for d in data:
            if not frappe.db.exists("Statistical Component Log", {"voucher_type":'Salary Slip',"voucher_no": d["name"]}):
                salary_slip = frappe.get_doc("Salary Slip",{"name":d["name"]})
                get_data(salary_slip)
    except:
        frappe.log_error(title='Getting error on Creating Statistical Component Log', message=frappe.get_traceback())