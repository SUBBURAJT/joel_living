// Copyright (c) 2025, Subburaj and contributors
// For license information, please see license.txt

frappe.ui.form.on("Lead Export Request", {
    refresh: function(frm) {
        if (frm.doc.status === "Pending Approval") {
            // Approve button
            frm.add_custom_button(__("Approve"), function() {
                frappe.call({
                    method: "joel_living.joel_living.doctype.lead_export_request.lead_export_request.approve_export_request",
                    args: { docname: frm.doc.name },
                    callback: function(r) {
                        if (!r.exc) {
                            if (r.message && r.message.status === "success") {
                                frappe.msgprint(__("Export Request Approved. Excel generated."));
                            } else {
                                frappe.msgprint(__("Export Request Failed: " + (r.message.error || "Unknown error")));
                            }
                            frm.reload_doc();
                        }
                    }
                });

            }, __("Actions"));

            // Reject button
            frm.add_custom_button(__("Reject"), function() {
                frappe.prompt(
                    [
                        {
                            label: __("Rejection Notes"),
                            fieldname: "rejected_notes",
                            fieldtype: "Small Text",
                            reqd: 1
                        }
                    ],
                    function(values) {
                        frappe.call({
                            method: "joel_living.joel_living.doctype.lead_export_request.lead_export_request.reject_export_request",
                            args: {
                                docname: frm.doc.name,
                                rejected_notes: values.rejected_notes
                            },
                            callback: function(r) {
                                if (!r.exc) {
                                    frappe.msgprint(__("Export Request Rejected."));
                                    frm.reload_doc();
                                }
                            }
                        });
                    },
                    __("Reject Export Request"),
                    __("Reject")
                );
            }, __("Actions"));
        }
    }
});
