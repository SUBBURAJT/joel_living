frappe.ui.form.on("Sales Completion Form", {
    refresh(frm) {
        // First, remove any existing buttons to prevent duplicates on refresh
        frm.remove_custom_button('Approve Sale');

        // Define the conditions for showing the button
        const can_approve = frappe.user.has_role(['Admin', 'Super Admin']);
        const is_pending_approval = frm.doc.docstatus === 0; // 0 = Draft

        // Only show the button if the user has the role AND the form is in Draft state
        if (can_approve && is_pending_approval) {
            // Add the custom 'Approve Sale' button to the page header
            frm.add_custom_button(__("Approve Sale"), () => {
                // When the button is clicked, show a confirmation dialog
                frappe.confirm(
                    __("Are you sure you want to approve this sale and close the linked lead? This action cannot be undone."),
                    () => {
                        // If the user confirms, freeze the UI to prevent further actions
                        frappe.dom.freeze(__("Approving..."));

                        // Call the server-side Python function
                        frappe.call({
                            method: "joel_living.joel_living.doctype.sales_completion_form.sales_completion_form.approve_and_close_lead",
                            args: {
                                form_name: frm.doc.name, // Pass the name of this form
                                lead_name: frm.doc.lead_id    // Pass the name of the linked lead
                            },
                            callback: function(r) {
                                // When the server responds, unfreeze the UI
                                frappe.dom.unfreeze();
                                
                                if (r.message) {
                                    // Show a success message from the server
                                    frappe.show_alert({
                                        message: __(r.message),
                                        indicator: 'green'
                                    });
                                    
                                    // Refresh the form to show its new status (Submitted)
                                    frm.refresh();
                                }
                            }
                        });
                    }
                );
            }).addClass("btn-primary"); // Make the button visually prominent
        }
    },
});