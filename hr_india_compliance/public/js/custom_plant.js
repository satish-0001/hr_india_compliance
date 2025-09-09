// Copyright (c) 2023, Dexciss and contributors
// For license information, please see license.txt

frappe.ui.form.on("Branch", {
// })
    refresh: function(frm) {    
        console.log("*****************************");
        frm.fields_dict.custom_holiday_wise_shift_rotation.grid.wrapper.find('.grid-add-row').hide();
        cur_frm.fields_dict.custom_holiday_wise_shift_rotation.grid.wrapper.find(".grid-remove-rows").hide();
        
        frm.fields_dict['custom_holiday_wise_shift_rotation'].grid.get_field('column_a').get_query = function(doc, cdt, cdn) {
            return applyShiftFilter(doc, cdt, cdn, 'column_a');
        };
        
        frm.fields_dict['custom_holiday_wise_shift_rotation'].grid.get_field('column_b').get_query = function(doc, cdt, cdn) {
            return applyShiftFilter(doc, cdt, cdn, 'column_b');
        };
        
        frm.fields_dict['custom_holiday_wise_shift_rotation'].grid.get_field('column_c').get_query = function(doc, cdt, cdn) {
            return applyShiftFilter(doc, cdt, cdn, 'column_c');
        };
    },
    // validate: function(frm) {
    //     if (frm.doc.custom_allow_shift_rotation_ != 0 && frm.doc.custom_shift_rotation_day !=0)
    //     $.each(frm.doc.custom_holiday_wise_shift_rotation || [], function(i, row) {
    //         if (row.weekly_off_day && !row.column_a ) {
    //             frappe.show_alert({
    //                 message: "Column A is mandatory when Weekly Off Day is selected.",
    //                 indicator: "red"
    //             });
    //             frappe.validated = false;
    //         }
    //         if (row.weekly_off_day && !row.column_b && !row.column_c) {
    //             frappe.show_alert({
    //                 message: "Column B is mandatory when Weekly Off Day is selected.",
    //                 indicator: "red"
    //             });
    //             frappe.validated = false;
    //         }
    //         if (row.weekly_off_day && !row.column_c) {
    //             frappe.show_alert({
    //                 message: "Column C is mandatory when Weekly Off Day is selected.",
    //                 indicator: "red"
    //             });
    //             frappe.validated = false;
    //         }
    //     });
    // },
//     custom_no_of_shift: function(frm) {
//         var noOfShifts = frm.doc.custom_no_of_shift;
//         var days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

//         if (!isNaN(noOfShifts) && noOfShifts > 0) {
//             frm.doc.custom_holiday_wise_shift_rotation = [];

//             for (var i = 0; i < noOfShifts; i++) {
//                 days.forEach(function(day) {
//                     frm.add_child('custom_holiday_wise_shift_rotation', {
//                         weekly_off_day: day
//                     });
//                 });
//             }
//             frm.refresh_field('custom_holiday_wise_shift_rotation');
//             console.log(noOfShifts,"time colums are added , Table Refreshed ")
//         } else {
//             frappe.msgprint(__("Value for No Of Shift Is Greater Than 0."));
//         }
//     }

});

function applyShiftFilter(doc, cdt, cdn, fieldname) {
    const child = locals[cdt][cdn];
    const selectedShifts = [];
    
    // Collect selected shifts in previous columns in the same row
    for (const field of ['column_a', 'column_b', 'column_c']) {
        if (field !== fieldname) {
            const shift = child[field];
            if (shift) {
                selectedShifts.push(shift);
            }
        }
    }

    return {
        filters: {
            // 'custom_weekly_off_days': child.weekly_off_day,
            'name': ['not in', selectedShifts],
            'custom_is_shift_rotation': 1  // Only select shifts with custom_is_shift_rotation checkbox checked
        }
    };

}



