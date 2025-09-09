// Copyright (c) 2023, Dexciss and contributors
// For license information, please see license.txt
frappe.ui.form.on('Salary Component', {
    refresh:function(frm){
        frm.fields_dict['custom_statistical_payment_component'].get_query = function(doc, cdt, cdn) {
            return {
                filters: [
                    ['Salary Component', 'statistical_component', '!=', 1],
                ]
            };
        };
    },
    custom_pf_salary: function(frm) {
        checkAndHandleCheckbox(frm, 'custom_pf_salary');
    },
    custom_pension_salary: function(frm) {
        checkAndHandleCheckbox(frm, 'custom_pension_salary');
    },
    custom_pf_12_per: function(frm) {
        checkAndHandleCheckbox(frm, 'custom_pf_12_per');
    },
    custom_employee_pension_amount: function(frm) {
        checkAndHandleCheckbox(frm, 'custom_employee_pension_amount');
    },
    custom_employee_pf: function(frm) {
        checkAndHandleCheckbox(frm, 'custom_employee_pf');
    }
});

function checkAndHandleCheckbox(frm, field_name) {
    if (frm.doc[field_name]) {
        frappe.call({
            method: 'hr_india_compliance.hr_india_compliance.doctype.custom_salary_component.get_records_with_custom_field',
            args: {
                doc_name: frm.doc.name,
                field_name: field_name
            },
            callback: function(response) {
                if (response.message && response.message.records.length > 0) {
                    const recordNames = response.message.records.join(', ');
                    const message = `This field is already in use in the ${recordNames} record`;
                    frappe.msgprint(message);
                    frm.doc[field_name] = 0;
                    frm.refresh_field(field_name);
                }
            }
        });
    }
}

