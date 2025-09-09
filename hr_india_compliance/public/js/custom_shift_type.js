
frappe.ui.form.on('Shift Type', {
	refresh: function(frm) {
		frm.add_custom_button(
			__('Mark Attendance Branch Wise '),
			() => {
				frappe.prompt(
					[{
						label: __('Select Plant'),
						fieldname: 'plant',
						fieldtype: 'Link',
						options: 'Branch',
						reqd: 1,
					}],
					(data) => {
						frm.call({
							method: 'hr_india_compliance.hr_india_compliance.custom_shift_type.plant_wise_attendance',
							args: {
								plant: data.plant,
								shift_type_name: frm.doc.name,
							},
							freeze: true,
							callback: () => {
								frappe.msgprint(__('Attendance has been marked as per employee check-ins'));
							}
						});
					},
					__('Select Plant'),
					__('Mark Attendance')
				);
			},
			__('Mark Attendance Manually')
		);
		frm.add_custom_button(
			__('Mark Attendance Employee Wise'),
			() => {
				frappe.prompt(
					[{
						label: __('Select Employee'),
						fieldname: 'employee',
						fieldtype: 'Link',
						options: 'Employee',
						reqd: 1,
					}],
					(data) => {
						frm.call({
							method: 'hr_india_compliance.hr_india_compliance.custom_shift_type.process_auto_attendance_employee_wise',
							args: {
								selected_employee: data.employee,
								shift_type_name: frm.doc.name,
							},
							freeze: true,
							callback: () => {
								frappe.msgprint(__('Attendance has been marked as per employee check-ins'));
							}
						});
					},
					__('Select Employee'),
					__('Mark Employee Attendane')
				);
			},
			__('Mark Attendance Manually')
		
		);
	}
});

