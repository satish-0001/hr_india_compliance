// Copyright (c) 2024, Dexciss Technology Pvt Ltd and contributors
// For license information, please see license.txt

frappe.ui.form.on("Scheduled Job Manual Settings", {
    scheduled_job_type:function(frm){
        if (frm.doc.scheduled_job_type === "run_leave_allocation_method") {
            frm.dashboard.add_comment(
                __(
                    "Runnibg this methos will be affect on your Leave Allocation records."
                ),
                "red",
                true
            );
            frm.set_df_property("to_date","read_only",1)

        }else{
            frm.set_df_property("to_date","read_only",0)
        }
        frm.set_value("from_date",null)
        frm.set_value("to_date",null)
        frm.refresh_field("from_date")
        frm.refresh_field("to_date")
    },
	refresh(frm) {
        
        frm.disable_save() 
        frappe.call({
            method: "get_function_names",
            doc:frm.doc,
            args: {
                module_path: "hr_india_compliance.hr_india_compliance_utils"
            },
            callback: function(r) {
                if (r.message) {
                    var jobs_dict = [];
                    r.message.forEach(function(fn_name) {
                        jobs_dict.push(fn_name);
                    });
                    frm.fields_dict.scheduled_job_type.set_data(jobs_dict);
                }
            }
        });
    },
    from_date: function(frm) {
        if (frm.doc.scheduled_job_type === "run_leave_allocation_method") {
            frm.set_value('to_date', "")
            var fromDate = frm.doc.from_date;
            var toDate = frm.doc.to_date;
            if (fromDate && toDate) {
                var fromDateTime = new Date(fromDate).getTime();
                var toDateTime = new Date(toDate).getTime();

                if (fromDateTime > toDateTime) {
                    frappe.msgprint(__('From Date cannot be greater than To Date.'));
                    frm.set_value('from_date', toDate);
                }
            }
        
            var fromDate = frm.doc.from_date;
            if (fromDate) {
                var parts = fromDate.split('-');
                var year = parseInt(parts[0]);
                var month = parseInt(parts[1]);
                var lastDayOfMonth = new Date(year, month, 0).getDate();

                var toDate = year + '-' + (month < 10 ? '0' + month : month) + '-' + lastDayOfMonth;
                frm.set_value('to_date', toDate);
            } 
        } 
    },
    to_date: function(frm) {
        // if (frm.doc.scheduled_job_type === "run_leave_allocation_method") {
            var fromDate = frm.doc.from_date;
            var toDate = frm.doc.to_date;
    
            if (fromDate && toDate) {
                var fromDateTime = new Date(fromDate).setHours(0, 0, 0, 0);
                var toDateTime = new Date(toDate).setHours(0, 0, 0, 0);
                var todayDateTime = new Date().setHours(0, 0, 0, 0);
    
                console.log('fromDateTime:', fromDateTime);
                console.log('toDateTime:', toDateTime);
                console.log('todayDateTime:', todayDateTime);
    
                if (toDateTime < fromDateTime) {
                    frappe.msgprint(__('To Date cannot be smaller than From Date.'));
                    var lastDayOfMonth = new Date(new Date(fromDate).getFullYear(), new Date(fromDate).getMonth() + 1, 0);
                    frm.set_value('to_date', lastDayOfMonth);
                } else if (toDateTime > todayDateTime) {
                    frappe.msgprint(__('To Date cannot be greater than today\'s date.'));
                    frm.set_value('to_date', new Date());
                }
            }
        // }
    },
    
    run_job: function(frm) {
        var selected_job = frm.doc.scheduled_job_type;
        const warning_html = `<p class="bold">
				${__("Are you sure you want to run this method manually?")}
			</p>`;
        let proceed_action = () => {
            if (selected_job) {
                var method_format = "hr_india_compliance.hr_india_compliance_utils." + selected_job;
                frappe.call({
                    method: method_format,
                    args:{
                        MANUAL_RUN:"True",
                        FROM_DATE:frm.doc.from_date,
                        TO_DATE:frm.doc.to_date
                    },
                    callback: function(r) {
                        console.log("Triggered function: " + selected_job);
                        frappe.add_comment
                    }
                });
            }
        };
        if(frm.doc.scheduled_job_type){
            if (!frm.doc.from_date) {
                frappe.throw("Please select from date first")
            }
            if (!frm.doc.to_date) {
                frappe.throw("Please select to date first")
            }
            frappe.warn(
                __("Alert"),
                warning_html,
                proceed_action,
                __("Run Anyway")
            )
        }else{
            frappe.throw("Please select scheduled job type first")
        }
    }
});
