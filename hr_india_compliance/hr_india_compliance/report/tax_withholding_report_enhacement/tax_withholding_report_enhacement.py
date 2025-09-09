# Copyright (c) 2025, Dexciss Technology Pvt Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip as sal
from hrms.payroll.doctype.payroll_period.payroll_period import (
	get_payroll_period,
	get_period_factor,
)
from frappe.utils import flt

def execute(filters=None):
	columns, data = [], []
	data = get_data(filters)
	columns = get_column()
	return columns, data


def get_data(filters):
	data = []
	conditions = []
	date_cond = []

	if filters.get("employee"):
		employee = filters.get("employee")
		conditions.append(f"employee = '{employee}'")
	
	if filters.get("company"):
		company = filters.get("company")
		conditions.append(f"company = '{company}'")

	if filters.get("branch"):
		branch = filters.get("branch")
		conditions.append(f"branch = '{branch}'")

	from_Date = filters.get("from_date")
	to_date = filters.get("to_date")
	
	if filters.get("from_date") and filters.get("to_date"):
		date_cond.append(f"posting_date between '{from_Date}' and '{to_date}'")
	
	
	date_cond_str = " AND ".join(date_cond) if date_cond else "1=1"
	conditions_str = " AND ".join(conditions) if conditions else "1=1"

	employee_data = frappe.db.sql(f"""
		SELECT name, employee_name, pan_number, custom_tax_withholding_category
		FROM `tabEmployee`
		WHERE status = 'Active'
		AND date_of_joining < '{to_date}'
		AND custom_tax_withholding_category is not null
		AND {conditions_str}
	""", as_dict=True)

	for emp in employee_data:
		employee_name = emp.get("employee_name")
		pan_number = emp.get("pan_number")
		section_code = emp.get("custom_tax_withholding_category")

		tds_rate = None
		# entity_type = None

		if section_code:
			twc_doc = frappe.get_doc("Tax Withholding Category", section_code)
			# entity_type = twc_doc.entity_type
			for rate in twc_doc.rates:
				tds_rate = rate.tax_withholding_rate

	
		salary_slip_list = frappe.db.sql(f"""
			SELECT name,posting_date,gross_pay,net_pay
			from `tabSalary Slip` 
			WHERE employee = '{emp.get("name")}'
			AND docstatus = 1
			AND {date_cond_str}
		""",as_dict = True)
		tax_amount = 0
		
		for sal_data in salary_slip_list:
			reference_no = sal_data.get("name")
			date_of_transaction = sal_data.get("posting_date")
			gross_salary = sal_data.get("gross_pay")
			net_salary = sal_data.get("net_pay")

			slip = frappe.get_doc("Salary Slip", {"employee": emp.get("name"),"name":reference_no})
			
			taxable_salary = calculate_net_pay(slip)
			if taxable_salary:
				taxable_salary = taxable_salary
			
			


			taxable_earnings = 0
			for e in slip.earnings:
				taxable_earnings += e.amount

			for ded in slip.deductions:
				if ded.salary_component == "Income Tax" and ded.amount > 0:
					taxable_salary = add_tax_components(slip)
					if tds_rate:
						tax_amount = (gross_salary * tds_rate)/ 100

					parent_row = {
					"section_code": section_code,
					"pan": pan_number,
					"employee_name": employee_name,
					"entity_type": "Individual",
					"tds_rate": tds_rate,
					"gross_salary": gross_salary,
					"net_salary": net_salary,
					"base_total": taxable_salary, 
					"tds_amount": tax_amount,
					"transaction_type": "Salary Slip", 
					"reference_no": reference_no,
					"date_of_transaction": date_of_transaction,
					"indent": 1
				}

					data.append(parent_row)

	return data


	


