// Copyright (c) 2025, Dexciss Technology Pvt Ltd and contributors
// For license information, please see license.txt

frappe.query_reports["Tax Withholding Report Enhacement"] = {
	"filters": [
		{
			fieldname: "employee",
			label: __("Employee"),
			fieldtype: "Link",
			width: "80",
			options:"Employee"
		},
		
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			width: "80",
			options:"Company",
			reqd:1
		},
		{
			"fieldname":"branch",
			"label": __("Plant"),
			"fieldtype": "Link",
			"options": "Branch",
			get_query: () => {
				var company = frappe.query_report.get_filter_value('company');
				return {
					filters: {
						'company': company
					}
				};
			}
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			width: "80",
			reqd: 1,
			default: frappe.datetime.month_start(frappe.datetime.get_today()),
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			width: "80",
			reqd: 1,
			default: frappe.datetime.get_today(),
		},
	]
};
