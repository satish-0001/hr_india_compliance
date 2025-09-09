// Copyright (c) 2023, Dexciss Technology Pvt Ltd and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Daily Absenteeism"] = {
	"filters": [
		{
			"fieldname":"plant",
			"label":__("Plant"),
			"fieldtype":"Link",
			"options":"Branch",
			"reqd":1
		},
		{
			"fieldname":"department",
			"label":__("Department"),
			"fieldtype":"Link",
			"options":"Department"
		},
		{
            "fieldname": "date",
            "label": __("Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
			"reqd":1
        },
		{
			"fieldname": "shift",
			"label": "Shift",
			"fieldtype": "Link",
			"options":"Shift Type",
			"width": 170

		}

	],
	onload: function(report) {
		report.refresh();
	},
	onchange: function(report) {
		report.refresh();
	},
};