def get_column():
	return [
		{
			"label": _("Section Code"),
			"fieldtype": "Link",
			"fieldname": "section_code",
			"options": "Tax Withholding Category",
			"width": 250,
		},
		{
			"label": _("Pan"),
			"fieldtype": "Data",
			"fieldname": "pan",
			"width": 150,
		},
		{
			"label": _("Employee Name"),
			"fieldtype": "Data",
			"fieldname": "employee_name",
			"width": 150,
		},
		{
			"label": _("Entity Type"),
			"fieldtype": "Data",
			"fieldname": "entity_type",
			"width": 150,
		},
		{
			"label": _("TDS Rate %"),
			"fieldtype": "Data",
			"fieldname": "tds_rate",
			"width": 200,
		},
		{
			"label": _("Gross Salary"),
			"fieldtype": "Currency",
			"fieldname": "gross_salary",
			"width": 250,
		},
		{
			"label": _("Net Salary"),
			"fieldtype": "Currency",
			"fieldname": "net_salary",
			"width": 250,
		},
		{
			"label": _("Base Total"),
			"fieldtype": "Currency",
			"fieldname": "base_total",
			"width": 250,
		},
		{
			"label": _("TDS Amount"),
			"fieldtype": "Currency",
			"fieldname": "tds_amount",
			"width": 250,
		},
		{
			"label": _("Transaction Type"),
			"fieldtype": "Data",
			"fieldname": "transaction_type",
			"width": 250,
		},
		{
			"label": _("Reference No."),
			"fieldtype": "Link",
			"fieldname": "reference_no",
			"options":"Salary Slip",
			"width": 250,
		},
		{
			"label": _("Date of Transaction"),
			"fieldtype": "Date",
			"fieldname": "date_of_transaction",
			"width": 250,
		},
	]




def calculate_net_pay(self, skip_tax_breakup_computation: bool = False):
		def set_gross_pay_and_base_gross_pay():
			self.gross_pay = self.get_component_totals("earnings", depends_on_payment_days=1)
			self.base_gross_pay = flt(
				flt(self.gross_pay) * flt(self.exchange_rate), self.precision("base_gross_pay")
			)

		if self.salary_structure:
			calculate_component_amounts(self,"earnings")

		# get remaining numbers of sub-period (period for which one salary is processed)
		if self.payroll_period:
			self.remaining_sub_periods = get_period_factor(
				self.employee,
				self.start_date,
				self.end_date,
				self.payroll_frequency,
				self.payroll_period,
				joining_date=self.joining_date,
				relieving_date=self.relieving_date,
			)[1]

		set_gross_pay_and_base_gross_pay()

		if self.salary_structure:
			calculate_component_amounts(self,"deductions")


def calculate_component_amounts(self, component_type):
		if not getattr(self, "_salary_structure_doc", None):
			self.set_salary_structure_doc()

		self.add_structure_components(component_type)
		self.add_additional_salary_components(component_type)
		if component_type == "earnings":
			self.add_employee_benefits()
		else:
			add_tax_components(self)


def add_tax_components(self):
		# Calculate variable_based_on_taxable_salary after all components updated in salary slip
		tax_components, self.other_deduction_components = [], []
		for d in self._salary_structure_doc.get("deductions"):
			if d.variable_based_on_taxable_salary == 1 and not d.formula and not flt(d.amount):
				tax_components.append(d.salary_component)
			else:
				self.other_deduction_components.append(d.salary_component)

		if self.handle_additional_salary_tax_component():
			return

		# consider manually added tax component
		if not tax_components:
			tax_components = [
				d.salary_component for d in self.get("deductions") if d.variable_based_on_taxable_salary
			]

		if self.is_new() and not tax_components:
			tax_components = self.get_tax_components()
			frappe.msgprint(
				_(
					"Added tax components from the Salary Component master as the salary structure didn't have any tax component."
				),
				indicator="blue",
				alert=True,
			)

		if tax_components and self.payroll_period and self.salary_structure:
			self.tax_slab = self.get_income_tax_slabs()
			self.compute_taxable_earnings_for_year()

		self._component_based_variable_tax = {}
		for d in tax_components:
			self._component_based_variable_tax.setdefault(d, {})
			# tax_amount = self.calculate_variable_based_on_taxable_salary(d)
			try:
				tax_amount = self.calculate_variable_tax(d)
				if tax_amount:
					return tax_amount
			except Exception as e:
				print(e)
