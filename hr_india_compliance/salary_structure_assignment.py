import json
from datetime import datetime
from erpnext import get_company_currency
import frappe
from hrms.payroll.doctype.salary_structure.salary_structure import make_salary_slip
from frappe.utils import (
	formatdate,
	rounded,
)


@frappe.whitelist()
def update_salary_breakup(doc,method):
    if isinstance(doc.from_date, str):
        demo_date = datetime.strptime(doc.from_date, "%Y-%m-%d").date()
        print("Converted Date:", demo_date)
        doc.from_date = demo_date
    try:
        print_format = "Salary Slip based on Timesheet" if frappe.db.get_value("Salary Structure",doc.salary_structure,'salary_slip_based_on_timesheet') else "Salary Slip Standard"
        from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip
        def custom_set_salary_structure_assignment(self):
            doc_as_dict = doc.as_dict() if hasattr(doc, "as_dict") else dict(doc)
            self._salary_structure_assignment = doc_as_dict

            if not self._salary_structure_assignment:
                frappe.throw(
                    frappe._(
                        "Please assign a Salary Structure for Employee {0} applicable from or before {1} first"
                    ).format(
                        frappe.bold(self.employee_name),
                        frappe.bold(formatdate(self.actual_start_date)),
                    )
                )
        setattr(SalarySlip,"set_salary_structure_assignment",custom_set_salary_structure_assignment)
        
        salary_slip = make_salary_slip(
            source_name = doc.salary_structure,
            employee=doc.employee,
            posting_date=doc.from_date,
            for_preview=1,
            print_format=print_format
        )

        doc.custom_salary_detail=[]
        doc.custom_earning_ctc=[]
        gross=[]
        ctc_monthly = []
        ctc_yearly = []

        salary_slip.data, salary_slip.default_data = salary_slip.get_data_for_eval()
        ss = frappe.get_cached_doc("Salary Structure", salary_slip.salary_structure)

        for struct_row in ss.get("earnings"):
            amount = salary_slip.eval_condition_and_formula(struct_row, salary_slip.data)
            if frappe.db.get_value(
                "Salary Component", struct_row.salary_component, "round_to_the_nearest_integer", cache=True
            ):
                amount = rounded(amount or 0)
            
            amount = amount or 0
            if amount > 0:
                sc = frappe.get_cached_doc("Salary Component", struct_row.salary_component)
                if sc.custom_gross:
                    doc.append("custom_salary_detail",{
                        "salary_component":sc.salary_component,
                        "amount":amount
                    })
                    gross.append(amount)
                
                if sc.custom_ctc:
                    doc.append("custom_earning_ctc",{
                        "salary_component":sc.salary_component,
                        "amount_monthly":amount,
                        "amount_yearly":amount * 12
                    })

                    ctc_monthly.append(amount)
                    ctc_yearly.append(amount*12)

        doc.custom_gross_salary = sum(gross)
        doc.custom_total_ctc_monthly = sum(ctc_monthly)
        doc.custom_total_ctc_yearly = sum(ctc_yearly)

        from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip
        def custom_set_salary_structure_assignment(self):
            self._salary_structure_assignment = frappe.db.get_value(
                "Salary Structure Assignment",
                {
                    "employee": self.employee,
                    "salary_structure": self.salary_structure,
                    "from_date": ("<=", self.actual_start_date),
                    "docstatus": 1,
                },
                "*",
                order_by="from_date desc",
                as_dict=True,
            )

            if not self._salary_structure_assignment:
                frappe.throw(
                    frappe._(
                        "Please assign a Salary Structure for Employee {0} applicable from or before {1} first"
                    ).format(
                        frappe.bold(self.employee_name),
                        frappe.bold(formatdate(self.actual_start_date)),
                    )
                )
        setattr(SalarySlip,"set_salary_structure_assignment",custom_set_salary_structure_assignment)
    except:
        frappe.log_error(frappe.get_traceback())


@frappe.whitelist()
def get_salary_breakup(doc):

    if isinstance(doc, str):
        doc = frappe._dict(json.loads(doc))
    
    from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip
    def custom_set_salary_structure_assignment(self):
        self._salary_structure_assignment = frappe.get_doc("Salary Structure Assignment",doc.name).as_dict()

        if not self._salary_structure_assignment:
            frappe.throw(
                frappe._(
                    "Please assign a Salary Structure for Employee {0} applicable from or before {1} first"
                ).format(
                    frappe.bold(self.employee_name),
                    frappe.bold(formatdate(self.actual_start_date)),
                )
            )
    setattr(SalarySlip,"set_salary_structure_assignment",custom_set_salary_structure_assignment)

    doc = make_salary_slip(
        source_name = doc.salary_structure,
        employee=doc.employee,
        posting_date=doc.from_date,
        for_preview=1,
        print_format = "Salary Slip based on Timesheet" if frappe.db.get_value("Salary Structure",doc.salary_structure,'salary_slip_based_on_timesheet') else "Salary Slip Standard",
    )

    data = add_structure_components(doc,salary_slip=doc,component_type="earnings")

    from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip
    def custom_set_salary_structure_assignment(self):
        self._salary_structure_assignment = frappe.db.get_value(
			"Salary Structure Assignment",
			{
				"employee": self.employee,
				"salary_structure": self.salary_structure,
				"from_date": ("<=", self.actual_start_date),
				"docstatus": 1,
			},
			"*",
			order_by="from_date desc",
			as_dict=True,
		)

        if not self._salary_structure_assignment:
            frappe.throw(
                frappe._(
                    "Please assign a Salary Structure for Employee {0} applicable from or before {1} first"
                ).format(
                    frappe.bold(self.employee_name),
                    frappe.bold(formatdate(self.actual_start_date)),
                )
            )
    setattr(SalarySlip,"set_salary_structure_assignment",custom_set_salary_structure_assignment)

   
    return data

def add_structure_components(doc,salary_slip, component_type):
    doc.custom_salary_detail=[]
    doc.custom_earning_ctc=[]
    salary_detail = []
    earning_ctc = []
    gross=[]
    ctc_monthly = []
    ctc_yearly = []

    salary_slip.data, salary_slip.default_data = salary_slip.get_data_for_eval()
    ss = frappe.get_cached_doc("Salary Structure", salary_slip.salary_structure)
    for struct_row in ss.get(component_type):
        amount = salary_slip.eval_condition_and_formula(struct_row, salary_slip.data)
        
        amount = amount or 0

        if frappe.db.get_value(
			"Salary Component", struct_row.salary_component, "round_to_the_nearest_integer", cache=True
		):
            amount = rounded(amount or 0)
        if amount > 0:
            sc = frappe.get_cached_doc("Salary Component", struct_row.salary_component)
            if sc.custom_gross:
                salary_detail.append({
                    "salary_component":sc.salary_component,
                    "amount":amount
                })
                gross.append(amount)
            
            if sc.custom_ctc:
                earning_ctc.append({
                    "salary_component":sc.salary_component,
                    "amount_monthly":amount,
                    "amount_yearly":amount * 12
                })

                ctc_monthly.append(amount)
                ctc_yearly.append(amount*12)
            
    return salary_detail,earning_ctc,sum(gross),sum(ctc_monthly),sum(ctc_yearly)
            





        
