# Copyright (c) 2023, Dexciss Technology Pvt Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class StatisticalPaymentRequest(Document):
	@frappe.whitelist()
	def get_data(self,method):
		if not self.from_date:
			frappe.throw("Please select From Date")
		if not self.to_date:
			frappe.throw("Please select To date")
		if not self.plant:
			frappe.throw("please select Plant")
		if not self.salary_component:
			frappe.throw("please select Salary Component")
		# data = frappe.db.sql("""
		# 						SELECT employee,employee_name,balance_amount,is_cancelled,plant,component,voucher_no
		# 			   			FROM `tabStatistical Component Log`
		# 			   			WHERE is_cancelled !=1 
		# 			   			AND plant = '{0}'
		# 			   			AND component = '{1}'
		# 			   			AND from_date >= '{2}'
		# 			   			And to_date <= '{3}'
		# 			   			ORDER BY creation DESC
		# 			   			LIMIT 1
		# 					""".format(self.plant,self.salary_component,self.from_date,self.to_date),as_dict=1)
		data = frappe.db.sql(
    							"""
    								SELECT 
        								employee, employee_name, balance_amount, is_cancelled, plant, component, voucher_no
    								FROM 
        								`tabStatistical Component Log`
    								WHERE 
        								is_cancelled != 1 
        								AND plant = %s
        								AND component = %s
        								AND from_date >= %s
        								AND to_date <= %s
    								ORDER BY 
        							creation DESC
    							""",
    							(self.plant, self.salary_component, self.from_date, self.to_date),
    							as_dict=True)
		if data:
			self.statistical_payment_details=[]
			for d in data:
				if d.get("balance_amount"):
					salary_component = frappe.get_doc("Salary Component",{"name":self.salary_component})
					self.append("statistical_payment_details",{
						"employee":d.get("employee"),
						"employee_name":d.get("employee_name"),
						"balance_amount":d.get("balance_amount"),
						"statistical_payment_component":salary_component.custom_statistical_payment_component,
						"company":self.company,
						"payroll_date":self.payroll_date,
						"salary_slip":d.get("voucher_no")
					})
			
	def on_submit(self):
		for data in self.statistical_payment_details:
			if data.get("balance_amount"):
				doc = frappe.new_doc("Additional Salary")
				doc.employee = data.get("employee")
				doc.company = data.get("company")
				doc.salary_component = data.get("statistical_payment_component")
				doc.payroll_date = data.get("payroll_date")
				doc.amount = data.get("balance_amount")
				doc.ref_doctype = "Statistical Payment Request"
				doc.ref_docname = self.name
				doc.save(ignore_permissions=True)
				doc.submit()

				
				s_slip = frappe.get_doc("Salary Slip",{"name":data.get("salary_slip")})
				s_s_assignment = frappe.get_value("Salary Structure Assignment",{"salary_structure":s_slip.salary_structure,"employee":s_slip.employee},order_by ="creation ASC")
				if s_s_assignment:
					ssa = frappe.get_doc("Salary Structure Assignment",s_s_assignment)
					for pc in ssa.payroll_cost_centers:
						payroll_cost_center = pc.cost_center
				
				pp = frappe.get_doc("Payroll Period",{"company":self.company})
				new_doc = frappe.new_doc("Statistical Component Log")
				new_doc.employee = data.get("employee")
				new_doc.employee_name = data.get("employee_name")
				new_doc.plant = self.plant
				new_doc.company = data.get("company")
				new_doc.from_date = self.from_date
				new_doc.to_date = self.to_date
				new_doc.component = self.salary_component
				new_doc.voucher_type = "Statistical Payment Request"
				new_doc.voucher_no = self.name
				new_doc.posting_date = self.payroll_date
				new_doc.payroll_period = pp.name
				new_doc.payroll_cost_center = payroll_cost_center
				new_doc.paid_amount = data.get("balance_amount")
				# new_doc.is_paid = 1
				new_doc.save(ignore_permissions=True)

				logs = frappe.get_all("Statistical Component Log",
					filters={
						"employee": data.get("employee"),
						"component": self.salary_component,
						"voucher_type": "Salary Slip"
					},
					fields=[
						"name", "paid_amount", "is_paid", "voucher_type", "voucher_no", "component"
					])
				if logs:
					for log in logs:
						frappe.db.set_value("Statistical Component Log", log.name, "is_paid", 1)

	def on_cancel(self):
		for data in self.statistical_payment_details:
			if data.get("balance_amount"):
				_as = frappe.get_all("Additional Salary",
							{
								"employee":data.get("employee"),
								"salary_component":data.get("statistical_payment_component"),
								"custom_statistical_payment_request":self.name,
								"company":data.get("company"),
								"docstatus":["!=",0]
							},
							["name","docstatus"])
				if _as:
					for d in _as:
						frappe.db.set_value("Additional Salary",d.name,"docstatus",2)

			ad2 = frappe.get_all("Statistical Component Log",
					  {"employee":data.get("employee"),"voucher_type":"Salary Slip","component":self.salary_component,"is_paid":["!=",0]},
					  ["name","employee","salary_slip","component","is_cancelled","is_paid","voucher_type"])
			if ad2:
				for j in ad2:
					frappe.db.set_value("Statistical Component Log",j.name,"is_paid",0)
					# frappe.db.set_value("Statistical Component Log",d.name,"is_cancelled",1)


			ad = frappe.get_all("Statistical Component Log",
						{"employee":data.get("employee"),"voucher_no":self.name,"component":self.salary_component,"is_paid":["!=",1]},
						["name","employee","salary_slip","component","is_cancelled","is_paid","voucher_no"])
			if ad:
				for d in ad:
					frappe.db.set_value("Statistical Component Log",d.name,"is_cancelled",1)
					frappe.db.set_value("Statistical Component Log",d.name,"paid_amount",0)
					# frappe.db.set_value("Statistical Component Log",d.name,"is_paid",0)