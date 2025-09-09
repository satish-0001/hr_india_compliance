// Copyright (c) 2023, Dexciss Technology Pvt Ltd and contributors
// For license information, please see license.txt

frappe.query_reports["Bank Remittance With Branch"] = {
	"filters": [
		{
			fieldname:"company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1,
			on_change: () => {
				const company = frappe.query_report.get_filter_value('company');
				const branch_filter = frappe.query_report.get_filter('branch');
				if (company) {
					branch_filter.df.get_query = () => {
						return {
							filters: {
								'company': company
							}
						};
					};
				}
			}
		},
		{
			fieldname:"branch",
			label: __("Branch"),
			fieldtype: "Link",
			options: "Branch",
			default: frappe.defaults.get_user_default("Branch"),
		},
		{
			fieldname:"from_date",
			label: __("From Date"),
			fieldtype: "Date",
		},
		{
			fieldname:"to_date",
			label: __("To Date"),
			fieldtype: "Date",
		},

	]
}
