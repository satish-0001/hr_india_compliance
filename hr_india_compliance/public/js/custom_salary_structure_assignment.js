frappe.ui.form.on("Salary Structure Assignment",{
    refresh:function(frm){
        if (frm.doc.docstatus === 1) {
            frm.toggle_display("custom_update_salary_breakup",true)
        } else {
            frm.toggle_display("custom_update_salary_breakup",false)
        }
    },
    custom_update_salary_breakup: function(frm) {
        frappe.call({
            method:"hr_india_compliance.salary_structure_assignment.get_salary_breakup",
            args:{
                doc:frm.doc
            },
            callback:function(r) {
                if (r.message) {
                    if (r.message[0]) {
                        frm.clear_table("custom_salary_detail")
                        $.each(r.message[0],function(i,d){
                            frm.add_child("custom_salary_detail",{
                                salary_component:d.salary_component,
                                amount:d.amount
                            })
                        })
                    }
                    if (r.message[1]) {
                        frm.clear_table("custom_earning_ctc")
                        $.each(r.message[1],function(i,d){
                            frm.add_child("custom_earning_ctc",{
                                salary_component:d.salary_component,
                                amount_monthly:d.amount_monthly,
                                amount_yearly:d.amount_yearly
                            })
                        })
                    }
                    frm.set_value("custom_gross_salary",r.message[2])
                    frm.set_value("custom_total_ctc_monthly",r.message[3])
                    frm.set_value("custom_total_ctc_yearly",r.message[4])
                    frm.refresh_field("custom_salary_detail")
                    frm.refresh_field("custom_earning_ctc")
                    frm.refresh_field("custom_gross_salary")
                    frm.refresh_field("custom_total_ctc_monthly")
                    frm.refresh_field("custom_total_ctc_yearly")
                    frm.save("Update")
                }
            }
        })
    }
})