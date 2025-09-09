# Copyright (c) 2023, Dexciss Technology Pvt Ltd and contributors
# For license information, please see license.txt

import frappe
import time
from frappe.model.document import Document
from frappe.utils.data import flt, getdate
from datetime import datetime
from hr_india_compliance.hr_india_compliance_utils import get_season_details

class ShortLeaveCalculation(Document):
	@frappe.whitelist()
	def get_data(self):
		if not self.from_date:
			frappe.throw("From date required before Getting Short Leave Data")
		if not self.to_date:
			frappe.throw("To date required before Getting Short leave Data")
		if not self.branch:
			frappe.throw("Plant is required for Getting Short Leave Data")

		employee_data = frappe.db.sql("""SELECT a.employee,a.employee_name,a.status,a.custom_designation,a.attendance_date,a.company,TIME(a.out_time),
					a.department,a.plant,a.attendance_request,a.late_entry,a.early_exit,a.custom_short_leave,a.shift,a.working_hours,a.in_time,
					e.payroll_cost_center as cost_center,e.attendance_device_id as biometric_id,a.name,
					s.start_time,s.end_time,s.working_hours_threshold_for_half_day,s.custom_threshold_for_short_leave,s.custom_is_shift_rotation,
					b.custom_allowed_short_leave,b.custom_allowed_late_entrys,b.custom_allowed_early_exits
					FROM `tabAttendance` a
					LEFT JOIN `tabEmployee` e on e.employee = a.employee
					LEFT JOIN `tabBranch` b on b.branch = a.plant
					LEFT JOIN `tabShift Type` s on s.name =  a.shift
					WHERE a.plant = "{0}"
					AND a.status !=  "Absent"
					AND a.docstatus != 2 
					AND (
						(a.custom_short_leave != 0 AND a.attendance_date BETWEEN "{1}" AND "{2}")
						OR (a.late_entry = 1 AND a.attendance_date BETWEEN "{1}" AND "{2}")
						OR (a.early_exit = 1 AND a.attendance_date BETWEEN "{1}" AND "{2}")
					)
				""".format(self.branch,self.from_date,self.to_date),as_dict=1)	

		b = frappe.get_doc("Branch", self.branch)
		remove_short_leave_rec = int(b.custom_allowed_short_leave) if b.custom_allowed_short_leave else 0
		remove_early_exit_rec = int(b.custom_allowed_early_exits) if b.custom_allowed_early_exits else 0
		remove_late_entry_rec = int(b.custom_allowed_late_entrys)if b.custom_allowed_late_entrys else 0
		
		remove_short_leave_data = {}
		remove_early_exit_data = {}
		remove_late_entry_data = {}

		new_employee_data = []
		for record in employee_data:
			employee = record["employee"]
			
			if record["custom_short_leave"] !=0:	
				if employee not in remove_short_leave_data:
					remove_short_leave_data[employee] = 0
				if remove_short_leave_data[employee] < remove_short_leave_rec:
					remove_short_leave_data[employee] += 1
				else:
					new_employee_data.append(record)

			elif record["late_entry"] !=0:		
				if employee not in remove_late_entry_data:
					remove_late_entry_data[employee] = 0
				if remove_late_entry_data[employee]<remove_late_entry_rec:
					remove_late_entry_data[employee] +=1
				else:
					new_employee_data.append(record)

			elif record["early_exit"] !=0:	
				if employee not in remove_early_exit_data:
					remove_early_exit_data[employee] = 0
				if remove_early_exit_data[employee]<remove_early_exit_rec:
					remove_early_exit_data[employee] +=1
				else:
					new_employee_data.append(record)

			if remove_short_leave_rec > 0:
				employee_data = [record for record in employee_data if remove_short_leave_data.get(record["employee"], 0) >= remove_short_leave_rec]

			if remove_late_entry_rec > 0:
				employee_data = [record for record in employee_data if remove_late_entry_data.get(record["employee"], 0) >= remove_late_entry_rec]
				
			if remove_early_exit_rec > 0:
				employee_data = [record for record in employee_data if remove_early_exit_data.get(record["employee"], 0) >= remove_early_exit_rec]

		employee_data = new_employee_data

		if not employee_data:
			frappe.msgprint(f"No data found from {self.from_date} to {self.to_date} for {self.branch} plant")
			self.short_leave_calculation_details=[]
		
		if employee_data:
			self.short_leave_calculation_details=[]
			
			for att in employee_data:
				remarks = ""
				if att.late_entry:
					remarks = "Late Entry"
				if att.custom_short_leave:
					remarks = "Short Leave"
				if att.early_exit:
					remarks = "Early Exit"
				self.append("short_leave_calculation_details",{
					"employee":att.employee,
					"employee_name":att.employee_name,
					"designation":att.custom_designation,
					"department":att.department,
					"attendance_date":att.attendance_date,
					"cost_center":att.cost_center,
					"biometric_id":att.biometric_id,
					"shift_type":att.shift,
					"plant":att.plant,
					"remarks":remarks
				})

	@frappe.whitelist()
	def on_submit(self):
		for emp in self.short_leave_calculation_details:
			if emp.leave_type_for_half_day:
				existing_attendance = frappe.get_doc("Attendance",{"employee":emp.employee,"attendance_date":emp.attendance_date})
				if existing_attendance:					
					frappe.db.set_value("Attendance",existing_attendance.name,"docstatus",2)
					frappe.db.commit()
					create_leave_application(self, emp)
					doc = frappe.get_doc("Leave Application",{"custom_reference_no":self.name})
					if doc:
						att_doc = frappe.get_doc("Attendance",{"employee":doc.employee,"leave_type":doc.leave_type,"attendance_date":doc.from_date})
						if att_doc:
							att_doc.db_set("custom_reference_type","Short Leave Calculation")
							att_doc.db_set("custom_reference_no",doc.custom_reference_no)
							season=""
							gsd = get_season_details(emp.plant)
							if gsd:
								for d in gsd:
									if getdate(d.year_start_date)<=emp.attendance_date<=getdate(d.year_end_date):
										season= "Season"
									else:
										season="Off Season"
							else:
								season="Off Season"
							att_doc.db_set("custom_season",season)
								
							
					

@frappe.whitelist()
def create_leave_application(self, emp):
    new_leave = frappe.new_doc("Leave Application")
    new_leave.employee = emp.employee
    new_leave.leave_type = emp.leave_type_for_half_day
    new_leave.from_date = emp.attendance_date
    new_leave.to_date = emp.attendance_date
    new_leave.half_day = 1
    new_leave.description = f"Marked Short Leave based on {emp.remarks}"
    new_leave.status = "Approved"
    new_leave.custom_reference_type = "Short Leave Calculation"
    new_leave.custom_reference_no = self.name
    new_leave.save(ignore_permissions=True)
    new_leave.submit()

