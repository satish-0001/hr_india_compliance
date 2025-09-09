import frappe
from frappe.model.document import Document

@frappe.whitelist()
def create_job_opening(doc):
    doc = frappe.get_doc(frappe.parse_json(doc))
    
    for detail in doc.staffing_details:
        job_opening = frappe.new_doc('Job Opening')
        job_opening.job_title = f"Job Opening for {detail.designation}"
        job_opening.designation = detail.designation
        job_opening.employment_type = detail.custom_employment_type
        job_opening.department=doc.department
        job_opening.custom_current_openings=detail.current_openings 
        job_opening.closes_on=doc.to_date
        job_opening.insert()
        
    return "Job Opening created successfully"


def validate(self,method):
    for detail in self.staffing_details:
        designation = detail.designation
        if designation:
            count = frappe.db.count('Employee', {'designation': designation})
            detail.custom_current_department_designation_count = count