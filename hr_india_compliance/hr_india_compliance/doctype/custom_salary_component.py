
import frappe
@frappe.whitelist()
def get_records_with_custom_field(doc_name, field_name):
    doc = frappe.get_doc("Salary Component", doc_name)
    filters = {field_name: 1, "name": ("!=", doc_name)}
    existing_records = frappe.get_all("Salary Component", filters=filters)
    
    record_names = [record.name for record in existing_records]
    return {"records": record_names}
