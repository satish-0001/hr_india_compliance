from datetime import date
import frappe
from frappe import _
from frappe.utils.data import cint, flt, get_datetime, rounded
from hrms.payroll.doctype.payroll_period.payroll_period import get_payroll_period
from hrms.payroll.doctype.salary_slip.salary_slip import _safe_eval, throw_error_message
from hrms.payroll.utils import sanitize_expression
from frappe.utils import (
	ceil,
	floor,
	getdate,
)

def before_submit(self,method):
    get_data(self)

def get_data(self):

    whitelisted_globals = {
			"int": int,
			"float": float,
			"long": int,
			"round": round,
			"date": date,
			"getdate": getdate,
			"ceil": ceil,
			"floor": floor,
		}
    
    __data ,default_data = self.get_data_for_eval()
    emp = frappe.get_cached_doc("Employee",self.employee)
    payroll_period = get_payroll_period(
        from_date = self.start_date,
        to_date=self.end_date,
        company=self.company
    )
    ss = frappe.get_cached_doc("Salary Structure",self.salary_structure)
    for key in ("earnings", "deductions"):
        for k in ss.get(key):
            new_amount = 0
            sc = frappe.get_cached_doc("Salary Component",k.salary_component)
            amount = eval_condition_and_formula(struct_row=k,whitelisted_globals=whitelisted_globals,data=__data)
            if sc.depends_on_payment_days:
                amount = (
                    flt(amount) * flt(self.payment_days) / cint(self.total_working_days)
                    if self.total_working_days else 0
                )
            if sc.round_to_the_nearest_integer:
                amount = rounded(amount or 0)
            if sc.statistical_component and sc.custom_is_log_required and (amount>0):
                existing_logs = frappe.get_all("Statistical Component Log",filters={"employee": self.employee,"component": sc.salary_component,"is_cancelled": ["!=", 1]},fields=["name", "amount"])
                if existing_logs:
                    existing_balance_sum = sum(flt(log.amount) for log in existing_logs)
                    new_amount = amount + existing_balance_sum
            
            
            if flt(amount) > 0 and sc.custom_is_log_required:
                doc = frappe.new_doc("Statistical Component Log")
                doc.employee = self.employee
                doc.employee_name = self.employee_name
                doc.plant = self.branch
                doc.company = self.company
                doc.department = emp.department
                doc.from_date = self.start_date
                doc.to_date = self.end_date
                doc.posting_date = self.posting_date
                doc.payroll_period = payroll_period.get("name")
                doc.payroll_cost_center = emp.payroll_cost_center
                doc.component = sc.salary_component
                doc.voucher_type = "Salary Slip"
                doc.voucher_no = self.name
                doc.amount = amount
                doc.balance_amount = new_amount
                doc.save(ignore_permissions=True)

def set_statistical_component_log_as_cancelled(self, method):
    # pass
    # Get the posting date of the salary slip you are trying to cancel
    posting_date_to_cancel = self.posting_date

    # Check if there are any future statistical component logs for the same employee
    has_future_logs = frappe.db.exists(
        'Statistical Component Log',
        {
            'employee': self.employee,
            'posting_date': ('>', posting_date_to_cancel),
            'is_paid':["!=",1],
            
        }
    )
    if has_future_logs:
        frappe.throw('Cannot cancel this salary slip because future statistical component calculations exist')
    
    # Otherwise, mark the records as canceled
    logs = frappe.get_all(
        'Statistical Component Log',
        filters={'voucher_no': self.name,'is_paid':["!=",1]},
        fields=['name', 'is_cancelled']
    )
    if logs:
        for log in logs:
            frappe.db.delete("Statistical Component Log",{"name":log.name},"name")
            # frappe.db.set_value("Statistical Component Log", log.name, "is_cancelled", 1)
            # frappe.db.set_value("Statistical Component Log",log.name,"voucher_no",None)
            # frappe.db.set_value("Statistical Component Log",log.name,"voucher_type",None)

             



def eval_condition_and_formula(struct_row, whitelisted_globals, data):
    try:
        condition = sanitize_expression(struct_row.condition)
        if condition:
            if not _safe_eval(condition, whitelisted_globals, data):
                return None
        
        amount = struct_row.amount
        if struct_row.amount_based_on_formula:
            formula = sanitize_expression(struct_row.formula)
            if formula:
                amount = flt(
                    _safe_eval(formula, whitelisted_globals, data)
                )
        
        if amount:
            data[struct_row.abbr] = amount
        return amount

    except NameError as ne:
        throw_error_message(
            struct_row,
            ne,
            title=_("Name error"),
            description=_("This error can be due to missing or deleted field."),
        )
    except SyntaxError as se:
        throw_error_message(
            struct_row,
            se,
            title=_("Syntax error"),
            description=_("This error can be due to invalid syntax."),
        )
    except Exception as exc:
        throw_error_message(
            struct_row,
            exc,
            title=_("Error in formula or condition"),
            description=_("This error can be due to invalid formula or condition."),
        )
        raise