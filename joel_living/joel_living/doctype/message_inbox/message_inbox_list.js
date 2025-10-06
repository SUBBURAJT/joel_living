
frappe.listview_settings['Message Inbox'] = {
    onload: function(listview) {
        listview.wrapper.on('click', '.list-row', function() {
            let row = $(this);
            let docname = row.attr('data-name');

            frappe.db.get_doc('Message Inbox', docname).then(doc => {
                let d = new frappe.ui.Dialog({
                    title: doc.title,
                    fields: [
                        { fieldname: 'content', label: 'Message', fieldtype: 'HTML', options: doc.content }
                    ],
                    primary_action_label: 'Close',
                    primary_action(values) { d.hide(); }
                });
                d.show();

                // Optional: mark as read
                frappe.db.set_value('Message Inbox', docname, 'read', 1);
            });

            return false; // prevent default opening
        });
    }
};