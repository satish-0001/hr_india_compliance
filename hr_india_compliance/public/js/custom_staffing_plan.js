frappe.ui.form.on('Staffing Plan', {
    refresh: function(frm) {
        if (!frm.is_new()) {

            frm.add_custom_button(__('Create Job Opening'), function() {
            frappe.call({
                method: 'hr_india_compliance.custom_staffing_plan.create_job_opening',
                // doc:frm.doc,
                args: {
                    doc: frm.doc
                },
                callback: function(r) {
                    if (!r.exc) {
                        frappe.msgprint(__('Job Opening created successfully'));

                    }
                }
            });
        });
    }
}

});
