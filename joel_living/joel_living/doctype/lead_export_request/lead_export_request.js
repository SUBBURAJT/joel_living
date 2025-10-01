// Copyright (c) 2025, Subburaj and contributors
// For license information, please see license.txt

frappe.ui.form.on("Lead Export Request", {
	refresh: function (frm) {
		let allowed_roles = ["Super Admin", "Admin"];

		// Clear wrapper first
		frm.fields_dict.download_button.$wrapper.empty();

		// Wrapper div with padding
		let wrapper_html = `<div style="padding:20px;">`;

		// Show button if file exists
		if (frm.doc.export_file) {
			wrapper_html += `
			<button class="btn btn-primary btn-sm m-1" id="download_file_btn">
				<i class="fa fa-download"></i> Download Approved Lead Excel File
			</button>
		`;
		}

		wrapper_html += `</div>`;
		frm.fields_dict.download_button.$wrapper.html(wrapper_html);

		// Attach click events
		if (frm.doc.export_file) {
			frm.fields_dict.download_button.$wrapper
				.find("#download_file_btn")
				.on("click", function () {
					window.open(frm.doc.export_file, "_blank");
				});
		}
		// ✅ Ensure lead_list is parsed correctly
		let lead_list = [];
		if (frm.doc.lead_list) {
			try {
				lead_list = Array.isArray(frm.doc.lead_list)
					? frm.doc.lead_list
					: JSON.parse(frm.doc.lead_list);
			} catch (e) {
				console.error("Invalid lead_list format", e);
			}
		}

		if (lead_list && lead_list.length) {
			frappe.call({
				method: "frappe.client.get_list",
				args: {
					doctype: "Lead",
					filters: {
						name: ["in", lead_list],
					},
					fields: [
						"name",
						"lead_name",
						"job_title",
						"custom_main_lead_source",
						"custom_secondary_lead_sources",
						"custom_lead_category",
						"email_id",
						"mobile_no",
					],
					limit_page_length: 1000,
				},
				callback: function (r) {
					if (r.message && r.message.length) {
						let rows = r.message
							.map(
								(lead, idx) => `
                                <tr>
                                    <td>${idx + 1}</td>
                                    <td><a href="/app/lead/${lead.name}" target="_blank">
                                        ${lead.name || ""}
                                    </a></td>
                                    <td>${lead.lead_name || ""}</td>
                                    <td>${lead.job_title || ""}</td>
                                    <td>${lead.custom_main_lead_source || ""}</td>
                                    <td>${lead.custom_secondary_lead_sources || ""}</td>
                                    <td>${lead.custom_lead_category || ""}</td>
                                    <td>${lead.email_id || ""}</td>
                                    <td>${lead.mobile_no || ""}</td>
                                </tr>`
							)
							.join("");

						let table_html = `
                            <table class="table table-bordered table-sm">
                                <thead style="background-color:#3498DB;color:white;text-align: left;">
                                    <tr>
                                        <th>#</th>
                                        <th>Lead ID</th>
                                        <th>Lead Name</th>
                                        <th>Job Title</th>
                                        <th>Main Lead Source</th>
                                        <th>Secondary Lead Source</th>
                                        <th>Lead Category</th>
                                        <th>Email</th>
                                        <th>Mobile No</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${rows}
                                </tbody>
                            </table>
                        `;

						frm.fields_dict.lead_export_list_html.$wrapper.html(table_html);
					} else {
						frm.fields_dict.lead_export_list_html.$wrapper.html(
							"<p>No leads found in this request.</p>"
						);
					}
				},
			});
		} else {
			frm.fields_dict.lead_export_list_html.$wrapper.html(
				"<p>No leads linked to this request.</p>"
			);
		}
		// check if session user has at least one role from allowed_roles
		if (allowed_roles.some((role) => frappe.user.has_role(role))) {
			if (frm.doc.status === "Pending Approval") {
				// Approve button
				frm.add_custom_button(
					__("Approve"),
					function () {
						frappe.confirm(
							"Are you sure you want to <b>Approve</b> this Export Request? This will generate the Excel file.",
							function () {
								// On confirm → call backend
								frappe.call({
									method: "joel_living.joel_living.doctype.lead_export_request.lead_export_request.approve_export_request",
									args: { docname: frm.doc.name },
									callback: function (r) {
										if (!r.exc) {
											if (r.message && r.message.status === "success") {
												frappe.msgprint(
													__("Export Request Approved. Excel generated.")
												);
											} else {
												frappe.msgprint(
													__(
														"Export Request Failed: " +
															(r.message.error || "Unknown error")
													)
												);
											}
											frm.reload_doc();
										}
									},
								});
							},
							function () {
								frappe.msgprint("Approval cancelled.");
							}
						);
					},
					__("Actions")
				);

				// Reject button
				frm.add_custom_button(
					__("Reject"),
					function () {
						frappe.prompt(
							[
								{
									label: __("Rejection Notes"),
									fieldname: "rejected_notes",
									fieldtype: "Small Text",
									reqd: 1,
								},
							],
							function (values) {
								frappe.call({
									method: "joel_living.joel_living.doctype.lead_export_request.lead_export_request.reject_export_request",
									args: {
										docname: frm.doc.name,
										rejected_notes: values.rejected_notes,
									},
									callback: function (r) {
										if (!r.exc) {
											frappe.msgprint(__("Export Request Rejected."));
											frm.reload_doc();
										}
									},
								});
							},
							__("Reject Export Request"),
							__("Reject")
						);
					},
					__("Actions")
				);
			}
		}
	},
});
