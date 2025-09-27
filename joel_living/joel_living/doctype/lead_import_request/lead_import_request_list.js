frappe.listview_settings['Lead Import Request'] = {
    onload: function(listview) {
        listview.page.add_inner_button(
            __('Download Lead Template'),
            function() {
                window.open('/files/Lead Template.xlsx');
            }
        )
        .css({
            "background-color": "#4CAF50",  
            "color": "white",               
            "font-weight": "bold",         
            "border-radius": "6px",        
            "padding": "6px 12px"        
        });
    }
};
