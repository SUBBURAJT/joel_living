// Copyright (c) 2025, Subburaj and contributors
// For license information, please see license.txt

frappe.ui.form.on('Admin Message Inbox', {
    onload: function (frm) {
        // ✅ Hide the Save button permanently
        frm.disable_save();

        // ✅ Automatically mark as seen when user opens the message
        if (frm.doc.status === "Not Seen") {
            frappe.db.set_value('Admin Message Inbox', frm.doc.name, 'status', 'Seen')
                .then(() => {
                    // Silent update — no alerts or reload needed
                    frm.refresh_field('status');
                });
        }
    },

    refresh: function (frm) {
        // ✅ Also hide Save on every refresh (ensures it never reappears)
        frm.disable_save();
    }
})