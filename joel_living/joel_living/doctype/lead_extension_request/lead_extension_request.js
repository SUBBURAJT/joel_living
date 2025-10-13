frappe.ui.form.on('Lead Extension Request', {
    refresh: function(frm) {
        
        // --- THIS IS THE FIX ---
        // This is the correct and most robust way to clear all previously added custom buttons.
        // It's safer than frm.remove_custom_button() because you don't need to know the button labels.
        frm.page.clear_custom_actions();
        // --- END OF FIX ---

        // Only show buttons if the document is saved and the status is 'Open'.
        if (frm.doc.status === 'Open' && !frm.is_new()) {

            // Asynchronously fetch the deadline from Admin Settings.
            frappe.db.get_single_value('Admin Settings', 're_approval_deadline_days').then(days => {
                
                const deadlineDays = days || 3; // Fallback to 3 if setting is not configured

                // 1. --- THE APPROVE BUTTON (with dynamic text and confirmation) ---
                const approveButtonLabel = __("Approve Re-assignment ({0} Days)", [deadlineDays]);
                const approveBtn = frm.add_custom_button(approveButtonLabel, function() {
                    frappe.confirm(
                        __('Are you sure you want to approve this re-assignment for {0} days?', [deadlineDays]),
                        () => {
                            frm.disable_save();
                            approveBtn.prop('disabled', true);
                            frappe.call({
                                method: 'joel_living.lead_permission.approve_lead_reassignment',
                                args: { request_name: frm.doc.name },
                                always: () => { frm.enable_save(); },
                                callback: (r) => {
                                    if (!r.exc) {
                                        frm.reload_doc();
                                    } else {
                                        approveBtn.prop('disabled', false);
                                    }
                                }
                            });
                        }
                    );
                }).addClass('btn-primary');


                // 2. --- THE REJECT BUTTON (with confirmation) ---
                const rejectBtn = frm.add_custom_button(__('Reject Request'), function() {
                    frappe.confirm(
                        __('Are you sure you want to reject this request? This action cannot be undone.'),
                        () => {
                            frappe.prompt({
                                fieldname: 'reason',
                                label: 'Reason for Rejection (Optional)',
                                fieldtype: 'Small Text'
                            }, (values) => {
                                frm.disable_save();
                                rejectBtn.prop('disabled', true);
                                frappe.call({
                                    method: 'joel_living.lead_permission.reject_lead_extension',
                                    args: {
                                        request_name: frm.doc.name,
                                        reason: values.reason
                                    },
                                    always: () => { frm.enable_save(); },
                                    callback: (r) => {
                                        if (!r.exc) {
                                            frm.reload_doc();
                                        } else {
                                            rejectBtn.prop('disabled', false);
                                        }
                                    }
                                });
                            });
                        }
                    );
                }).addClass('btn-danger');

            });
        }
    }
});