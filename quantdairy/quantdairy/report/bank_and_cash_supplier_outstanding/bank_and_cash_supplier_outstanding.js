// Copyright (c) 2024, quantdairy and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Bank and Cash Supplier Outstanding"] = {
	"filters": [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			reqd: 1,
			width: "60px",
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1,
			width: "60px",
		},
		{
			fieldname: "party",
			label: __("Supplier"),
			fieldtype: "Link",
			options: "Supplier",
			on_change: () => {
				var party = frappe.query_report.get_filter_value("party");
				if (party) {
					frappe.db.get_value("Supplier", party, ["tax_id", "customer_name"], function (value) {
						frappe.query_report.set_filter_value("tax_id", value["tax_id"]);
						frappe.query_report.set_filter_value("customer_name", value["customer_name"]);
					});
				} else {
					frappe.query_report.set_filter_value("tax_id", "");
					frappe.query_report.set_filter_value("customer_name", "");
				}
			},
		},
		{
			fieldname: "supplier_group",
			label: __("Supplier Group"),
			fieldtype: "MultiSelectList",
			options: "Supplier Group",
			get_data: function(txt) {
				return frappe.db.get_link_options("Supplier Group", txt);
			},
			reqd: 0,
		}
		
	]
};
