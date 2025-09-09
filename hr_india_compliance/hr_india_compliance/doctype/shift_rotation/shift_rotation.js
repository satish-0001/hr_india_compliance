// Copyright (c) 2023, Dexciss Technology Pvt Ltd and contributors
// For license information, please see license.txt

frappe.ui.form.on('Shift Rotation', {
	from_date: function(frm) {
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
	refresh: function(frm) {
		if (frm.doc.docstatus != 1)
		frm.add_custom_button(__("Get Data"),function(){
			frappe.call({
				method:"get_data",
				doc:frm.doc,
				callback:function(){
					console.log("*********************")
					frm.refresh_field("shift_rotation_details")
					// frm.set_df_property('get_data', 'hidden', true);
				}
			})	
		});
        frm.set_query("employee","shift_rotation_details",function(doc,cdt,cdn){
            return{
                filters:[
                    ["branch","=",frm.doc.plant]
                ]
            }
        })		
	},
    	
});

