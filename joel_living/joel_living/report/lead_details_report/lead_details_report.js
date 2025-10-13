frappe.query_reports["Lead Details Report"] = {
    "filters": [
        { "fieldname": "lead_owner", "label": __("Lead Owner"), "fieldtype": "Link", "options": "User" },
        { "fieldname": "custom_lead_category", "label": __("Lead Category"), "fieldtype": "Data", "hidden": 1 },
        { "fieldname": "show_unassigned", "label": __("Show Only Unassigned Leads"), "fieldtype": "Check", "default": 0 },
    ],
    // The fieldname in python is 'select', the column fieldname in the grid is also 'select'.
    "formatter": function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        
        // Ensure the state map is INITIALIZED SAFELY and GLOBALLY accessible 
        const report_def = frappe.query_reports["Lead Details Report"];
        if (!report_def.selected_lead_map) {
             report_def.selected_lead_map = {};
        }

        // IMPORTANT: The row-level checkbox must only render on the column with fieldname 'select' (per your Python code).
        if (column.fieldname === 'select' && data && data.name) { 
            const is_checked = report_def.selected_lead_map[data.name] ? "checked" : "";
            
            return `<div class="text-center"><input type="checkbox" class="report-row-checkbox" data-name="${data.name}" ${is_checked}></div>`;
        }
        return value;
    },
    "onload": function(report) {
        
        // 1. Assign the global map reference to the instance's 'report' object
        report.selected_lead_map = frappe.query_reports["Lead Details Report"].selected_lead_map; 

        // --- 2. Highly Robust Helper Functions (Safe against uninitialized map) ---
        report.get_selected_data = () => {
            const lead_map = report.selected_lead_map || {}; 
            const names = Object.keys(lead_map);
            return report.data.filter(row => lead_map[row.name]);
        };
        
        report.get_selected_names = () => {
            const lead_map = report.selected_lead_map || {}; 
            return Object.keys(lead_map);
        };


        // --- MASTER SELECT ALL/DESELECT FUNCTION ---
        const toggle_all_checkboxes = (is_checked) => {
            if (is_checked) {
                // Select all leads currently visible in the data
                report.data.forEach(row => {
                    if (row.name) {
                        report.selected_lead_map[row.name] = true;
                    }
                });
            } else {
                // Clear the map entirely
                report.selected_lead_map = {};
            }
            report.refresh(); 
        };

        // --- 3. Global Export Function (for inline onclick fix on Export button) ---
        if (typeof window.handle_report_export !== 'function') {
            window.handle_report_export = () => {
                const selected_data = report.get_selected_data();
                if (!selected_data.length) { frappe.msgprint(__('Please select at least one Lead.')); return; }
        
                const data_to_export = selected_data.map(row => {
                    let export_row = {};
                    report.columns.slice(1).forEach(col => {
                        export_row[col.label] = row[col.fieldname]; 
                    });
                    return export_row;
                });
                
                frappe.ui.export.download_csv(data_to_export, 'Lead', 'Selected_Leads_Report');
                frappe.msgprint({ message: __('Export file generated successfully.'), indicator: 'green', title: __('Success') });
            };
        }


        // --- 4. Persistent Event Handler Attacher for ALL elements ---
        const attach_event_handlers = () => {
            const report_wrapper = $(report.wrapper);
            const buttons_container = report_wrapper.find('#report-custom-buttons');
            const tabs_container = report_wrapper.find('.report-tabs-container');

            if (buttons_container.length === 0) { 
                setTimeout(attach_event_handlers, 200); 
                return; 
            }
            
            const get_selected_data = report.get_selected_data;
            const get_selected_names = report.get_selected_names;


            // === CRITICAL FIX: CHECKBOX HANDLERS ===
            
            // 4a. MASTER CHECKBOX HANDLER (Uses the dedicated Master Checkbox element ID)
            report_wrapper.find('#report-select-all-checkbox')
                .off('change.master_checkbox') 
                .on('change.master_checkbox', function() {
                    console.log(`[MASTER DEBUG] Master Checkbox clicked. New state: ${this.checked}`);
                    toggle_all_checkboxes(this.checked);
                });

            // 4b. SINGLE ROW CHECKBOX HANDLER (Manual State Tracking and Master Checkbox sync)
            report_wrapper.find('.frappe-list-table')
                .off('change.custom_checkbox_tracker', '.report-row-checkbox') 
                .on('change.custom_checkbox_tracker', '.report-row-checkbox', function() {
                    const checkbox = $(this);
                    const lead_name = checkbox.data('name');
                    
                    if (!lead_name) {
                        console.error("[CHECKBOX FATAL] Checkbox is missing the data-name attribute!", checkbox[0]);
                        return;
                    }
                    
                    if (this.checked) {
                        report.selected_lead_map[lead_name] = true;
                    } else {
                        delete report.selected_lead_map[lead_name];
                    }
                    
                    // Logic to sync the Master checkbox state
                    const total_rows = report.data.length;
                    const selected_count = Object.keys(report.selected_lead_map).length;
                    
                    const master_checkbox = report_wrapper.find('#report-select-all-checkbox');
                    master_checkbox.prop('checked', selected_count > 0 && selected_count === total_rows);
                    master_checkbox.prop('indeterminate', selected_count > 0 && selected_count < total_rows);
                });
            // ==========================================================

            
            // --- UI Setup (Owner Filter) ---
            const user_roles = frappe.session.user_roles;
            const is_unrestricted = user_roles.some(r => ["System Manager", "Administrator", "Sales Manager"].includes(r));
            if (!is_unrestricted) {
                const leadOwnerFilter = report.get_filter('lead_owner');
                if (leadOwnerFilter) {
                    leadOwnerFilter.set_value(frappe.session.user);
                    leadOwnerFilter.df.read_only = 1;
                    leadOwnerFilter.refresh();
                }
            }

            // --- Unbind and re-bind Delegation (Standard procedure) ---
            buttons_container.off('click', '#report-btn-request-hide, #report-btn-assign-lead, #report-btn-approve-hide, #report-btn-reject-hide');
            tabs_container.off('click', '.custom-report-tab'); 

            // Filter Tabs - Event Delegation
            tabs_container.on('click', '.custom-report-tab', function(e) {
                e.preventDefault();
                const category = $(this).data('value');
                tabs_container.find('.custom-report-tab').removeClass('active');
                $(this).addClass('active');
                report.set_filter_value("custom_lead_category", category === "All" ? "" : category);
                // Clear state map on filter change
                report.selected_lead_map = {}; 
                report.refresh();
            });
            
            // Set active tab based on current filter value
            const current_category_filter = report.get_filter_value("custom_lead_category");
            let active_tab_value = current_category_filter || "All"; 
            tabs_container.find('.custom-report-tab').removeClass('active');
            tabs_container.find(`.custom-report-tab[data-value="${active_tab_value}"]`).addClass('active');

            // --- Action Buttons Event Handlers (Unchanged logic) ---

            // Request Hide Button
            buttons_container.on('click', '#report-btn-request-hide', () => {
                const selected = get_selected_data();
                if (!selected.length) { frappe.msgprint(__('Please select at least one Lead.')); return; }
                
                let valid_leads = selected.filter(r => r.custom_hide_status === 'No Request' || r.custom_hide_status === 'Rejected');
                let pending_leads = selected.filter(r => r.custom_hide_status === 'Pending');

                if (pending_leads.length) frappe.msgprint(__('Already sent for approval: ' + pending_leads.map(r => r.name).join(', ')));
                
                if (valid_leads.length > 0) {
                    frappe.confirm(__('Are you sure you want to request hide for these {0} leads?', [valid_leads.length]), () => {
                        frappe.call({
                            method: 'lead_custom_app.api.unassigned_lead.request_hide_bulk', 
                            args: { leads: valid_leads.map(l => l.name) },
                            callback: () => {
                                frappe.show_alert({ message: __('Hide requests submitted successfully.'), indicator: 'green'});
                                report.selected_lead_map = {};
                                report.refresh();
                            }
                        });
                    });
                }
            });

            // Assign Lead Button
            buttons_container.on('click', '#report-btn-assign-lead', () => {
                const names = get_selected_names();
                if (!names.length) { frappe.msgprint(__('Please select at least one Lead.')); return; }
                
                frappe.prompt(
                    [{ fieldname: 'lead_owner', fieldtype: 'Link', label: __('Select Lead Owner'), options: 'User', reqd: 1 }],
                    (values) => frappe.call({
                        method: "joel_living.custom_lead.assign_leads_to_user", 
                        args: { leads: names, lead_owner: values.lead_owner },
                        callback: (r) => { 
                            if (!r.exc) { 
                                frappe.msgprint(__('Leads assigned successfully'));
                                report.selected_lead_map = {};
                                report.refresh(); 
                            }
                        }
                    }),
                    __('Assign Lead'), 
                    __('Assign')
                );
            });

            const update_hide_status = (status, method, message, indicator) => {
                const selected = get_selected_data().filter(r => r.custom_hide_status === 'Pending');
                if (!selected.length) { frappe.msgprint(__("Please select leads with 'Pending' hide status.")); return; }
                
                const lead_names = selected.map(lead => lead.name);

                frappe.call({ 
                    method: method,
                    args: { leads: lead_names },
                    callback: () => {
                        frappe.show_alert({ message: message, indicator: indicator });
                        report.selected_lead_map = {};
                        report.refresh();
                    }
                });
            };

            // Approve Hide Button
            buttons_container.on('click', '#report-btn-approve-hide', () => {
                update_hide_status('Pending', 'lead_custom_app.api.unassigned_lead.approve_hide_bulk', __('Selected leads approved for hiding.'), 'green');
            });
            
            // Reject Hide Button
            buttons_container.on('click', '#report-btn-reject-hide', () => {
                update_hide_status('Pending', 'lead_custom_app.api.unassigned_lead.reject_hide_bulk', __('Selected requests have been rejected.'), 'orange');
            });
        };
        
        attach_event_handlers();
    }
};