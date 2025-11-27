// // Copyright (c) 2025, Subburaj and contributors
// // For license information, please see license.txt

// frappe.ui.form.on("Admin Message", {
//     onload(frm) {
//         control_form_state(frm);
//         toggle_fields(frm);
//     },

//     refresh(frm) {
//         control_form_state(frm);
//         toggle_fields(frm);
//     },

//     send_to_all_users(frm) {
//         toggle_fields(frm);
//     },

//     recipients_on_form_rendered(frm) {
//         toggle_fields(frm);
//     },

//     recipients_add(frm) {
//         setTimeout(() => toggle_fields(frm), 200);
//     },

//     recipients_remove(frm) {
//         setTimeout(() => toggle_fields(frm), 200);
//     },

//     validate(frm) {
//         if (frm.confirmed_send) return;

//         let msg = "";
//         if (frm.doc.send_to_all_users) {
//             msg = "Are you sure you want to send this message to ALL users?";
//         } else if (frm.doc.recipients && frm.doc.recipients.length > 0) {
//             msg = "Are you sure you want to send this message to selected user(s)?";
//         }

//         if (!msg) {
//             frappe.msgprint("No recipients selected.");
//             frappe.validated = false;
//             return;
//         }

//         frappe.validated = false;

//         frappe.confirm(
//             msg,
//             function () {
//                 frm.confirmed_send = true;
//                 frm.set_value("sent_date", frappe.datetime.now_datetime());
//                 frm.save().then(() => {
//                     frappe.set_route("List", "Admin Message");
//                 });
//             },
//             function () {
//                 frappe.msgprint("Message sending cancelled.");
//             }
//         );
//     },
// });

// // --- CONTROL FORM STATE FOR SENT MESSAGES ---
// function control_form_state(frm) {
//     setTimeout(() => {
//         const isNewDocument = frm.doc.__islocal;

//         if (!isNewDocument && frm.doc.status === "Sent") {
//             frm.set_read_only();
//             frm.disable_save();
//             if (frm.page.btn_primary) frm.page.btn_primary.hide();
//             if (frm.page.set_primary_action) frm.page.set_primary_action(null);
//             frm.page.clear_secondary_action();
//         } else {
//             if (frm.page.btn_primary) frm.page.btn_primary.show();
//             frm.dashboard.clear_headline();
//         }
//     }, 300);
// }

// // --- TOGGLE FIELDS BASED ON SELECTION ---
// function toggle_fields(frm) {
//     if (frm.doc.send_to_all_users) {
//         // ✅ Hide recipients when "Send to All Users" checked
//         frm.set_df_property("recipients", "hidden", 1);
//         frm.set_df_property("send_to_all_users", "read_only", 0);

//         // 🧹 Clear recipients if switching to "Send to All Users"
//         if (frm.doc.recipients && frm.doc.recipients.length > 0) {
//             frm.clear_table("recipients");
//             frm.refresh_field("recipients");
//         }

//     } else {
//         // ✅ Show recipients if not sending to all
//         frm.set_df_property("recipients", "hidden", 0);

//         if (frm.doc.recipients && frm.doc.recipients.length > 0) {
//             frm.set_df_property("send_to_all_users", "read_only", 1);
//         } else {
//             frm.set_df_property("send_to_all_users", "read_only", 0);
//         }
//     }

//     // 🔁 Force refresh to apply visibility changes to child table
//     frm.refresh_field("recipients");
// }




frappe.ui.form.on("Admin Message", {
    onload(frm) {
        // 🔥 Reset confirmation flag for NEW documents
        if (frm.is_new()) {
            frm.confirmed_send = false;
        }
 
        control_form_state(frm);
        toggle_fields(frm);
    },
 
    refresh(frm) {
        control_form_state(frm);
        toggle_fields(frm);
    },
 
    send_to_all_users(frm) {
        toggle_fields(frm);
    },
 
    recipients_on_form_rendered(frm) {
        toggle_fields(frm);
    },
 
    recipients_add(frm) {
        setTimeout(() => toggle_fields(frm), 200);
    },
 
    recipients_remove(frm) {
        setTimeout(() => toggle_fields(frm), 200);
    },
 
    validate(frm) {
        if (frm.confirmed_send) return;
 
        let error_messages = [];
 
        // Recipients required if NOT send-to-all
        if (!frm.doc.send_to_all_users &&
            (!frm.doc.recipients || frm.doc.recipients.length === 0)) {
            error_messages.push("- Please select at least one Recipient.");
        }
 
        if (!frm.doc.subject || frm.doc.subject.trim() === "") {
            error_messages.push("- Subject is required.");
        }
 
        if (!frm.doc.message || frm.doc.message.trim() === "") {
            error_messages.push("- Message is required.");
        }
 
        if (error_messages.length > 0) {
            frappe.msgprint({
                title: __('Validation Error'),
                indicator: 'red',
                message: error_messages.join('<br>')
            });
            frappe.validated = false;
            return;
        }
 
        // Confirmation dialog
        let msg = frm.doc.send_to_all_users
            ? "Are you sure you want to send this message to ALL users?"
            : "Are you sure you want to send this message to selected user(s)?";
 
        frappe.validated = false;
 
        frappe.confirm(
            msg,
            function () {
                frm.confirmed_send = true;
                frm.set_value("sent_date", frappe.datetime.now_datetime());
 
                frm.save().then(() => {
 
                    // -----------------------------
                    // LOCK THE FORM BEFORE ROUTING
                    // -----------------------------
                    frm.set_value("status", "Sent");
                    frm.set_read_only();
                    frm.disable_save();
 
                    if (frm.page.btn_primary) frm.page.btn_primary.hide();
                    if (frm.page.set_primary_action) frm.page.set_primary_action(null);
                    frm.page.clear_secondary_action();
 
                    // Redirect
                    frappe.set_route("List", "Admin Message");
                });
            },
            function () {
                frappe.msgprint("Message sending cancelled.");
            }
        );
    },
});
 
// ------------------------------
// CONTROL READ-ONLY FOR SENT DOC
// ------------------------------
function control_form_state(frm) {
    setTimeout(() => {
        if (!frm.is_new() && frm.doc.status === "Sent") {
 
            frm.set_read_only();
            frm.disable_save();
 
            if (frm.page.btn_primary) frm.page.btn_primary.hide();
            if (frm.page.set_primary_action) frm.page.set_primary_action(null);
            frm.page.clear_secondary_action();
 
        } else {
            if (frm.page.btn_primary) frm.page.btn_primary.show();
            frm.dashboard.clear_headline();
        }
    }, 300);
}
 
// ------------------------------
// TOGGLE RECIPIENT FIELD
// ------------------------------
function toggle_fields(frm) {
    const is_all = frm.doc.send_to_all_users;
    const has_recipients = frm.doc.recipients && frm.doc.recipients.length > 0;
 
    // Required asterisk control
    frm.set_df_property("recipients", "reqd", is_all ? 0 : 1);
 
    if (is_all) {
        frm.set_df_property("recipients", "hidden", 1);
        frm.set_df_property("send_to_all_users", "read_only", 0);
 
        if (has_recipients) {
            frm.clear_table("recipients");
            frm.refresh_field("recipients");
        }
 
    } else {
        frm.set_df_property("recipients", "hidden", 0);
 
        if (has_recipients) {
            frm.set_df_property("send_to_all_users", "read_only", 1);
        } else {
            frm.set_df_property("send_to_all_users", "read_only", 0);
        }
    }
 
    frm.refresh_field("recipients");
}
 