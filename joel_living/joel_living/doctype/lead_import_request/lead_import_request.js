// Copyright (c) 2025, Subburaj and contributors
// For license information, please see license.txt

frappe.ui.form.on("Lead Import Request", {
	refresh: function (frm) {
		// Show main Excel preview if file exists
		frm.fields_dict.html_lead.$wrapper.empty();
		frm.fields_dict.failed_lead_html.$wrapper.empty();
		if (frm.doc.file) {
			frappe.call({
				method: "joel_living.joel_living.doctype.lead_import_request.lead_import_request.preview_excel",
				args: { docname: frm.doc.name },
				callback: function (r) {
					if (r.message) {
						let html = `
                <div style="margin-top:20px;">
                    <h4 style="background-color:#e2f0fd; padding:8px; border-radius:4px;">Uploaded File Preview</h4>
                    <div style="overflow-x:auto; border:1px solid #ddd; padding:5px; border-radius:4px; background-color:#ffffff;">
                        ${r.message}
                    </div>
                </div>`;
						frm.fields_dict.html_lead.$wrapper.html(html);
					}
				},
			});
		}

		// Show failed leads preview if file exists
		if (frm.doc.failed_leads_file) {
			frappe.call({
				method: "joel_living.joel_living.doctype.lead_import_request.lead_import_request.preview_failed_leads",
				args: { docname: frm.doc.name },
				callback: function (r) {
					if (r.message) {
						let html = `
                <div style="margin-top:20px;">
                    <h4 style="background-color:#fde2e2; padding:8px; border-radius:4px;">Failed Leads Preview</h4>
                    <div style="overflow-x:auto; border:1px solid #ddd; padding:5px; border-radius:4px; background-color:#ffffff;">
                        ${r.message}
                    </div>
                </div>`;
						frm.fields_dict.failed_lead_html.$wrapper.html(html);
					}
				},
			});
		}

		let allowed_roles = ["Super Admin", "Admin"];

		// check if session user has at least one role from allowed_roles
		if (allowed_roles.some((role) => frappe.user.has_role(role))  && !frm.doc.__islocal) {
			// Clear wrapper first
			frm.fields_dict.download_button.$wrapper.empty();

			// Wrapper div with padding
			let wrapper_html = `<div style="padding:20px;">`;

			// Show button if file exists
			if (frm.doc.file) {
				wrapper_html += `
			<button class="btn btn-primary btn-sm m-1" id="download_file_btn">
				<i class="fa fa-download"></i> Download Imported Excel File
			</button>
		`;
			}

			// Show button if failed_leads_file exists
			if (frm.doc.failed_leads_file) {
				wrapper_html += `
			<button class="btn btn-danger btn-sm m-1" id="download_failed_file_btn">
				<i class="fa fa-file-excel-o"></i> Download Failed Leads
			</button>
		`;
			}

			wrapper_html += `</div>`;
			frm.fields_dict.download_button.$wrapper.html(wrapper_html);

			// Attach click events
			if (frm.doc.file) {
				frm.fields_dict.download_button.$wrapper
					.find("#download_file_btn")
					.on("click", function () {
						window.open(frm.doc.file, "_blank");
					});
			}
			if (frm.doc.failed_leads_file) {
				frm.fields_dict.download_button.$wrapper
					.find("#download_failed_file_btn")
					.on("click", function () {
						window.open(frm.doc.failed_leads_file, "_blank");
					});
			}
			// Action buttons if status is Pending
			if (frm.doc.status === "Pending") {
				// Approve button with confirmation
				frm.add_custom_button(
					"Approve",
					function () {
						frappe.confirm(
							"Are you sure you want to <b>Approve</b> this Lead Import Request? This action cannot be undone.",
							function () {
								frappe.call({
									method: "joel_living.joel_living.doctype.lead_import_request.lead_import_request.approve_request",
									args: { docname: frm.doc.name },
									callback: function () {
										frappe.msgprint(
											"Lead Import Request has been approved successfully."
										);
										frm.reload_doc();
									},
								});
							},
							function () {
								frappe.msgprint("Approval cancelled.");
							}
						);
					},
					"Actions"
				);

				// Reject button with reason prompt
				frm.add_custom_button(
					"Reject",
					function () {
						frappe.prompt(
							[
								{
									fieldname: "rejection_reason",
									fieldtype: "Small Text",
									label: "Rejection Reason",
									reqd: 1,
								},
							],
							function (values) {
								// On submit
								frappe.call({
									method: "joel_living.joel_living.doctype.lead_import_request.lead_import_request.reject_request",
									args: {
										docname: frm.doc.name,
										reason: values.rejection_reason,
									},
									callback: function () {
										frappe.msgprint("Lead Import Request has been rejected.");
										frm.reload_doc();
									},
								});
							},
							"Confirm Rejection",
							"Reject"
						);
					},
					"Actions"
				);
			}
			if (frm.doc.status === "Rejected") {
				frm.add_custom_button(
					"Move to Pending",
					function () {
						frappe.confirm(
							"Are you sure you want to move this Rejected request back to <b>Pending</b>?",
							function () {
								frappe.call({
									method: "joel_living.joel_living.doctype.lead_import_request.lead_import_request.move_to_pending",
									args: { docname: frm.doc.name },
									callback: function () {
										frappe.msgprint("Request status changed back to Pending.");
										frm.reload_doc();
									},
								});
							},
							function () {
								frappe.msgprint("Action cancelled.");
							}
						);
					},
					"Actions"
				);
			}
		}
		// 🔒 Hide the Clear button after Approved/Rejected/Partially Approved
		setTimeout(() => {
			$(frm.fields_dict.file.$wrapper).find('[data-action="clear_attachment"]').show();
		}, 100);

		// Hide if status is in restricted list
		if (["Approved", "Partially Approved", "Rejected", "Failed"].includes(frm.doc.status)) {
			setTimeout(() => {
				$(frm.fields_dict.file.$wrapper).find('[data-action="clear_attachment"]').hide();
			}, 300);
		}
	},
});

frappe.realtime.on("lead_import_progress", (data) => {
	if (data.docname === cur_frm.doc.name) {
		frappe.msgprint(
			`Lead Import ${data.status}: ${data.added || 0} added, ${data.failed || 0} failed`
		);
		cur_frm.reload_doc();
	}
});
