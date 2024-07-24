// Copyright (c) 2023, quantdairy and contributors
// For license information, please see license.txt

frappe.ui.form.on('Variable Deduction', {
	// refresh: function(frm) {

	// }
});


frappe.ui.form.on('Variable Deduction', {
	setup: function(frm) {
		frm.set_query("farmer_code", function(doc) {
			return {
				filters: [
				    ['Supplier', 'dcs_id', '=', frm.doc.warehouse_branch],
				]
			};
		});
	},
	paid_from_account_name: function(frm) {
		frm.set_query("paid_from_account_name", function(doc) {
			return {
				filters: [
				    ['Bank Account', 'is_company_account', '=', true],
				]
			};
		});
	}

})
