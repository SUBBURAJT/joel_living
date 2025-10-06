frappe.listview_settings['Lead Export Request'] = {
    add_fields: ["export_file", "status"], // 👈 ensures these fields are fetched for each row

    button: {
        show: function (doc) {
            // console.log("Export file URL:", doc.export_file, "Status:", doc.status);
            // Show the button only if Approved and file exists
            return doc.status === "Approved" && !!doc.export_file;
        },
        get_label: function () {
            return __("Download");
        },
        get_description: function (doc) {
            return __("Download export file for {0}", [doc.name]);
        },
        action: function (doc) {
            if (doc.export_file) {
                // console.log("Downloading file:", doc.export_file);
                const file_url = doc.export_file.startsWith('/')
                    ? doc.export_file
                    : '/' + doc.export_file;
                window.open(file_url, '_blank');
            } else {
                frappe.msgprint(__('No export file found for this record.'));
            }
        },
    },
};
