// Copyright (c) 2025, Subburaj and contributors
// For license information, please see license.txt

frappe.ui.form.on("System Message", {
	refresh: function(frm) {
        frm.trigger("toggle_fields");
    },

    send_to_all_users: function(frm) {
        frm.trigger("toggle_fields");
    },

    recipients: function(frm) {
        frm.trigger("toggle_fields");
    },

    recipients: function(frm) {
        frm.trigger("toggle_fields");
    },

    toggle_fields: function(frm) {
        // Check if any recipient row has a user selected
        const hasRecipients = frm.doc.recipients && 
                             frm.doc.recipients.length > 0 && 
                             frm.doc.recipients.some(row => row.user);
        
        if (frm.doc.send_to_all_users) {
            // If "Send to All Users" checked → lock recipients table
            frm.set_df_property("recipients", "read_only", 1);
            frm.set_df_property("send_to_all_users", "read_only", 0);
        } 
        else if (hasRecipients) {
            // If at least one recipient with a user selected → lock the checkbox
            frm.set_df_property("send_to_all_users", "read_only", 1);
            frm.set_df_property("recipients", "read_only", 0);
        } 
        else {
            // Reset → both editable
            frm.set_df_property("send_to_all_users", "read_only", 0);
            frm.set_df_property("recipients", "read_only", 0);
        }

        frm.refresh_field("recipients");
        frm.refresh_field("send_to_all_users");
    }
});
