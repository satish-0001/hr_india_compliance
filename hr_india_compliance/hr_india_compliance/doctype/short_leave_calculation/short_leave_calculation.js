// Copyright (c) 2023, Dexciss Technology Pvt Ltd and contributors
// For license information, please see license.txt

frappe.ui.form.on('Short Leave Calculation', {
	refresh: function(frm) {
		let leave_details;
		let lwps;
		frm.set_query("leave_type_for_half_day", "short_leave_calculation_details", function(doc, cdt, cdn) {
			let child = locals[cdt][cdn];
			if (child.employee){
				frappe.call({
					method: "hrms.hr.doctype.leave_application.leave_application.get_leave_details",
					async: false,
					args: {
						employee: child.employee,
						date: frm.doc.from_date || frm.doc.to_date
					},
					callback: function(r) {
						if (r.message) {
							leave_details = r.message.leave_allocation;
							lwps = r.message.lwps;
						}
					}
				});
				let allowed_leave_types = Object.keys(leave_details);
				allowed_leave_types = Object.keys(leave_details).concat(lwps)
				return {
					filters: [
						["leave_type_name", "in", allowed_leave_types]
					]
				};		
			}
		});
		if (frm.doc.docstatus!=1){
			frm.add_custom_button("Get Data",function(){
				frappe.call({
					method:"get_data",
					doc:frm.doc,
					callback:function(){
						frm.refresh_field("short_leave_calculation_details")
					}
				})
			})
		}		
	},
	from_date: function(frm) {
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
    },
    to_date: function(frm) {
        var fromDate = frm.doc.from_date;
        var toDate = frm.doc.to_date;

        if (fromDate && toDate) {
            var fromDateTime = new Date(fromDate).getTime();
            var toDateTime = new Date(toDate).getTime();

            if (toDateTime < fromDateTime) {
                frappe.msgprint(__('To Date cannot be smaller than From Date.'));
                var lastDayOfMonth = new Date(new Date(fromDate).getFullYear(), new Date(fromDate).getMonth() + 1, 0).getDate();
                frm.set_value('to_date', new Date(new Date(fromDate).getFullYear(), new Date(fromDate).getMonth(), lastDayOfMonth));
            }
        }
    },
	on_submit:function(frm){
        frappe.show_alert({
            message:__('The Records are Updated Successfully'),
            indicator:'green'
        }, 3);
    }	
});

// on_submit: function(frm) {
// 	var toRemove = [];
// 	frm.doc.short_leave_calculation_details.forEach(function(child) {
// 		if (!child.leave_type_for_half_day) {
// 			toRemove.push(child.name);
// 		}
// 	});
// 	toRemove.forEach(function(name) {
// 		var index = frm.doc.short_leave_calculation_details.findIndex(function(child) {
// 			return child.name === name;
// 		});
// 		if (index !== -1) {
// 			frm.doc.short_leave_calculation_details.splice(index, 1);
// 		}
// 	});
// 	frm.refresh_field('short_leave_calculation_details');

// 	frappe.show_alert({
// 		message: __('Records have been updated successfully'),
// 		indicator: 'green'
// 	}, 5);
// }