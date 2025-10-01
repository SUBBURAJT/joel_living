frappe.listview_settings['Lead Import Request'] = {
    onload: function(listview) {
        listview.page.add_inner_button(
            __('Sample Import Excel File'),
            function() {
                window.open('/private/files/sample_import_lead.xlsx');
            }
        )
        .css({
            "background-color": "#000000ff",  
            "color": "white",               
            "font-weight": "bold",         
            "border-radius": "6px",        
            "padding": "6px 12px"        
        });
    }
};
