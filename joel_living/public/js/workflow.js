class WorkflowOverride extends frappe.ui.form.States {
    show_actions() {
        // console.log("WorkflowOverride: show_actions() executed"); // Add log
        let added = false;
        const me = this;

        if (this.frm.doc.__unsaved === 1) {
            // console.log("Document is unsaved, skipping workflow actions.");
            return;
        }

        frappe.workflow.get_transitions(this.frm.doc).then((transitions) => {
            // console.log("Available transitions:", transitions);
            this.frm.page.clear_actions_menu();
            transitions.forEach((d) => {
                // console.log("Checking transition:", d.action);
                if (!frappe.user_roles.includes(d.allowed)) {
                    return;
                }

                if (
                    me.frm.doc.doctype === "Lead" &&
                    frappe.user.has_role("Sales Agent") &&
                    !me.frm.doc.lead_owner
                ) {
                    return;
                }
                    // console.log("User has access to transition:", d.action);
                    added = true;
                    me.frm.page.add_action_item(__(d.action), function () {
                        // console.log("Workflow action triggered:", d.action);
                        if (me.frm.doc.doctype === "Lead") {
                            frappe.confirm(
                                __(`Are you sure you want to proceed with ${d.action}?`),
                                () => {
                                    // console.log("User confirmed:", d.action);
                                    
                                 



                                    if (d.action === "Sales Completed") {
                                        // This is the new validation check
                                        frappe.call({
                                            method: "joel_living.custom_lead.check_for_existing_sales_form", // Dot path to your python function
                                            args: {
                                                lead_name: me.frm.doc.name
                                            },
                                            callback: function(r) {
                                                if (r.message) {
                                                    // A form already exists. Show a message with a link.
                                                    frappe.msgprint({
                                                        title: __('Form Already Exists'),
                                                        indicator: 'info',
                                                        // message: __("A Sales Registration Form already exists for this lead and is pending approval.", [`<a href="/app/sales-registration-form/${r.message}" target="_blank">${r.message}</a>`])
                                                        message: __("A Sales Registration Form already exists for this lead and is pending approval.")
                                                    });
                                                } else {
                                                    // No form exists, so proceed with showing the dialog.
                                                    me.show_sales_completion_dialog();
                                                }
                                            }
                                        });
                                    } 
                                    else if (d.action === "Lead Lost") {

                                        frappe.prompt(
                                            [
                                                {
                                                    fieldname: "lost_reason",
                                                    label: "Lead Lost Reason",
                                                    fieldtype: "Small Text",
                                                    reqd: 1
                                                }
                                            ],
                                            (data) => {
                                                me.frm.set_value("custom_lead_lost_reason", data.lost_reason);
                                                me.frm.set_value("custom_lead_lost_date", frappe.datetime.get_today());
                                                me.frm.save().then(() => {
                                                    me.apply_workflow_action(d);
                                                });
                                            },
                                            __("Provide Lead Lost Reason"),
                                            __("Submit")
                                        );

                                    } 
                                    
                                    else {
                                        me.apply_workflow_action(d);
                                    }
                                },
                                () => {
                                    // console.log("Workflow action cancelled by the user.");
                                }
                            );
                        } 
                       
                        
                        
                        else {
                            me.apply_workflow_action(d);
                        }
                    });
                
            });

            this.setup_btn(added);
        });
    }



// show_sales_completion_dialog() {
//     const me = this;
//     const lead = me.frm.doc;
//     let controls = {}; 
//      let receipts_data = [];

//     // --- DRAFT MANAGEMENT ---
//     const DRAFT_KEY = `sales_reg_draft_${frappe.session.user}_${lead.name}`;
    
//     // START OF FIX: REVISED save_draft function (ensures '0', 'null', '' states for critical fields are saved)
//     // const save_draft = () => {
//     //     const values = {};
//     //     for (let key in controls) {
//     //         if (controls[key] && controls[key].get_value) {
//     //             let val = controls[key].get_value();
//     //             const control = controls[key];
//     //             if (control.df.fieldtype === 'Table') {
//     //                 // A table's value is an array of rows. Save it if there are any rows.
//     //                 if (Array.isArray(val) && val.length > 0) {
//     //                     values[key] = val;
//     //                 }
//     //                 // Use 'continue' to skip the generic handling below for this field.
//     //                 continue;
//     //             }
//     //             // Keys that represent a global UI state which must save an empty/zero state.
//     //             // extra_joint_owners (select), unit_floor (select options populated by project), screened_before_payment (select)
//     //             const is_ui_state_key = key === 'extra_joint_owners' || key === 'unit_floor' || key === 'screened_before_payment'; 
                
//     //             // Keys that are for Joint Owner data - must be saved if they exist in `controls`.
//     //             const is_joint_owner_key = key.startsWith('jo') && key.split('_').length > 1;

//     //             // Step 1: Normalize val: get_value() can return null or undefined for unset Selects. Convert to "" for saving consistency.
//     //             if (val === null || val === undefined) {
//     //                  val = '';
//     //             }

//     //             // Step 2: Check for value existence - Save if meaningful OR it is a mandatory state/JO field.
//     //             const is_meaningful = (val !== '' && (String(val).length > 0) || (Array.isArray(val) && val.length > 0));

//     //             // Save if a meaningful value exists OR the key is a dynamic state/joint owner field.
//     //             if (is_meaningful || is_ui_state_key || is_joint_owner_key)
//     //             { 
//     //                  // Since we converted null/undefined to '', we can just save 'val' directly.
//     //                  // It will save '0' or '1' (if selected), or '' (if empty).
//     //                  values[key] = val; 
//     //             }
//     //         }
//     //     }
//     //     console.log(values);
//     //     if (Object.keys(values).length > 0) {
//     //         localStorage.setItem(DRAFT_KEY, JSON.stringify(values));
//     //     }
//     // };
//     const get_receipt_values = () => {
//         const collected_data = [];
//         // Only collect from rows that are part of the table body (ignore header, buttons)
//         const $rows = wrapper.find('#receipts_table_placeholder table tbody tr').not('.no-data-row'); 

//         $rows.each(function() {
//             const $row = $(this);
//             // We use .get_value() here to leverage the frappe number and link control formatting 
//             // even though they're not frappe controls anymore - fall back to basic input value.
//             const date_val = $row.find('.receipts-date').val();
//             const amount_val = $row.find('.receipts-amount').val();
//             const proof_val = $row.find('.receipts-proof').val(); 
            
//             // Only collect the row if at least one critical field has a value
//             if (date_val || amount_val || proof_val) {
//                  collected_data.push({
//                     receipt_date: date_val,
//                     receipt_amount: amount_val,
//                     receipt_proof: proof_val
//                  });
//             }
//         });

//         return collected_data;
//     };
//     const save_draft = () => {
//         const values = {};
//         for (let key in controls) {
//             const control = controls[key];
//             if (control && control.get_value) {
//                 if (key === 'receipts') continue;
//                 // --- SPECIAL HANDLING FOR TABLE FIELDS ---
//                 // if (control.df.fieldtype === 'Table') {
//                 //     const table_data = control.get_value();
//                 //     if (Array.isArray(table_data) && table_data.length > 0) {
//                 //         // Create a "clean" array with only the necessary data
//                 //         const clean_data = table_data.map(row => ({
//                 //             receipt_date: row.receipt_date,
//                 //             receipt_amount: row.receipt_amount,
//                 //             receipt_proof: row.receipt_proof
//                 //         }));
//                 //         values[key] = clean_data;
//                 //     }
//                 //     continue; // Crucial to skip the other logic
//                 // }
//                 // --- END OF TABLE HANDLING ---

//                 // Generic handling for all other field types
//                 let val = control.get_value();
//                 if (val === null || val === undefined) {
//                     val = '';
//                 }

//                 const is_meaningful = (String(val).length > 0) || (Array.isArray(val) && val.length > 0);
//                 const is_ui_state_key = key === 'extra_joint_owners' || key === 'unit_floor' || key === 'screened_before_payment';
//                 const is_joint_owner_key = key.startsWith('jo');

//                 if (is_meaningful || is_ui_state_key || is_joint_owner_key) {
//                     values[key] = val;
//                 }
//             }
//         }
//         // CRITICAL: Manually get and inject the custom table data.
//         const current_receipts_data = get_receipt_values();
//         if (current_receipts_data.length > 0) {
//             values.receipts = current_receipts_data;
//         }
//         // Only save to localStorage if there is data to save
//         if (Object.keys(values).length > 0) {
//             localStorage.setItem(DRAFT_KEY, JSON.stringify(values));
//         } else {
//             // If the form is empty, clear any old drafts
//             localStorage.removeItem(DRAFT_KEY);
//         }
//     };
//     // END OF REVISED save_draft function

  
//     const clear_draft = () => {
//         localStorage.removeItem(DRAFT_KEY);
//     };
 
    
//     const load_draft = () => {
//         const draft_data = localStorage.getItem(DRAFT_KEY);
//         let loaded = false;

//         if (draft_data) {
//             const values = JSON.parse(draft_data);
//             // Store receipts data from draft in a variable. It will be rendered later.
//            // CRITICAL: If receipts exist, populate the custom data array.
//             if (values.receipts && Array.isArray(values.receipts)) {
//                 receipts_data = values.receipts; // This is where the draft data is loaded into our global manager array.
//             }

//             // Primary Draft Load (delayed to allow controls to be created first)
//             setTimeout(() => {
//                 const is_project_in_draft = !!values.project;

//                 for (let key in values) {
//                     if (key === 'receipts' || !controls[key] || !controls[key].set_value) {
//                         continue;
//                     }

//                     const control = controls[key];
//                     const original_onchange = control.df.onchange;

//                     // Temporarily disable onchange for Link fields to prevent premature triggers
//                     if (key === 'project' || control.fieldtype === 'Link') {
//                         control.df.onchange = null;
//                     }

//                     let value_to_set = values[key];

//                     // --- FIX FOR link.js ERROR ---
//                     // For Link fields, aggressively ensure the value is a string to prevent errors.
//                     // An empty string is safe; null, undefined, or other types are not.
//                     if (control.fieldtype === 'Link') {
//                         value_to_set = String(values[key] || '');
//                     }

//                     // Set value and restore onchange handler
//                     control.set_value(value_to_set);
//                     if (original_onchange) {
//                         control.df.onchange = original_onchange;
//                     }
//                 }

//                 // Manually trigger onchange for dynamic sections after their values are set
//                 if (controls.extra_joint_owners && controls.extra_joint_owners.df.onchange) {
//                     controls.extra_joint_owners.df.onchange();
//                 }

//                 // If project was in draft, re-fetch floor details to populate the options
//                 if (is_project_in_draft && controls.unit_floor) {
//                      frappe.call({
//                         method: "joel_living.custom_lead.get_project_floor_details",
//                         args: { project_name: values.project },
//                         callback: function(r) {
//                             if (r.message && controls.unit_floor) {
//                                  // (Your existing floor fetching logic here...)
//                                  const details = r.message;
//                                  let numbered_floor_count = details.no_of_floors || 0;
//                                  const has_mezzanine = details.include_mezzanine_floor;
//                                  const has_ground_floor = details.include_ground_floor;

//                                  let floor_options = [];
//                                  if (has_ground_floor) { floor_options.push('G'); numbered_floor_count--; }
//                                  if (has_mezzanine) { floor_options.push('M'); numbered_floor_count--; }
//                                  if (numbered_floor_count < 0) { numbered_floor_count = 0; }
//                                  for (let i = 1; i <= numbered_floor_count; i++) { floor_options.push(String(i)); }

//                                  controls.unit_floor.df.options = floor_options;
//                                  controls.unit_floor.refresh();
//                                  if (values.unit_floor) controls.unit_floor.set_value(values.unit_floor);
//                             }
//                         }
//                      });
//                 }
//             }, 300);

//             // Secondary load for dynamically created Joint Owner fields
//             setTimeout(() => {
//                 for (let key in values) {
//                     if (key.startsWith('jo') && controls[key] && controls[key].set_value) {
//                         const value_to_set = String(values[key] || '');
//                         controls[key].set_value(value_to_set);
//                     }
//                 }
//                 if(controls.screened_before_payment) $(controls.screened_before_payment.input).trigger('change');
//             }, 400);

//             loaded = true;
//         } else {
//              // Logic for a new, clean dialog when no draft exists
//              setTimeout(() => {
//                 if (controls.first_name) controls.first_name.set_value(lead.first_name);
//                 if (controls.last_name) controls.last_name.set_value(lead.last_name || lead.lead_name);
//                 if (controls.email) controls.email.set_value(lead.email_id);
//                 if (controls.main_phone_number && !controls.main_phone_number.get_value()) {
//                     controls.main_phone_number.set_value('+971-');
//                 }
//                 if (controls.country_of_residence) controls.country_of_residence.set_value(lead.country);
//                 if (controls.extra_joint_owners) controls.extra_joint_owners.set_value('0');
//                 if (controls.screened_before_payment) controls.screened_before_payment.set_value('');
//                 render_dynamic_fields();
//             }, 300);
//         }
//         return loaded;
//     };






//     // const load_draft = () => {
//     //     const draft_data = localStorage.getItem(DRAFT_KEY);
//     //     console.log('draft_data', draft_data);
//     //     let loaded = false;
//     //     if (draft_data) {
//     //         const values = JSON.parse(draft_data);
            
//     //         // Primary Draft Load (300ms delay) - Sets static fields and triggers dynamic control creation.
//     //         setTimeout(() => {
//     //             const is_project_in_draft = !!values.project;

//     //             // FIX 1: Project/Link Fields Draft Load Bug - Temporarily disable onchange
//     //             for (let key in values) {
//     //                 if (controls[key] && controls[key].set_value) {
//     //                     const control = controls[key];
//     //                     const original_onchange = control.df.onchange;

//     //                     if (key === 'project' || control.fieldtype === 'Link') {
//     //                         control.df.onchange = null;
//     //                     }
                        
//     //                     let value_to_set = values[key];
//     //                     // Also include Phone field in standard text value normalization
//     //                     if (control.fieldtype === 'Select' || control.fieldtype === 'Data' || control.fieldtype === 'Link' || control.fieldtype === 'Phone') { 
//     //                          value_to_set = (values[key] === null || values[key] === undefined) ? '' : values[key];
//     //                     }
                        
//     //                     // FIX: Add small delay for phone fields as suggested, to help external libraries init
//     //                     if (control.fieldtype === 'Phone') {
//     //                         setTimeout(() => { control.set_value(value_to_set); }, 100);
//     //                     } else {
//     //                         control.set_value(value_to_set);
//     //                     }


//     //                     if (original_onchange) {
//     //                          control.df.onchange = original_onchange;
//     //                     }
//     //                 }
//     //             }
                
//     //             // --- FIX 2: FORCE RENDER JOINT OWNER SECTIONS ---
//     //             // Must be done AFTER setting the extra_joint_owners value (which happened in the loop above)
//     //             if (controls.extra_joint_owners && controls.extra_joint_owners.df.onchange) {
//     //                 // This calls render_dynamic_fields() to CREATE the joX_... controls
//     //                 controls.extra_joint_owners.df.onchange(); 
//     //             }
//     //             // ---------------------------------------------
                
                
//     //             // FIX 1 CONTINUED: Manually run floor fetch to re-establish unit_floor OPTIONS 
//     //             if (is_project_in_draft && controls.unit_floor) {
//     //                  frappe.call({
//     //                     method: "joel_living.custom_lead.get_project_floor_details", 
//     //                     args: { project_name: values.project },
//     //                     callback: function(r) {
//     //                         if (r.message && controls.unit_floor) {
//     //                              const details = r.message;
//     //                              let numbered_floor_count = details.no_of_floors || 0;
//     //                              const has_mezzanine = details.include_mezzanine_floor; 
//     //                              const has_ground_floor = details.include_ground_floor; 
                                 
//     //                              let floor_options = [];
//     //                              if (has_ground_floor) { floor_options.push('G'); numbered_floor_count--; }
//     //                              if (has_mezzanine) { floor_options.push('M'); numbered_floor_count--; }
//     //                              if (numbered_floor_count < 0) { numbered_floor_count = 0; }
//     //                              for (let i = 1; i <= numbered_floor_count; i++) { floor_options.push(String(i)); }

//     //                              controls.unit_floor.df.options = floor_options;
//     //                              controls.unit_floor.refresh();
//     //                              if (values.unit_floor) controls.unit_floor.set_value(values.unit_floor);
//     //                         }
//     //                     }
//     //                  });
//     //             }
                
//     //             // END FIX 1
//     //         }, 300); 

//     //         // START OF FIX: Rerun set_value for dynamic fields after a slight additional delay (400ms total)
//     //         setTimeout(() => {
//     //              for (let key in values) {
//     //                 // This populates the dynamic controls (joX_...) that were just rendered/created by the onchange call.
//     //                 if (key.startsWith('jo') && controls[key] && controls[key].set_value) {
//     //                      const value_to_set = (values[key] === null || values[key] === undefined) ? '' : values[key];
//     //                      controls[key].set_value(value_to_set);
//     //                 }
//     //             }
                
//     //             // Force screen select change for UI toggle (even if field was empty)
//     //             if(controls.screened_before_payment) $(controls.screened_before_payment.input).trigger('change');
                
//     //         }, 400); 
//     //         // END OF FIX
            
//     //         loaded = true;
//     //     } else {
//     //          // NEW/CLEAN: ONLY apply data from the original Lead if no draft exists
//     //          setTimeout(() => {
//     //             if (controls.first_name) controls.first_name.set_value(lead.first_name);
//     //             if (controls.last_name) controls.last_name.set_value(lead.last_name || lead.lead_name);
//     //             if (controls.email) controls.email.set_value(lead.email_id);
                
//     //             // IGNORE lead.mobile_no for Main Phone Control. Default is handled post-creation via setTimeout.
//     //             if (controls.main_phone_number && !controls.main_phone_number.get_value()) {
//     //                 controls.main_phone_number.set_value('+971-'); // Ensure the clean state gets the visual default
//     //             }
                
//     //             if (controls.country_of_residence) controls.country_of_residence.set_value(lead.country);
                
//     //             if (controls.extra_joint_owners) controls.extra_joint_owners.set_value('0');
//     //             if (controls.screened_before_payment) controls.screened_before_payment.set_value('');
                
//     //             render_dynamic_fields(); 
//     //         }, 300);

//     //     }

//     //     return loaded;
//     // };
    




//     const add_receipt_row = (draft_data = {}) => {
//         receipts_data.push({
//             receipt_date: draft_data.receipt_date || '',
//             receipt_amount: draft_data.receipt_amount || '',
//             receipt_proof: draft_data.receipt_proof || ''
//         });
//         render_receipt_rows(); // Re-render the HTML after adding new row
//     };
    
//     const handle_input_change = ($input, row_index) => {
//         const field_name = $input.data('fieldname');
//         // Update the central JavaScript array which acts as the data source
//         if (receipts_data[row_index]) {
//             receipts_data[row_index][field_name] = $input.val();
//         }
//     };
    
//     // Ensure this helper function is in your script's scope
// const getFileName = (url) => {
//     if (!url) return '';
//     return url.substring(url.lastIndexOf('/') + 1) || url;
// }

// // --- FINAL Corrected Core Custom Rendering Function with Link View ---
// const render_receipt_rows = () => {
//     const $placeholder = wrapper.find('#receipts_table_placeholder');
//     $placeholder.empty();

//     let table_html = `
//         <table class="table table-bordered frappe-list-sidebar custom-receipt-table" style="margin-top:15px; background: white;">
//             <thead>
//                 <tr>
//                     <th style="width: 25%">Date *</th>
//                     <th style="width: 25%">Amount (AED) *</th>
//                     <th style="width: 35%">Proof of Payment *</th>
//                     <th style="width: 15%">Actions</th>
//                 </tr>
//             </thead>
//             <tbody>`;

//     if (receipts_data.length === 0) {
//          table_html += `<tr class="no-data-row"><td colspan="4" class="text-muted text-center" style="font-style: italic;">No receipts added.</td></tr>`;
//     }

//     receipts_data.forEach((row, index) => {
//         const date_val = row.receipt_date || '';
//         const amount_val = row.receipt_amount || '';
//         const proof_val = row.receipt_proof || '';
        
//         const file_name_display = getFileName(proof_val);

//         // --- NEW: HTML for File/Link display ---
//         let file_display_html;
//         if (proof_val) {
//             // If proof_val exists, render a clickable hyperlink
//             // The file path stored is typically an internal Frappe path like /files/image.png
//             // We prepend '/' just in case to ensure it's treated as a root path, and set target=_blank
//             const full_file_url = proof_val.startsWith('/') ? proof_val : ('/' + proof_val);
            
//             file_display_html = `
//                 <div style="margin-bottom: 5px;">
//                     <a href="${full_file_url}" target="_blank" class="receipts-file-link">${file_name_display}</a>
//                 </div>
//             `;
//         } else {
//             // Otherwise, render a read-only empty label
//             file_display_html = `<input type="text" readonly class="form-control input-sm receipts-file-label" value="">`;
//         }


//         table_html += `
//             <tr data-index="${index}">
//                 <td><input type="date" class="form-control input-sm receipts-input receipts-date" data-fieldname="receipt_date" value="${date_val}" ></td>
//                 <td><input type="number" min="0" class="form-control input-sm receipts-input receipts-amount" data-fieldname="receipt_amount" value="${amount_val}"></td>
//                 <td>
//                     <div class="input-group">
//                          ${file_display_html}
//                          <span class="input-group-btn" style="position: absolute; right: 0; top: 0;">
//                             <button class="btn btn-sm btn-default add-file-btn" data-fieldname="receipt_proof" type="button" data-index="${index}">Attach</button>
//                          </span>
//                          <!-- Hidden field to hold the actual URL/path -->
//                          <input type="hidden" class="receipts-proof" data-fieldname="receipt_proof" value="${proof_val}">
//                     </div>
//                 </td>
//                 <td>
//                     <button class="btn btn-xs btn-danger delete-row-btn" data-index="${index}">Delete</button>
//                 </td>
//             </tr>
//         `;
//     });

//     table_html += `</tbody></table>
//                     <button class="btn btn-sm btn-default add-custom-row-btn">Add Row</button>`;

//     $placeholder.html(table_html);
    
//     // --- Re-attach All Event Handlers ---
//     $placeholder.find('.add-custom-row-btn').off('click').on('click', () => add_receipt_row());
    
//     $placeholder.find('.delete-row-btn').off('click').on('click', function() {
//         const index = parseInt($(this).data('index'));
//         receipts_data.splice(index, 1);
//         render_receipt_rows(); 
//     });
    
//     // Update central data array on change
//     $placeholder.find('.receipts-input').off('change.sync blur.sync').on('change.sync blur.sync', function() {
//         const $input = $(this);
//         const index = parseInt($input.closest('tr').data('index'));
//         handle_input_change($input, index);
//     });
    
//     // Logic for attach button
//     $placeholder.find('.add-file-btn').off('click').on('click', function() {
//         const $btn = $(this);
//         const index = parseInt($btn.data('index'));
//         frappe.prompt(
//             { label: __('Attach File'), fieldname: 'file_url', fieldtype: 'AttachImage'}, 
//             (values) => {
//                 const file_url = values.file_url;
//                 if (file_url) {
//                      const file_name_display = getFileName(file_url);
                     
//                      // 1. Update the hidden URL input
//                      $btn.closest('tr').find('.receipts-proof').val(file_url);
//                      // 2. Update the central data array
//                      receipts_data[index].receipt_proof = file_url;
//                      // 3. Re-render the table to show the new clickable link instantly
//                      render_receipt_rows(); 
//                 }
//             }, 
//             __('Attach Receipt Proof')
//         );
//     });
// };



//     // Function to set up the Data field to visually appear as a locked +971 phone number
//     const setup_uae_phone_data_control = (control) => {
//         const $input = $(control.input);
//         const prefix = '+971';
        
//         setTimeout(() => {
//             let $input_group = $input.parent().is('.input-group') ? $input.parent() : null;
            
//             if ($input.val() && $input.val().startsWith(prefix)) {
//                 $input.val($input.val().replace(prefix, ''));
//             } else if (!$input.val()) {
//                 $input.val(''); 
//             }
            
//             if (!$input_group) {
//                  $input.wrap('<div class="input-group" style="width: 100%;"></div>');
//                  $input_group = $input.parent();
//             }

//             const $addon = $(`<span class="input-group-addon" style="font-weight: bold; background-color: #f7f9fa;">${prefix}</span>`);
//             $input.before($addon);

//             control.get_value = () => {
//                 let value = $input.val().trim();
//                 if (value && value !== prefix && !value.startsWith(prefix)) {
//                     return prefix + value;
//                 } else if (value.startsWith(prefix)) {
//                     return value;
//                 }
//                 return '';
//             }
//         }, 50); 
//     }
    
//     // **********************************************
//     // * Custom Validation Functions
//     // **********************************************
//     // const validate_age = (date_string) => {
//     //     if (!date_string) return { passed: true, message: '' };
//     //     try {
//     //         const today = moment();
//     //         const birthDate = moment(date_string);
//     //         const age = today.diff(birthDate, 'years');
//     //         if (age >= 18) { return { passed: true, message: '' }; }
//     //         return { passed: false, message: 'Client must be 18 years or older.' };
//     //     } catch (e) {
//     //         return { passed: false, message: 'Invalid date format for Date of Birth.' };
//     //     }
//     // };
    
//     const validate_email = (value) => {
//         if (!value) return { passed: true, message: '' };
//         // Standard basic email regex
//         const email_regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/; 
//         if (!email_regex.test(value)) {
//             return { passed: false, message: 'Please enter a valid email address.' };
//         }
//         return { passed: true, message: '' };
//     };
//     // Validate Future Date
//     const validate_future_date = (date_string) => {
//         if (!date_string) return { passed: true, message: '' };
//         const now = moment().format('YYYY-MM-DD'); 
//         if (date_string > now) { return { passed: true, message: '' }; }
//         return { passed: false, message: 'Expiry Date must be a future date.' };
//     };
    
//     const validate_passport_chars = (value) => {
//         if (!value) return { passed: true, message: '' };
//         if (/[^a-zA-Z0-9]/.test(value)) {
//             return { passed: false, message: 'Passport Number cannot contain special characters.' };
//         }
//         return { passed: true, message: '' };
//     }
    
//     // Global validation handler for individual controls - LOCAL ERROR DISPLAY (IMPROVED BLUR/CHANGE HANDLER)
//     const attach_validation_onchange = (control, validation_func) => {
//         if (!control) return;
        
//         let $elements_to_check = [];
//         $elements_to_check.push($(control.input)); 
//         if (control.fieldtype === 'Link') { $elements_to_check.push($(control.wrapper).find('.btn-link')); } 
//         if (control.fieldtype === 'Attach') { $elements_to_check.push($(control.wrapper).find('.attach-button')); }
//         if (control.fieldtype === 'Select' || control.fieldtype === 'Phone') { $elements_to_check.push($(control.select) || $(control.input)); }

//         // Remove previous handlers to prevent double triggering
//         for (const $element of $elements_to_check) {
//             $element.off('blur.customvalidate change.customvalidate'); 
//         }

//         for (const $element of $elements_to_check) {
//             $element.on('blur.customvalidate change.customvalidate', (e) => { 
                
//                 const is_attach = control.fieldtype === 'Attach';
                
//                 const value = control.get_value();
                
//                 const result = validation_func(value);
//                 const $wrapper = $(control.wrapper);
//                 $wrapper.find('.local-error-message').remove(); 
                
//                 // Determine target element for red border
//                 const $target_border = is_attach ? $wrapper.find('.attach-button').closest('.input-with-feedback') : $(control.input).length ? $(control.input) : $wrapper.find('.control-input');
//                 $target_border.css('border-color', ''); 

//                 if (!result.passed) {
//                     $wrapper.append(`<p class="local-error-message" style="color: red; font-size: 11px; margin-top: 5px;">${result.message}</p>`);
//                     $target_border.css('border-color', 'red');
//                 } else {
//                      $wrapper.find('.control-label').css('color', 'inherit');
//                 }
//             });
//         }
//     }

//     // **********************************************
    
//     // ** CUSTOM CLOSE CONFIRMATION DIALOG FUNCTION ** 
//     const show_custom_close_confirmation = () => {
//         save_draft(); 
        
//         const close_dialog = new frappe.ui.Dialog({
//             title: __('Close Confirmation'),
//             size: 'small',
//             fields: [
//                 {
//                     fieldtype: 'HTML',
//                     options: `
//                         <div style="padding-bottom: 10px;">
//                             <h4>${__('Unsaved changes detected. What would you like to do?')}</h4>
//                         </div>
//                         <div style="margin-top: 20px; text-align: right; width: 100%;">
//                             <button id="discard-close-btn" class="btn btn-sm btn-default" style="margin-right: 10px;">
//                                 ${__('Discard Data & Close')}
//                             </button>
//                             <button id="save-close-btn" class="btn btn-sm btn-primary">
//                                 ${__('Save Draft & Close')}
//                             </button>
//                         </div>
//                     `
//                 }
//             ],
//             actions: [] 
//         });

//         close_dialog.$wrapper.on('click', '#save-close-btn', () => {
//             save_draft(); 
//             clearInterval(dialog.draft_saver); 
//             close_dialog.hide();
//             dialog.hide();
//         });

//         close_dialog.$wrapper.on('click', '#discard-close-btn', () => {
//             clear_draft(); 
//             clearInterval(dialog.draft_saver); 
//             close_dialog.hide();
//             dialog.hide();
//         });

//         if (close_dialog.modal_close) {
//              close_dialog.modal_close.off('click').on('click', () => { close_dialog.hide() });
//         } else {
//              close_dialog.$wrapper.find('.modal-header .close').off('click').on('click', () => { close_dialog.hide() }); 
//         }
        
//         close_dialog.show();
//     }
//     // **********************************************

//     const dialog = new frappe.ui.Dialog({
//         title: __("Create Sales Registration"),
//         size: 'large',
//         static: true, 
//     });
    
//     // FIX 1: INCREASE DIALOG WIDTH
//     dialog.get_full_width = true;
//     dialog.$wrapper.find('.modal-dialog').css({
//         'max-width': '90vw',
//         'width': '90vw'
//     });


//     const wrapper = $(dialog.body);
//     // REORGANIZED TABS HTML
//     wrapper.html(`
//         <div>
//             <ul class="nav nav-tabs" role="tablist">
//                 <li class="nav-item"><a class="nav-link active" data-target="#tab-client" href="#">1. Client Information</a></li>
//                 <li class="nav-item"><a class="nav-link" data-target="#tab-joint-owners" href="#">2. Joint Owners</a></li> 
//                 <li class="nav-item"><a class="nav-link" data-target="#tab-unit" href="#">3. Unit & Sale Details</a></li>
//                 <li class="nav-item"><a class="nav-link" data-target="#tab-screening" href="#">4. Screening & KYC</a></li>
//                 <li class="nav-item"><a class="nav-link" data-target="#tab-remarks" href="#">5. Remarks & Files</a></li>
//             </ul>
//             <div class="tab-content" style="padding-top: 15px;">
//                 <!-- 1. Client Information (Main Client only) - 3 COLUMNS -->
//                 <div class="tab-pane fade show active" id="tab-client" role="tabpanel">
//                     <h4>Main Client Details</h4><hr><div class="row"><div class="col-md-4" id="client-col-1"></div><div class="col-md-4" id="client-col-2"></div><div class="col-md-4" id="client-col-3"></div><div class="col-md-12" id="client-col-4"></div></div>
//                 </div>
//                 <!-- 2. Joint Owners (Dedicated Tab) -->
//                 <div class="tab-pane fade" id="tab-joint-owners" role="tabpanel"> 
//                     <h4>Joint Owners</h4><hr><div id="joint-owners-section"></div>
//                 </div>
//                 <!-- 3. Unit & Sale Details - NOW 3 COLUMNS -->
//                 <div class="tab-pane fade" id="tab-unit" role="tabpanel">
    
//     <!-- This row is for the 3 columns of controls -->
//     <div class="row">
//         <div class="col-md-4" id="unit-col-1"></div>
//         <div class="col-md-4" id="unit-col-2"></div>
//         <div class="col-md-4" id="unit-col-3"></div>
//     </div>
    
//     <!-- START OF FIX: Add new full-width placeholders below the row -->
//     <div id="receipts_section_placeholder"></div>
//     <div id="receipts_table_placeholder"></div>
//     <!-- END OF FIX -->

// </div>
                
//                 <!-- 4. Screening & KYC (includes Joint Owner KYC) -->
//                 <div class="tab-pane fade" id="tab-screening" role="tabpanel">
//                     <h4>Client Screening</h4><hr><div id="screening-section"></div>
//                     <div id="screening-yes-section" class="mt-3" style="display:none;"><div class="row"><div class="col-md-6"></div></div></div>
//                     <div id="screening-no-section" class="mt-3" style="display:none;"><div class="row"><div class="col-md-6"></div><div class="col-md-6"></div><div class="col-md-12"></div></div></div>
//                     <h4 class="mt-4">Main Client KYC Uploads</h4><hr>
//                     <div id="main-kyc-placeholder"></div>
//                     <h4 class="mt-4">Joint Owners KYC Uploads</h4><hr><div id="joint-owners-kyc-placeholder"></div>
//                 </div>
//                 <!-- 5. Remarks & Files -->
//                 <div class="tab-pane fade" id="tab-remarks" role="tabpanel"><h4>Remarks (Optional)</h4><hr><div id="remarks-section"></div><h4 class="mt-4">Additional Files (Optional)</h4><hr><div id="files-section" class="row"><div class="col-md-6"></div><div class="col-md-6"></div></div></div>
//             </div>
//         </div>
//     `);
    
//     const make_control = (df, parent_id) => {
//         const parent_element = wrapper.find(`#${parent_id}`);
//         if (!parent_element.length) return;
//         const control = frappe.ui.form.make_control({ df, parent: parent_element, render_input: true });
//         controls[df.fieldname] = control;
//         return control;
//     };
    
//     // **********************************************
//     // * Main Client Field Creation
//     // **********************************************
//     // Client Col 1
//     make_control({ fieldname: 'form_type', label: 'Type of Register', fieldtype: 'Select', reqd: 1, options: ['Expression of Interest (EOI)', 'Completed Sale'] }, 'client-col-1');
//     make_control({ fieldname: 'first_name', label: 'First Name', fieldtype: 'Data', reqd: 1 }, 'client-col-1');
//     make_control({ fieldname: 'last_name', label: 'Last Name', fieldtype: 'Data', reqd: 1 }, 'client-col-1');
//     const main_email_control = make_control({ fieldname: 'email', label: 'Email', fieldtype: 'Data', options: 'Email', reqd: 1 }, 'client-col-1');
//     attach_validation_onchange(main_email_control, validate_email);
//     make_control({ fieldname: 'date_of_birth', label: 'Date of Birth', fieldtype: 'Date', reqd: 1 }, 'client-col-1');
//     // attach_validation_onchange(dob_control, validate_age); 

//     // Client Col 2
//     const main_phone_control = make_control({ 
//         fieldname: 'main_phone_number', 
//         label: 'Main Phone Number', 
//         fieldtype: 'Phone', 
//         reqd: 1, 
//         options: { 
//             onlyCountries: ['ae'],
//             initialCountry: 'ae',
//             separateDialCode: true 
//         } 
//     }, 'client-col-2'); 
    
//     // *** FIX: FORCE +971- VALUE IMMEDIATELY AFTER CREATION FOR VISUAL DEFAULT ***
//     setTimeout(() => {
//         if (main_phone_control && !main_phone_control.get_value()) {
//             main_phone_control.set_value('+971-');
//         }
//     }, 100);
//     // --------------------------------------------------------------------------

//     const uae_phone_control = make_control({ fieldname: 'uae_phone_number', label: 'UAE Phone Number', fieldtype: 'Data', description: 'Fixed to +971 for UAE' }, 'client-col-2'); 
//     setup_uae_phone_data_control(uae_phone_control); 
    
//     const passport_num_control = make_control({ fieldname: 'passport_number', label: 'Passport Number', fieldtype: 'Data', reqd: 1 }, 'client-col-2'); 
//     attach_validation_onchange(passport_num_control, validate_passport_chars); 
    
//     const passport_expiry_control = make_control({ fieldname: 'passport_expiry_date', label: 'Passport Expiry Date', fieldtype: 'Date', reqd: 1 }, 'client-col-2');
//     attach_validation_onchange(passport_expiry_control, validate_future_date); 
    
//     make_control({ fieldname: 'passport_copy', label: 'Passport Copy (PDF/JPG/PNG)', fieldtype: 'Attach', reqd: 1, options: { accepted_file_types: ['.pdf', '.jpg', '.jpeg', '.png'], show_preview: true } }, 'client-col-2');
    
//     // Client Col 3
//     const country_origin_control = make_control({ fieldname: 'country_of_origin', label: 'Country of Origin', fieldtype: 'Link', options: 'Country', reqd: 1 }, 'client-col-3');
//     attach_validation_onchange(country_origin_control, (v) => ({ passed: v, message: 'Country is required' })); 
    
//     const country_residence_control = make_control({ fieldname: 'country_of_residence', label: 'Country of Residence', fieldtype: 'Link', options: 'Country', reqd: 1 }, 'client-col-3');
//     attach_validation_onchange(country_residence_control, (v) => ({ passed: v, message: 'Country is required' })); 
    
//     make_control({ fieldname: 'age_range', label: 'Age Range', fieldtype: 'Select', options: ['\n21–29', '30–45', '46–55', '56–70', '+70'], reqd: 1 }, 'client-col-3');
//     make_control({ fieldname: 'yearly_estimated_income', label: 'Yearly Estimated Income (AED)', fieldtype: 'Currency', reqd: 1 }, 'client-col-3');
    
//     // Client Col 4 (12 column address fields)
//     make_control({ fieldname: 'home_address', label: 'Home Address', fieldtype: 'Small Text', reqd: 1 }, 'client-col-4');
//     make_control({ fieldname: 'uae_address', label: 'Address in UAE (Optional)', fieldtype: 'Small Text' }, 'client-col-4');
    
//     // Unit Details fields... 
//     make_control({ fieldname: 'unit_sale_type', label: 'Unit Category', fieldtype: 'Select', reqd: 1, options: ['Off-Plan', 'Secondary'] }, 'unit-col-1');
//     make_control({ fieldname: 'developer', label: 'Developer', fieldtype: 'Link', options: 'Developer', reqd: 1 }, 'unit-col-1');
//     const project_control = make_control({
//         fieldname: 'project',
//         label: 'Project',
//         fieldtype: 'Link',
//         options: 'Project List', 
//         reqd: 1,
//         onchange: () => {
//             const project_name = project_control.get_value();
//             const unit_floor_control = controls['unit_floor'];
//             unit_floor_control.set_value("");
//             unit_floor_control.df.options = [];
//             unit_floor_control.refresh();
//             if (!project_name) { return; }

//             frappe.call({
//                 method: "joel_living.custom_lead.get_project_floor_details", 
//                 args: { project_name: project_name },
//                 callback: function(r) {
//                     if (r.message) {
//                         const details = r.message;
//                         const number_of_floors_raw = details.no_of_floors || 0;
//                         const has_mezzanine = details.include_mezzanine_floor; 
//                         const has_ground_floor = details.include_ground_floor; 
                        
//                         let floor_options = [];
//                         let numbered_floor_count = number_of_floors_raw;

//                         if (has_ground_floor) { floor_options.push('G'); numbered_floor_count--; }
//                         if (has_mezzanine) { floor_options.push('M'); numbered_floor_count--; }
                        
//                         if (numbered_floor_count < 0) { numbered_floor_count = 0; }

//                         for (let i = 1; i <= numbered_floor_count; i++) { floor_options.push(String(i)); }

//                         unit_floor_control.df.options = floor_options;
//                         unit_floor_control.refresh();
//                     }
//                 }
//             });
//         }
//     }, 'unit-col-1');   
//     make_control({ fieldname: 'unit_floor', label: 'Unit Floor', fieldtype: 'Select', reqd: 1 }, 'unit-col-1'); 

//     make_control({ fieldname: 'unit_view', label: 'Unit View', fieldtype: 'Data', reqd: 1 }, 'unit-col-1');
    
//     // Unit Col 2
//     make_control({ fieldname: 'developer_sales_rep', label: 'Developer Sales Representative', fieldtype: 'Link', options: 'User' }, 'unit-col-2');
//     make_control({ fieldname: 'unit_number', label: 'Unit Number', fieldtype: 'Data', reqd: 1 }, 'unit-col-2');
//     make_control({ fieldname: 'unit_type', label: 'Unit Type (e.g., 1BR, Studio)', fieldtype: 'Data', reqd: 1 }, 'unit-col-2');
//     make_control({ fieldname: 'unit_price', label: 'Unit Price (AED)', fieldtype: 'Currency', reqd: 1 }, 'unit-col-2');
//     make_control({ fieldname: 'unit_area', label: 'Unit Area (SQFT)', fieldtype: 'Float', reqd: 1 }, 'unit-col-2');

//     // Unit Col 3
       
//     make_control({ fieldname: 'booking_eoi_paid_amount', label: 'Booking/EOI Paid Amount (AED)', fieldtype: 'Currency', reqd: 1 }, 'unit-col-3');
//     make_control({ fieldname: 'booking_form_signed', label: 'Booking Form Signed', fieldtype: 'Select', options: ['\nYes', '\nNo'], reqd: 1 }, 'unit-col-3');
//     make_control({ fieldname: 'booking_form_upload', label: 'Booking Form Upload', fieldtype: 'Attach' }, 'unit-col-3');
//     make_control({ fieldname: 'spa_signed', label: 'SPA Signed', fieldtype: 'Select', options: ['\nYes', '\nNo']}, 'unit-col-3');
//     make_control({ fieldname: 'spa_upload', label: 'SPA Upload', fieldtype: 'Attach' }, 'unit-col-3');
//     make_control({ fieldname: 'soa_upload', label: 'SOA Upload', fieldtype: 'Attach' }, 'unit-col-3');
    
//     // Receipts Section Title (use HTML instead of unsupported Section Break)
//     make_control({
//         fieldname: 'receipts_section_title',
//         fieldtype: 'HTML',
//         options: '<h4 style="margin-top:10px;">Receipts</h4>'
//     }, 'receipts_section_placeholder');

//     // This creates the table in its correct placeholder.
//     // make_control({
//     //     fieldname: 'receipts',
//     //     label: 'Receipts',
//     //     fieldtype: 'Table',
//     //     fields: [
//     //         { fieldname: 'receipt_date', label: 'Date', fieldtype: 'Date', in_list_view: 1, reqd: 1 },
//     //         { fieldname: 'receipt_amount', label: 'Amount (AED)', fieldtype: 'Currency', in_list_view: 1, reqd: 1 },
//     //         { fieldname: 'receipt_proof', label: 'Proof of Payment', fieldtype: 'Attach', reqd: 1, in_list_view: 1 }
//     //     ]
//     // }, 'receipts_table_placeholder');
    
//     // Screening fields... 
//     const screening_select = make_control({
//         fieldname: 'screened_before_payment',
//         label: 'Is the client screened by admin before the first payment?',
//         fieldtype: 'Select', options: ['', '\nYes', '\nNo'], reqd: 1
//     }, 'screening-section');

//     make_control({ fieldname: 'screenshot_of_green_light', label: 'Screenshot of green light', fieldtype: 'Attach', reqd: 1 }, 'screening-yes-section .col-md-6');
//     make_control({ fieldname: 'screening_date_time', label: 'Date and time of screening', fieldtype: 'Datetime', reqd: 1 }, 'screening-no-section .col-md-6:first-child');
//     make_control({ fieldname: 'screening_result', label: 'Results of screening', fieldtype: 'Select', options: ['\nGreen', '\nRed'], reqd: 1 }, 'screening-no-section .col-md-6:last-child');
//     make_control({ fieldname: 'screening_result', label: 'Result', fieldtype: 'Select', options: ['\nGreen', '\nRed'], reqd: 1 }, 'screening-no-section .col-md-12');

//     make_control({ fieldname: 'reason_for_late_screening', label: 'Reason for late screening', fieldtype: 'Small Text', reqd: 1 }, 'screening-no-section .col-md-12');
//     make_control({ fieldname: 'final_screening_screenshot', label: 'Screenshot of final screening result...', fieldtype: 'Attach', reqd: 1 }, 'screening-no-section .col-md-12');

  
//     $(screening_select.input).on('change', function() {
//         const val = screening_select.get_value();
//         let show_yes = false, show_no = false;
//         if (val) {
//             const trimmed_val = val.trim();
//             if (trimmed_val === 'Yes') { show_yes = true; }
//             else if (trimmed_val === 'No') { show_no = true; }
//         }
//         wrapper.find('#screening-yes-section').toggle(show_yes);
//         wrapper.find('#screening-no-section').toggle(show_no);
//     }).trigger('change');

//     // Remarks & Files fields...
//     make_control({ fieldname: 'remark_title', label: 'Title', fieldtype: 'Data' }, 'remarks-section');
//     make_control({ fieldname: 'remark_description', label: 'Description', fieldtype: 'Small Text' }, 'remarks-section');
//     make_control({ fieldname: 'remark_files', label: 'Attachments', fieldtype: 'Attach' }, 'remarks-section');
//     make_control({ fieldname: 'additional_file_title', label: 'File Title', fieldtype: 'Data' }, 'files-section .col-md-6:first-child');
//     make_control({ fieldname: 'additional_file_upload', label: 'File Upload', fieldtype: 'Attach' }, 'files-section .col-md-6:last-child');
    

    
//     // RENDER DYNAMIC FIELDS
//     const render_dynamic_fields = () => {
//         // Read the current value of the select control
//         const new_count = parseInt(controls.extra_joint_owners.get_value(), 10) || 0; 
//         const owners_placeholder = wrapper.find('#joint-owners-placeholder');
//         const kyc_placeholder = wrapper.find('#joint-owners-kyc-placeholder');
//         const current_count = owners_placeholder.find('.panel-group').length;

//         if (new_count > current_count) {
//             for (let i = current_count; i < new_count; i++) {
//                 const owner_num = i + 1, prefix = `jo${i}`;
                
//                 // *** Collapsible Accordion Setup (for Owner Info) ***
//                 const collapse_id = `jo-collapse-${i}`;
//                 const owner_section = $(`
//                     <div class="panel-group" id="jo-accordion-${i}" role="tablist" aria-multiselectable="true">
//                         <div class="panel panel-default">
//                             <div class="panel-heading" role="tab" id="heading-${collapse_id}" style="padding: 10px; cursor: pointer; background-color: #f7f9fa; border-bottom: 1px solid #d1d8dd;">
//                                 <h5 class="panel-title" data-toggle="collapse" data-parent="#jo-accordion-${i}" href="#${collapse_id}" aria-expanded="true" aria-controls="${collapse_id}">
//                                     Joint Owner ${owner_num} Details
//                                 </h5>
//                             </div>
//                             <div id="${collapse_id}" class="panel-collapse collapse joint-owner-wrapper" role="tabpanel" aria-labelledby="heading-${collapse_id}" data-idx="${i}" style="padding:15px; border:1px solid #d1d8dd; border-top: none;">
//                                 <div class="row">
//                                     <div class="col-md-4" id="${prefix}_col1"></div>
//                                     <div class="col-md-4" id="${prefix}_col2"></div>
//                                     <div class="col-md-4" id="${prefix}_col3"></div>
//                                     <div class="col-md-12" id="${prefix}_col4"></div>
//                                 </div>
//                             </div>
//                         </div>
//                     </div>
//                 `);
//                 owners_placeholder.append(owner_section);
//                 // * End Collapsible Setup *

//                 // *** KYC Section Setup (in Screening & KYC Tab) ***
//                 const kyc_html = $(`<div class="kyc-section joint-owner-kyc-wrapper row mt-3" data-idx="${i}"><div class="col-md-12"><h6>KYC for Joint Owner ${owner_num}</h6></div><div class="col-md-6" id="${prefix}_kyc_date"></div><div class="col-md-6" id="${prefix}_kyc_file"></div></div>`);
//                 kyc_placeholder.append(kyc_html);
                
//                 // Column 1
//                 make_control({ fieldname: `${prefix}_first_name`, label: 'First Name', fieldtype: 'Data', reqd: 1 }, `${prefix}_col1`);
//                 make_control({ fieldname: `${prefix}_last_name`, label: 'Last Name', fieldtype: 'Data', reqd: 1 }, `${prefix}_col1`);
// const jo_email_control = make_control({ fieldname: `${prefix}_email`, label: 'Email', fieldtype: 'Data', options: 'Email', reqd: 1 }, `${prefix}_col1`);
// attach_validation_onchange(jo_email_control, validate_email);                
//                 make_control({ fieldname: `${prefix}_date_of_birth`, label: 'Date of Birth', fieldtype: 'Date', reqd: 1 }, `${prefix}_col1`);
//                 // attach_validation_onchange(jo_dob_control, validate_age); 

//                 // Column 2
//                 const jo_phone_control = make_control({ 
//                     fieldname: `${prefix}_main_phone_number`,
//                     label: 'Main Phone Number', 
//                     fieldtype: 'Phone', 
//                     reqd: 1, 
//                     options: { 
//                         onlyCountries: ['ae'],
//                         initialCountry: 'ae',
//                         separateDialCode: true
//                     }
//                 }, `${prefix}_col2`);

//                 // Set default +971- for Joint Owner Phone
//                 setTimeout(() => {
//                     // Check if the control exists AND its current value is not set
//                     if (jo_phone_control && !jo_phone_control.get_value()) { 
//                         jo_phone_control.set_value('+971-');
//                     }
//                 }, 50);

//                 const jo_uae_phone_control = make_control({ fieldname: `${prefix}_uae_phone_number`, label: 'UAE Phone Number', fieldtype: 'Data', description: 'Fixed to +971 for UAE' }, `${prefix}_col2`);
//                 setup_uae_phone_data_control(jo_uae_phone_control);
                
//                 const jo_passport_num_control = make_control({ fieldname: `${prefix}_passport_number`, label: 'Passport Number', fieldtype: 'Data', reqd: 1 }, `${prefix}_col2`);
//                 attach_validation_onchange(jo_passport_num_control, validate_passport_chars);
                
//                 const jo_passport_expiry_control = make_control({ fieldname: `${prefix}_passport_expiry_date`, label: 'Passport Expiry Date', fieldtype: 'Date', reqd: 1 }, `${prefix}_col2`);
//                 attach_validation_onchange(jo_passport_expiry_control, validate_future_date);
                
//                 make_control({ fieldname: `${prefix}_passport_copy`, label: 'Passport Copy (PDF/JPG/PNG)', fieldtype: 'Attach', reqd: 1, options: { accepted_file_types: ['.pdf', '.jpg', '.jpeg', '.png'], show_preview: true } }, `${prefix}_col2`);

//                 // Column 3
//                 const jo_country_origin_control = make_control({ fieldname: `${prefix}_country_of_origin`, label: 'Country of Origin', fieldtype: 'Link', options: 'Country', reqd: 1 }, `${prefix}_col3`);
//                 attach_validation_onchange(jo_country_origin_control, (v) => ({ passed: v, message: 'Country is required' }));

//                 const jo_country_residence_control = make_control({ fieldname: `${prefix}_country_of_residence`, label: 'Country of Residence', fieldtype: 'Link', options: 'Country', reqd: 1 }, `${prefix}_col3`);
//                 attach_validation_onchange(jo_country_residence_control, (v) => ({ passed: v, message: 'Country is required' }));

//                 make_control({ fieldname: `${prefix}_age_range`, label: 'Age Range', fieldtype: 'Select', reqd: 1, options: ['\n21–29', '30–45', '46–55', '56–70', '+70'], reqd: 1 }, `${prefix}_col3`);
//                 make_control({ fieldname: `${prefix}_yearly_estimated_income`, label: 'Yearly Estimated Income (AED)', fieldtype: 'Currency', reqd: 1 }, `${prefix}_col3`);

//                 // Column 4 (12 column address)
//                 make_control({ fieldname: `${prefix}_home_address`, label: 'Home Address', fieldtype: 'Small Text', reqd: 1 }, `${prefix}_col4`);
//                 make_control({ fieldname: `${prefix}_uae_address`, label: 'Address in UAE (Optional)', fieldtype: 'Small Text' }, `${prefix}_col4`);
                
//                 // KYC placeholders (in the Screening & KYC Tab)
//                 const kyc_date_control = make_control({ fieldname: `${prefix}_kyc_date`, label: 'Date of KYC Entry', fieldtype: 'Date', reqd: 1 }, `${prefix}_kyc_date`);
//                 const kyc_file_control = make_control({ fieldname: `${prefix}_kyc_file`, label: 'KYC File Upload', fieldtype: 'Attach', reqd: 1, options: { accepted_file_types: ['.pdf', '.jpg', '.jpeg', '.png'], show_preview: true } }, `${prefix}_kyc_file`);
                
//                 // P1 FIX: Attach Live Validation to ALL newly created controls 
//                 const new_owner_controls = [
//                     `${prefix}_first_name`, `${prefix}_last_name`, `${prefix}_email`, `${prefix}_date_of_birth`, 
//                     `${prefix}_main_phone_number`, `${prefix}_uae_phone_number`, `${prefix}_passport_number`, 
//                     `${prefix}_passport_expiry_date`, `${prefix}_passport_copy`, `${prefix}_country_of_origin`, 
//                     `${prefix}_country_of_residence`, `${prefix}_age_range`, `${prefix}_yearly_estimated_income`, 
//                     `${prefix}_home_address`, `${prefix}_uae_address`, `${prefix}_kyc_date`, `${prefix}_kyc_file`
//                 ];

//                 new_owner_controls.forEach(key => {
//                     if(controls[key]) attachLiveValidation(controls[key]);
//                 });
                
//                 // Collapse the section by default
//                 owner_section.find(`#${collapse_id}`).collapse('hide');
//             }
//         }
//         else if (new_count < current_count) {
//             for (let i = new_count; i < current_count; i++) {
//                 const prefix = `jo${i}`;
//                 owners_placeholder.find(`#jo-accordion-${i}`).remove();
//                 kyc_placeholder.find(`.joint-owner-kyc-wrapper[data-idx="${i}"]`).remove();
                
//                 const fields_to_remove = [
//                     `${prefix}_first_name`, `${prefix}_last_name`, `${prefix}_email`, `${prefix}_main_phone_number`, `${prefix}_uae_phone_number`,
//                     `${prefix}_passport_number`, `${prefix}_passport_expiry_date`, `${prefix}_date_of_birth`, `${prefix}_passport_copy`, 
//                     `${prefix}_country_of_origin`, `${prefix}_country_of_residence`, `${prefix}_age_range`, `${prefix}_yearly_estimated_income`,
//                     `${prefix}_home_address`, `${prefix}_uae_address`,
//                     `${prefix}_kyc_date`, `${prefix}_kyc_file`
//                 ];
//                 fields_to_remove.forEach(fieldname => { delete controls[fieldname]; });
//             }
//         }
//     };
//     // --- Live validation cleanup (for all field types) ---
// function attachLiveValidation(control) {
//     const $wrapper = $(control.wrapper);
//     const $input = $(control.input);

//     // For basic input fields (Data, Date, Int, Float, etc.)
//     if (["Data", "Date", "Int", "Float", "Small Text", "Text", "Text Editor", "Datetime", "Currency"].includes(control.df.fieldtype)) {
//         $input.off("input.fieldvalidate change.fieldvalidate")
//             .on("input.fieldvalidate change.fieldvalidate", function () {
//                 if ($(this).val() && String($(this).val()).trim() !== "") {
//                     $wrapper.find('.field-error').remove();
//                     $wrapper.find('.control-input').css('border-color', '');
//                     $input.css('border-color', ''); // Ensure input element border is cleared
//                 }
//             });
//     }

//     // For Select fields
//     if (control.df.fieldtype === "Select") {
//         $wrapper.find("select").off("change.fieldvalidate").on("change.fieldvalidate", function () {
//             if ($(this).val()) {
//                 $wrapper.find('.field-error').remove();
//                 $wrapper.find('.select-container').css('border', '');
//             }
//         });
//     }

//     // For Link fields
//     if (control.df.fieldtype === "Link") {
//         // Use a safe onchange for validation error cleanup
//         const original_onchange = control.df.onchange;
//         control.df.onchange = () => {
//             const val = control.get_value();
//             if (val && val.trim() !== "") {
//                 $wrapper.find('.field-error').remove();
//                 $input.css('border-color', ''); 
//             }
//             if(original_onchange) original_onchange();
//         };
//     }

//     // For Attach fields
//     if (control.df.fieldtype === "Attach") {
//         // Attaching to the `on` call in control, triggered after a successful file attach
//         control.$wrapper.off("attachment_add").on("attachment_add", function () {
//             $wrapper.find('.field-error').remove();
//             $wrapper.find('.attach-button').closest('.input-with-feedback').css('border-color', '');
//         });
        
//     }
// }


//     // --- UI EVENT HANDLERS & BUTTONS ---

//     // 1. Manually Inject Close Button HTML into Header (Top Right Button)
//     const close_button_html = `
//         <a href="#" class="btn btn-xs btn-default" id="custom-close-dialog" 
//            style="position: absolute; right: 15px; top: 12px; color: #1e88e5; border-color: #bbdefb; background-color: #e3f2fd; font-weight: bold; padding: 4px 10px;">
//             Close
//         </a>`;
//     dialog.header.find('.modal-title').closest('.modal-header').append(close_button_html);
    
//     // 2. Attach action to the new manual close button - Dual Confirmation (calls functional small dialog)
//     dialog.header.find('#custom-close-dialog').on('click', (e) => {
//         e.preventDefault();
//         show_custom_close_confirmation();
//     });
//     // This MUST also be updated to ensure the single browser prompt doesn't overwrite your custom dialog on native X-click
//     dialog.header.find('.modal-close').off('click').on('click', (e) => { 
//         e.preventDefault();
//         show_custom_close_confirmation();
//     });

//     // CRITICAL FIX FOR TAB SWITCHING RELIABILITY (Replace default bootstrap logic with custom)
//     wrapper.find('.nav-link').on('click', function(e) { 
//         e.preventDefault(); 
//         const target = $(this).data('target'); 

//         // Remove active class from all links and content
//         wrapper.find('.nav-link').removeClass('active'); 
//         wrapper.find('.tab-pane').removeClass('show active'); 
        
//         // Add active class to clicked link and target content
//         $(this).addClass('active'); 
//         wrapper.find(target).addClass('show active'); 

//         // Force scroll to top of the dialog after tab change
//         frappe.utils.scroll_to(dialog.body, true, 0);
//         if (target === '#tab-unit') {
//         // Use a timeout to guarantee the tab is visually 'open' before filling its HTML
//         setTimeout(() => {
//             render_receipt_rows(); 
//         }, 100);
//     }
//     });
   
//     // --- THE DEFINITIVE SOLUTION: Create the control only when its tab is visible ---
//     // --- THE DEFINITIVE SOLUTION: Fixing the render race condition ---
//     // --- THE DEFINITIVE SOLUTION: Forcing a final UI render event ---
// //    wrapper.find('.nav-link[data-target="#tab-unit"]').one('click', () => {
// //         console.log("Tab clicked. Beginning table creation and population.");

// //         // Prevent running twice
// //         if (controls['receipts']) {
// //             return;
// //         }

// //         // STEP A: CREATE THE CONTROL now that its container is visible.
// //         // This guarantees Frappe will initialize it correctly.
// //         make_control({
// //             fieldname: 'receipts',
// //             label: 'Receipts',
// //             fieldtype: 'Table',
// //             fields: [
// //                 { fieldname: 'receipt_date', label: 'Date', fieldtype: 'Date', in_list_view: 1, reqd: 1 },
// //                 { fieldname: 'receipt_amount', label: 'Amount (AED)', fieldtype: 'Currency', in_list_view: 1, reqd: 1 },
// //                 { fieldname: 'receipt_proof', label: 'Proof of Payment', fieldtype: 'Attach', reqd: 1, in_list_view: 1 }
// //             ]
// //         }, 'receipts_table_placeholder');

// //         // STEP B: WAIT briefly for the browser to render the new empty table.
// //         // This solves the JavaScript race condition.
// //         setTimeout(() => {
// //             const receipts_control = controls['receipts'];

// //             // STEP C: POPULATE the now healthy and visible control.
// //             if (receipts_control && draft_receipts_data && Array.isArray(draft_receipts_data)) {
// //                 console.log("Control is rendered. Populating with data:", draft_receipts_data);
                
// //                 // The standard API now works because the control is healthy.
// //                 receipts_control.set_value(draft_receipts_data);
// //                 receipts_control.refresh();

// //                 console.log("SUCCESS: Population complete.");
// //             }
// //         }, 150); // A small delay is all that's needed.
// //     });
//     // END OF CORRECTED FIX
//     // Dialog cleanup logic
//     dialog.on_hide = () => { clearInterval(dialog.draft_saver); };
//     dialog.draft_saver = setInterval(save_draft, 3000);
    
//     // 3. Define the bottom button (Create Registration) - Primary Action
//     // dialog.set_primary_action(__("Create Registration"), () => {
//     //     const values = {};
//     //     let first_invalid_control = null;
//     //     let is_valid = true;

//     //     // Clear any previous error messages and borders from custom and primary validation
//     //     wrapper.find(".field-error").remove();
//     //     wrapper.find(".local-error-message").remove(); 
//     //     wrapper.find('input, select, textarea').css('border-color', '');
//     //     wrapper.find('.attach-button').closest('.input-with-feedback').css('border-color', '');
//     //     wrapper.find('.select-container').css('border', '');
        
//     //     // --- FIX: Conditional Required State Check ---
//     //     const screening_status_val = controls.screened_before_payment ? (controls.screened_before_payment.get_value() || '').trim() : '';
//     //     const is_yes_required = screening_status_val === 'Yes';
//     //     const is_no_required = screening_status_val === 'No';
        
//     //     // Fields that are conditionally required
//     //     const YES_FIELDS = ['screenshot_of_green_light'];
//     //     const NO_FIELDS = ['screening_date_time', 'screening_result', 'reason_for_late_screening', 'final_screening_screenshot'];


//     //     // Loop through all controls in dialog (Validation Check)
//     //     for (let key in controls) {
//     //         if (controls[key]) {
//     //             const control = controls[key];
//     //             const value = control.get_value();
//     //             let failed_validation = false;
//     //             let validation_message = "";

//     //             // --- 1. Custom Field Validations (Check BEFORE required if present) ---
//     //             // (Existing Custom Validation logic remains here, no change needed)
//     //             let custom_validation_result = { passed: true, message: "" };

//     //             if (key.endsWith('passport_expiry_date') && value) {
//     //                  custom_validation_result = validate_future_date(value);
//     //             } else if (key.endsWith('passport_number') && value) {
//     //                  custom_validation_result = validate_passport_chars(value);
//     //             }
                
//     //             if (!custom_validation_result.passed) {
//     //                 failed_validation = true;
//     //                 validation_message = custom_validation_result.message;
//     //             }
                
//     //             // --- 2. Required Field Validation (If custom validation hasn't already failed) ---
//     //             if (!failed_validation && control.df.reqd) 
//     //             {
//     //                 const trimmed_value = String(value || '').trim();
//     //                 let is_empty = (value === undefined || value === null || trimmed_value === "" || (Array.isArray(value) && value.length === 0));

//     //                 // Special handling for Phone controls which can default to a prefix
//     //                 if ((control.fieldtype === 'Phone' || key === 'main_phone_number' || key.endsWith('_phone_number')) && (trimmed_value === '+971-' || trimmed_value === '+971')) {
//     //                     is_empty = true;
//     //                 }
                    
//     //                 // Special handling for Select controls with default 'blank' option 
//     //                 if (control.fieldtype === 'Select' && (value === undefined || value === null || trimmed_value === "" || trimmed_value === "null")) {
//     //                      if (!value || (typeof value === 'string' && value.trim() === '')) {
//     //                          is_empty = true;
//     //                      } else {
//     //                          is_empty = false;
//     //                      }
//     //                 }

//     //                 // --- NEW LOGIC: Check for Conditional Required Fields ---
//     //                 let should_check_required = true;
//     //                 if (YES_FIELDS.includes(key) && !is_yes_required) {
//     //                     should_check_required = false;
//     //                 } else if (NO_FIELDS.includes(key) && !is_no_required) {
//     //                     should_check_required = false;
//     //                 }
//     //                 // -----------------------------------------------------

//     //                 if (should_check_required && is_empty) {
//     //                     failed_validation = true;
//     //                     validation_message = "This field is required.";
//     //                 }
//     //             }
                
//     //             // --- 3. Handle Failure: Apply UI Error and Log First Invalid Control ---
//     //             if (failed_validation) {
//     //                 is_valid = false;

//     //                 // Display error
//     //                 const $wrapper = $(control.wrapper);
//     //                 $wrapper.find('.field-error, .local-error-message').remove();
//     //                 $wrapper.append(`<div class="field-error local-error-message" style="color: red; font-size: 11px; margin-top: 5px;">${validation_message}</div>`);
                    
//     //                 // Apply red border
//     //                 const $target_border = (control.fieldtype === 'Attach') 
//     //                     ? $wrapper.find('.attach-button').closest('.input-with-feedback') 
//     //                     : ($(control.input).length ? $(control.input) : $wrapper.find('.control-input'));

//     //                 // For Select, highlight the internal input container if no explicit input field
//     //                 if (control.fieldtype === 'Select') {
//     //                      $wrapper.find('.select-container').css('border', '1px solid red');
//     //                 } else {
//     //                      $target_border.css('border-color', 'red');
//     //                 }
                    

//     //                 if (!first_invalid_control) {
//     //                     first_invalid_control = control;
//     //                 }
//     //             }

//     //             // Collect values
//     //             values[key] = value;
//     //         }
//     //     }

//     //     // --- FINAL CHECK AND ACTION ---

//     //     if (!is_valid) { // Block submission if validation failed
//     //         const control = first_invalid_control;

//     //         // ** 1. Open Collapsible Section if needed (for Joint Owners) **
//     //         const joint_owner_wrapper = $(control.wrapper).closest('.joint-owner-wrapper');
//     //         if (joint_owner_wrapper.length) {
//     //             // This targets the inner div with the collapse class (e.g., #jo-collapse-0)
//     //             const collapse_id = joint_owner_wrapper.attr('id'); 
//     //             // Use Bootstrap/JQuery to force show the collapsed section
//     //             $(`#${collapse_id}`).collapse('show'); 
//     //         }

//     //         // ** 2. Switch Tab if needed **
//     //         const tab_pane = $(control.wrapper).closest('.tab-pane');
//     //         if (tab_pane.length) {
//     //             const tab_id = tab_pane.attr('id');
//     //             const tab_link = wrapper.find(`.nav-link[data-target="#${tab_id}"]`);
//     //             if (tab_link.length && !tab_link.hasClass('active')) {
//     //                 // Manually click the link to switch the tab using the custom handler
//     //                 tab_link.trigger('click'); 
//     //             }
//     //         }

//     //         // ** 3. Scroll & focus **
//     //         setTimeout(() => { 
//     //              // Scroll to the error field's wrapper
//     //              frappe.utils.scroll_to($(control.wrapper), true, 150);
//     //              if (control.input) control.input.focus();
//     //              else control.set_focus(); 
//     //         }, 300); // Give extra time for collapse/tab animation

//     //         // Stop submission alert
//     //         // frappe.show_alert({
//     //         //     message: __("Please correct all validation errors before proceeding. Errors may be on hidden fields in other tabs or in joint owner sections."),
//     //         //     indicator: "red",
//     //         // });

//     //         return;
//     //     }

//     //     // --- If all valid, proceed to backend ---
//     //     // const primary_btn = dialog.get_primary_btn();
//     //     // primary_btn.prop('disabled', true);
//     //     // frappe.call({
//     //     //     method: "joel_living.custom_lead.create_sales_registration",
//     //     //     args: {
//     //     //         lead_name: me.frm.doc.name,
//     //     //         data: values,
//     //     //     },
//     //     //     callback: (r) => {
//     //     //         if (r.message) {
//     //     //             localStorage.removeItem(DRAFT_KEY);
//     //     //             dialog.hide();
//     //     //             // frappe.set_route('Form', 'Sales Completion Form', r.message);
//     //     //             me.frm.reload_doc();
//     //     //         }
//     //     //     },
//     //     //     always: () => {
//     //     //         primary_btn.prop('disabled', false);
//     //     //     },
//     //     // });



//     //     const confirm_dialog = new frappe.ui.Dialog({
//     //         title: __('Confirm Submission'),
//     //         fields: [
//     //             {
//     //                 fieldtype: 'HTML',
//     //                 options: `<h4>${__('Are you sure you want to create the Sales Registration?')}</h4>`
//     //             }
//     //         ],
//     //         primary_action_label: __('Confirm & Submit'),
//     //         primary_action: () => {
//     //             confirm_dialog.hide();
                
//     //             // --- If all valid, proceed to backend ---
//     //             const primary_btn = dialog.get_primary_btn();
//     //             primary_btn.prop('disabled', true);
                
//     //             // Collect values one final time (already collected, but safer)
//     //             // Need to re-collect values if this block is executed separately, 
//     //             // but for simplicity, we'll pass the 'values' object already populated.
//     //             console.log('aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',values);
//     //             frappe.call({
//     //                 method: "joel_living.custom_lead.create_sales_registration",
//     //                 args: {
//     //                     lead_name: me.frm.doc.name,
                        
//     //                     data: values, // 'values' is still accessible here from the outer function scope
//     //                 },
//     //                 callback: (r) => {
//     //                     if (r.message) {
//     //                         // localStorage.removeItem(DRAFT_KEY);
//     //                         dialog.hide();
//     //                         // frappe.set_route('Form', 'Sales Completion Form', r.message);
//     //                         me.frm.reload_doc();
//     //                     }
//     //                 },
//     //                 always: () => {
//     //                     primary_btn.prop('disabled', false);
//     //                 },
//     //             });
//     //         }
//     //     });
        
//     //     confirm_dialog.show();
//     // });

//     dialog.set_primary_action(__("Create Registration"), () => {
//         const values = {};
//         let first_invalid_control = null;
//         let is_valid = true;
//          receipts_data = get_receipt_values(); 
//         // Clear any previous error messages and borders from custom and primary validation
//         wrapper.find(".field-error").remove();
//         wrapper.find(".local-error-message").remove(); 
//         wrapper.find('input, select, textarea').css('border-color', '');
//         wrapper.find('.attach-button').closest('.input-with-feedback').css('border-color', '');
//         wrapper.find('.select-container').css('border', '');
        
//         // --- FIX: Conditional Required State Check ---
//         const screening_status_val = controls.screened_before_payment ? (controls.screened_before_payment.get_value() || '').trim() : '';
//         const is_yes_required = screening_status_val === 'Yes';
//         const is_no_required = screening_status_val === 'No';
        
//         // Fields that are conditionally required
//         const YES_FIELDS = ['screenshot_of_green_light'];
//         const NO_FIELDS = ['screening_date_time', 'screening_result', 'reason_for_late_screening', 'final_screening_screenshot'];


//         // Loop through all controls in dialog (Validation Check)
//         for (let key in controls) {
//             if (controls[key]) {
//                 const control = controls[key];
//                 const value = control.get_value();
//                 let failed_validation = false;
//                 let validation_message = "";

//                 // --- 1. Custom Field Validations (Check BEFORE required if present) ---
//                 let custom_validation_result = { passed: true, message: "" };

//                 if (key.endsWith('passport_expiry_date') && value) {
//                      custom_validation_result = validate_future_date(value);
//                 } else if (key.endsWith('passport_number') && value) {
//                      custom_validation_result = validate_passport_chars(value);
//                 }
                
//                 if (!custom_validation_result.passed) {
//                     failed_validation = true;
//                     validation_message = custom_validation_result.message;
//                 }
                
//                 // --- 2. Required Field Validation (If custom validation hasn't already failed) ---
//                 if (!failed_validation && control.df.reqd) 
//                 {
//                     const trimmed_value = String(value || '').trim();
//                     let is_empty = (value === undefined || value === null || trimmed_value === "" || (Array.isArray(value) && value.length === 0));

//                     if ((control.fieldtype === 'Phone' || key === 'main_phone_number' || key.endsWith('_phone_number')) && (trimmed_value === '+971-' || trimmed_value === '+971')) {
//                         is_empty = true;
//                     }
                    
//                     if (control.fieldtype === 'Select' && (value === undefined || value === null || trimmed_value === "" || trimmed_value === "null")) {
//                          if (!value || (typeof value === 'string' && value.trim() === '')) {
//                              is_empty = true;
//                          } else {
//                              is_empty = false;
//                          }
//                     }

//                     let should_check_required = true;
//                     if (YES_FIELDS.includes(key) && !is_yes_required) {
//                         should_check_required = false;
//                     } else if (NO_FIELDS.includes(key) && !is_no_required) {
//                         should_check_required = false;
//                     }

//                     if (should_check_required && is_empty) {
//                         failed_validation = true;
//                         validation_message = "This field is required.";
//                     }
//                 }
                
//                 // --- 3. Handle Failure: Apply UI Error and Log First Invalid Control ---
//                 if (failed_validation) {
//                     is_valid = false;

//                     const $wrapper = $(control.wrapper);
//                     $wrapper.find('.field-error, .local-error-message').remove();
//                     $wrapper.append(`<div class="field-error local-error-message" style="color: red; font-size: 11px; margin-top: 5px;">${validation_message}</div>`);
                    
//                     const $target_border = (control.fieldtype === 'Attach') 
//                         ? $wrapper.find('.attach-button').closest('.input-with-feedback') 
//                         : ($(control.input).length ? $(control.input) : $wrapper.find('.control-input'));

//                     if (control.fieldtype === 'Select') {
//                          $wrapper.find('.select-container').css('border', '1px solid red');
//                     } else {
//                          $target_border.css('border-color', 'red');
//                     }
                    
//                     if (!first_invalid_control) {
//                         first_invalid_control = control;
//                     }
//                 }

//                 // Collect values
//                 values[key] = value;
//             }
//         }
//         if (receipts_data.length === 0) {
//             is_valid = false;
//              // Append global error message if receipts are required and empty
//              frappe.show_alert({ message: __("Please add at least one receipt."), indicator: "red" }); 
//         } else {
//              receipts_data.forEach((row, index) => {
//                 const row_num = index + 1;
//                 // You must update the HTML in render_receipt_rows to show errors here
//                 // For simplicity, this validation only blocks submission
//                 if (!row.receipt_date) {
//                     is_valid = false;
//                     frappe.show_alert({ message: `Row #${row_num}: Date is required.`, indicator: "red" });
//                 }
//                 if (!row.receipt_amount || parseFloat(row.receipt_amount) <= 0) {
//                     is_valid = false;
//                     frappe.show_alert({ message: `Row #${row_num}: Amount must be a positive number.`, indicator: "red" });
//                 }
//                 if (!row.receipt_proof) {
//                     is_valid = false;
//                     frappe.show_alert({ message: `Row #${row_num}: Proof of Payment is required.`, indicator: "red" });
//                 }
//              });
//         }
//         // END OF NEW VALIDATION BLOCK

//         // --- FINAL CHECK AND ACTION ---
//         values.receipts = receipts_data;
//         if (!is_valid) { // Block submission if validation failed
//             const control = first_invalid_control;

//             const joint_owner_wrapper = $(control.wrapper).closest('.joint-owner-wrapper');
//             if (joint_owner_wrapper.length) {
//                 const collapse_id = joint_owner_wrapper.attr('id'); 
//                 $(`#${collapse_id}`).collapse('show'); 
//             }

//             const tab_pane = $(control.wrapper).closest('.tab-pane');
//             if (tab_pane.length) {
//                 const tab_id = tab_pane.attr('id');
//                 const tab_link = wrapper.find(`.nav-link[data-target="#${tab_id}"]`);
//                 if (tab_link.length && !tab_link.hasClass('active')) {
//                     tab_link.trigger('click'); 
//                 }
//             }

//             setTimeout(() => { 
//                  frappe.utils.scroll_to($(control.wrapper), true, 150);
//                  if (control.input) control.input.focus();
//                  else control.set_focus(); 
//             }, 300);

//             return;
//         }

//         const confirm_dialog = new frappe.ui.Dialog({
//             title: __('Confirm Submission'),
//             fields: [
//                 {
//                     fieldtype: 'HTML',
//                     options: `<h4>${__('Are you sure you want to create the Sales Registration?')}</h4>`
//                 }
//             ],
//             primary_action_label: __('Confirm & Submit'),
//             primary_action: () => {
//                 confirm_dialog.hide();
                
//                 const primary_btn = dialog.get_primary_btn();
//                 primary_btn.prop('disabled', true);
                
//                 console.log('Submitting values:', values);
//                 frappe.call({
//                     method: "joel_living.custom_lead.create_sales_registration",
//                     args: {
//                         lead_name: me.frm.doc.name,
//                         data: values,
//                     },
//                     callback: (r) => {
//                         if (r.message) {
//                             dialog.hide();
//                             clear_draft();
//                             me.frm.reload_doc();
//                             me.apply_workflow_action(d);
//                         }
//                     },
//                     always: () => {
//                         primary_btn.prop('disabled', false);
//                     },
//                 });
//             }
//         });
        
//         confirm_dialog.show();
//     });


//     dialog.show();

//     // Create Main Client KYC only ONCE in its own safe placeholder
//     make_control({ fieldname: `main_client_kyc_date`, label: 'Date of KYC Entry', fieldtype: 'Date', reqd: 1 }, 'main-kyc-placeholder');
//     make_control({ fieldname: `main_client_kyc_file`, label: 'KYC File Upload', fieldtype: 'Attach', reqd: 1, options: { accepted_file_types: ['.pdf', '.jpg', '.jpeg', '.png'], show_preview: true } }, 'main-kyc-placeholder');
    
//     // Create the joint owner select control and attach its event handler
//     const joint_owners_wrapper = wrapper.find('#joint-owners-section');
//     joint_owners_wrapper.append('<div class="row"><div class="col-md-4" id="joint-owners-select"></div></div><div id="joint-owners-placeholder"></div>');
//     make_control({fieldname: 'extra_joint_owners', label: 'Number of Additional Joint Owners', fieldtype: 'Select', options: '0\n1\n2\n3'}, 'joint-owners-select');
//     controls.extra_joint_owners.df.onchange = render_dynamic_fields;

//     // P1 FIX: Loop through ALL statically created controls to attach generic live validation for error clearing
//     for (let key in controls) {
//         if (controls[key]) {
//             attachLiveValidation(controls[key]); 
//         }
//     }
    
//     // Load initial data trigger (calls load_draft and render_dynamic_fields)
//     load_draft();
    
//     render_dynamic_fields(); // Final initial render call (runs after initial load for fresh opens)
// }













show_sales_completion_dialog() {
    const me = this;
    const lead = me.frm.doc;
    let controls = {};
     let receipts_data = [];
    // --- DRAFT MANAGEMENT ---
    const DRAFT_KEY = `sales_reg_draft_${frappe.session.user}_${lead.name}`;
   
    const get_receipt_values = () => {
        const collected_data = [];
        // Only collect from rows that are part of the table body (ignore header, buttons)
        const $rows = wrapper.find('#receipts_table_placeholder table tbody tr').not('.no-data-row');
        $rows.each(function() {
            const $row = $(this);
            // We use .get_value() here to leverage the frappe number and link control formatting
            // even though they're not frappe controls anymore - fall back to basic input value.
            const date_val = $row.find('.receipts-date').val();
            const amount_val = $row.find('.receipts-amount').val();
            const proof_val = $row.find('.receipts-proof').val();
           
            // Only collect the row if at least one critical field has a value
            if (date_val || amount_val || proof_val) {
                 collected_data.push({
                    receipt_date: date_val,
                    receipt_amount: amount_val,
                    receipt_proof: proof_val
                 });
            }
        });
        return collected_data;
    };
    const save_draft = () => {
    const values = {};
    for (let key in controls) {
        const control = controls[key];
        if (control && control.get_value) {
            if (key === 'receipts') continue;
            // Generic handling for all other field types
            let val = control.get_value();
            if (val === null || val === undefined) {
                val = '';
            }
            // --- START UPDATED FIX: More reliable cleaning and saving logic ---
            // Clean specific placeholder values to null
            if (control.fieldtype === 'Phone' && (val === '+971-' || val === '+971')) {
                val = null;
            }
            const valString = String(val).toLowerCase();
            // Clean empty or literal 'null' strings to null
            if (valString === 'null' || valString.trim() === '') {
                 val = null;
            }
            // --- END UPDATED FIX ---
            const is_meaningful = (val !== null); // A value is meaningful if it's not null
            
            // Define all keys whose state should be saved even if empty
            const is_ui_state_key = key === 'extra_joint_owners' ||
                                    key === 'unit_floor' ||
                                    key === 'screened_before_payment' ||
                                    key === 'booking_form_signed' ||
                                    key === 'spa_signed';
                                    
            const is_joint_owner_key = key.startsWith('jo'); // Critical for saving dynamic JO fields
            
            if (is_meaningful || is_ui_state_key || is_joint_owner_key) {
                values[key] = val;
            }
        }
    }
    // CRITICAL: Manually get and inject the custom table data.
    const current_receipts_data = get_receipt_values();
    if (current_receipts_data.length > 0) {
        values.receipts = current_receipts_data;
    }
    // Only save to localStorage if there is data to save
    if (Object.keys(values).length > 0) {
        localStorage.setItem(DRAFT_KEY, JSON.stringify(values));
    } else {
        // If the form is empty, clear any old drafts
        localStorage.removeItem(DRAFT_KEY);
    }
};
 
    const clear_draft = () => {
        localStorage.removeItem(DRAFT_KEY);
    };
   
    const load_draft = () => {
        const draft_data = localStorage.getItem(DRAFT_KEY);
        let loaded = false;
        if (draft_data) {
            const values = JSON.parse(draft_data);
            // Store receipts data from draft in a variable. It will be rendered later.
           // CRITICAL: If receipts exist, populate the custom data array.
            if (values.receipts && Array.isArray(values.receipts)) {
                receipts_data = values.receipts; // This is where the draft data is loaded into our global manager array.
            }
            // Primary Draft Load (delayed to allow controls to be created first)
            setTimeout(() => {
                const is_project_in_draft = !!values.project;
                for (let key in values) {
                    if (key === 'receipts' || !controls[key] || !controls[key].set_value) {
                        continue;
                    }
                    const control = controls[key];
                    const original_onchange = control.df.onchange;
                    // Temporarily disable onchange for Link fields to prevent premature triggers
                    if (key === 'project' || control.fieldtype === 'Link') {
                        control.df.onchange = null;
                    }
                    let value_to_set = values[key];
                    
                    // --- CRITICAL FIX: AGGRESSIVE NULL/LINK CLEANING ---
                    // Aggressively convert 'null' string to empty string for all Data, Phone, and Text fields
                    if (['Data', 'Small Text', 'Phone'].includes(control.fieldtype) && 
                        (String(value_to_set).toLowerCase() === 'null' || value_to_set === null)) 
                    {
                        value_to_set = ''; 
                    }
                    
                    // For Link fields, aggressively ensure the value is a string to prevent errors.
                    if (control.fieldtype === 'Link') {
                        value_to_set = String(values[key] || '');
                    }
                    // --- END CRITICAL FIX ---

                    // Set value and restore onchange handler
                    control.set_value(value_to_set);
                    if (original_onchange) {
                        control.df.onchange = original_onchange;
                    }
                }
                // Manually trigger onchange for dynamic sections after their values are set
                if (controls.extra_joint_owners && controls.extra_joint_owners.df.onchange) {
                    controls.extra_joint_owners.df.onchange();
                }
                 if (parseInt(values.extra_joint_owners) > 0 && controls.jo0_main_phone_number) {
                    const jo0_phone_input = $(controls.jo0_main_phone_number.input);
                    // We only care if the current visual state is broken from draft loading
                    if (jo0_phone_input.val() === 'null') {
                        jo0_phone_input.val('-'); // Set the visual part to '-'
                        controls.jo0_main_phone_number.set_value('+971-'); // Clean the internal state
                    }
                }
                // If project was in draft, re-fetch floor details to populate the options
                if (is_project_in_draft && controls.unit_floor) {
                     frappe.call({
                        method: "joel_living.custom_lead.get_project_floor_details",
                        args: { project_name: values.project },
                        callback: function(r) {
                            if (r.message && controls.unit_floor) {
                                 // (Your existing floor fetching logic here...)
                                 const details = r.message;
                                 let numbered_floor_count = details.no_of_floors || 0;
                                 const has_mezzanine = details.include_mezzanine_floor;
                                 const has_ground_floor = details.include_ground_floor;
                                 let floor_options = [];
                                 if (has_ground_floor) { floor_options.push('G'); numbered_floor_count--; }
                                 if (has_mezzanine) { floor_options.push('M'); numbered_floor_count--; }
                                 if (numbered_floor_count < 0) { numbered_floor_count = 0; }
                                 for (let i = 1; i <= numbered_floor_count; i++) { floor_options.push(String(i)); }
                                 controls.unit_floor.df.options = floor_options;
                                 controls.unit_floor.refresh();
                                 if (values.unit_floor) controls.unit_floor.set_value(values.unit_floor);
                            }
                        }
                     });
                }
            }, 300);
            // Secondary load for dynamically created Joint Owner fields
            // Secondary load for dynamically created Joint Owner fields
           // ... inside the load_draft function ...

            // Secondary load for dynamically created Joint Owner fields
            setTimeout(() => {
                for (let key in values) {
                    // This specifically targets the dynamic fields that start with 'jo'
                    if (key.startsWith('jo') && controls[key] && controls[key].set_value) {
                        const control = controls[key];
                        let value_to_set = String(values[key] || '');
                        // console.log("value_to_set", value_to_set);
                        // Local visual cleanup check
                        if (String(value_to_set).toLowerCase() === 'null') {
                            value_to_set = '';
                        }
                        
                        // *** JOINT OWNER PHONE SPECIFIC VISUAL FIX ***
                        if (control.fieldtype === 'Phone' && (value_to_set === '' || value_to_set === 'null')) {
                            // Set with the desired visual prefix, and then ensure the visual input is clean
                            control.set_value('');              // internal value is empty (not '+971-')
                            $(control.input).val('');          // visible text empty (we'll use addon to show +971 and maybe a placeholder)
                            $(control.input).attr('placeholder', '-');
                        } else {
                            // For all other JO fields (Names, Passport, Country), use the stored string value
                            control.set_value(value_to_set);
                        }
                    }
                }
                if(controls.screened_before_payment) $(controls.screened_before_payment.input).trigger('change');
            }, 800); // MODIFIED: Changed timeout from 400ms to 800ms for reliability.
            loaded = true;
        } else {
             // Logic for a new, clean dialog when no draft exists
             setTimeout(() => {
                if (controls.first_name) controls.first_name.set_value(lead.first_name);
                if (controls.last_name) controls.last_name.set_value(lead.last_name || lead.lead_name);
                if (controls.email) controls.email.set_value(lead.email_id);
                if (controls.main_phone_number && !controls.main_phone_number.get_value()) {
                    controls.main_phone_number.set_value('+971-');
                }
                if (controls.country_of_residence) controls.country_of_residence.set_value(lead.country);
                if (controls.extra_joint_owners) controls.extra_joint_owners.set_value('0');
                if (controls.screened_before_payment) controls.screened_before_payment.set_value('');
                render_dynamic_fields();
            }, 300);
        }
        return loaded;
    };
   
    const add_receipt_row = (draft_data = {}) => {
        receipts_data.push({
            receipt_date: draft_data.receipt_date || '',
            receipt_amount: draft_data.receipt_amount || '',
            receipt_proof: draft_data.receipt_proof || ''
        });
        render_receipt_rows(); // Re-render the HTML after adding new row
    };
   
    const handle_input_change = ($input, row_index) => {
        const field_name = $input.data('fieldname');
        // Update the central JavaScript array which acts as the data source
        if (receipts_data[row_index]) {
            receipts_data[row_index][field_name] = $input.val();
        }
    };
   
    // Ensure this helper function is in your script's scope
const getFileName = (url) => {
    if (!url) return '';
    return url.substring(url.lastIndexOf('/') + 1) || url;
}
// --- FINAL Corrected Core Custom Rendering Function with Link View ---
const render_receipt_rows = () => {
    const $placeholder = wrapper.find('#receipts_table_placeholder');
    $placeholder.empty();
    let table_html = `
        <table class="table table-bordered frappe-list-sidebar custom-receipt-table" style="margin-top:15px; background: white;">
            <thead>
                <tr>
                    <th style="width: 25%">Date</th>
                    <th style="width: 25%">Amount (AED)</th>
                    <th style="width: 35%">Proof of Payment</th>
                    <th style="width: 15%">Actions</th>
                </tr>
            </thead>
            <tbody>`;
    if (receipts_data.length === 0) {
         table_html += `<tr class="no-data-row"><td colspan="4" class="text-muted text-center" style="font-style: italic;">No receipts added.</td></tr>`;
    }
    receipts_data.forEach((row, index) => {
        const date_val = row.receipt_date || '';
        const amount_val = row.receipt_amount || '';
        const proof_val = row.receipt_proof || '';
       
        const file_name_display = getFileName(proof_val);
        // --- NEW: HTML for File/Link display ---
        let file_display_html;
        if (proof_val) {
            // If proof_val exists, render a clickable hyperlink
            // The file path stored is typically an internal Frappe path like /files/image.png
            // We prepend '/' just in case to ensure it's treated as a root path, and set target=_blank
            const full_file_url = proof_val.startsWith('/') ? proof_val : ('/' + proof_val);
           
            file_display_html = `
                <div style="margin-bottom: 5px;">
                    <a href="${full_file_url}" target="_blank" class="receipts-file-link">${file_name_display}</a>
                </div>
            `;
        } else {
            // Otherwise, render a read-only empty label
            file_display_html = `<input type="text" readonly class="form-control input-sm receipts-file-label" value="">`;
        }
        table_html += `
            <tr data-index="${index}">
                <td><input type="date" class="form-control input-sm receipts-input receipts-date" data-fieldname="receipt_date" value="${date_val}" ></td>
                <td><input type="number" min="0" class="form-control input-sm receipts-input receipts-amount" data-fieldname="receipt_amount" value="${amount_val}"></td>
                <td>
                    <div class="input-group">
                         ${file_display_html}
                         <span class="input-group-btn" style="position: absolute; right: 0; top: 0;">
                            <button class="btn btn-sm btn-default add-file-btn" data-fieldname="receipt_proof" type="button" data-index="${index}">Attach</button>
                         </span>
                         <!-- Hidden field to hold the actual URL/path -->
                         <input type="hidden" class="receipts-proof" data-fieldname="receipt_proof" value="${proof_val}">
                    </div>
                </td>
                <td>
                    <button class="btn btn-xs btn-danger delete-row-btn" data-index="${index}">Delete</button>
                </td>
            </tr>
        `;
    });
    table_html += `</tbody></table>
                    <button class="btn btn-sm btn-default add-custom-row-btn">Add Row</button>`;
    $placeholder.html(table_html);
   
    // --- Re-attach All Event Handlers ---
    $placeholder.find('.add-custom-row-btn').off('click').on('click', () => add_receipt_row());
   
    $placeholder.find('.delete-row-btn').off('click').on('click', function() {
        const index = parseInt($(this).data('index'));
        receipts_data.splice(index, 1);
        render_receipt_rows();
    });
   
    // Update central data array on change
    $placeholder.find('.receipts-input').off('change.sync blur.sync').on('change.sync blur.sync', function() {
        const $input = $(this);
        const index = parseInt($input.closest('tr').data('index'));
        handle_input_change($input, index);
    });
   
    // --- START: FINAL CORRECTED UPLOAD LOGIC ---
// Logic for attach button using the modern FileUploader's correct method
$placeholder.find('.add-file-btn').off('click').on('click', function() {
    const $btn = $(this);
    const index = parseInt($btn.data('index'));

    // 1. Instantiate the FileUploader with its configuration
    const uploader = new frappe.ui.FileUploader({
        // Define restrictions
        restrictions: {
            allowed_file_types: ['.pdf', '.jpg', '.jpeg', '.png'],
        },
        
        // Define the callback for when the upload succeeds
        on_success: (file_doc) => {
            if (file_doc && file_doc.file_url) {
                // Update our central data array with the new file URL
                receipts_data[index].receipt_proof = file_doc.file_url;
                
                // Re-render the table to show the new file link
                render_receipt_rows();
            }
        },

        // Optional: handle errors if the upload fails for some reason
        on_error: () => {
             frappe.msgprint(__('There was an error uploading your file. Please try again.'));
        }
    });

    // 2. THIS IS THE CORRECT METHOD CALL
    // It handles the entire "browse -> select -> upload" flow.
    // uploader.browse_and_upload();
});
};
    
const setup_uae_phone_data_control = (control) => {
    const $input = $(control.input);
    const prefix = '+971';

    // Use a timeout to ensure the control is fully rendered in the DOM
    setTimeout(() => {
        let $input_group = $input.parent().is('.input-group') ? $input.parent() : null;

        if (!$input_group) {
             $input.wrap('<div class="input-group"></div>');
             $input_group = $input.parent();
        }

        // Prevent adding the prefix addon multiple times
        if ($input_group.find('.input-group-addon').length === 0) {
            const $addon = $(`<span class="input-group-addon" style="font-weight: bold; background-color: #f7f9fa; padding: 4px;">${prefix}</span>`);
            $input.before($addon);
        }

        // --- START: DEFINITIVE FIX ---
        // Store the original set_value function to call it internally
        const original_setter = control.set_value.bind(control);

        // 1. Override the 'set_value' function
        // This controls how data is DISPLAYED to the user.
        control.set_value = function(value) {
            let display_value = '';
            // Check if the value being set (e.g., from a draft) contains the prefix
            if (value && typeof value === 'string' && value.startsWith(prefix)) {
                // If it does, strip the prefix before showing it in the input box.
                display_value = value.substring(prefix.length);
            } else {
                // Otherwise, use the value as is (handles nulls, etc.)
                display_value = value || '';
            }
            // Use the original function to physically set the text in the input box.
            original_setter(display_value);
        };

        // 2. Override the 'get_value' function
        // This controls what data is SAVED.
        control.get_value = function() {
            // Get only the digits the user has typed from the input box.
            const input_val = $input.val() ? $input.val().trim() : '';

            // If the input box is empty, return an empty string.
            // This is the CRITICAL part that prevents saving a default value.
            if (!input_val) {
                return '';
            }

            // If the user has typed something, prepend the prefix to form the full number for saving.
            return prefix + input_val;
        };

        // 3. Re-apply the initial value
        // After redefining the functions, we need to format the control's current value correctly.
        // We get the raw, unformatted value that Frappe initially set...
        const raw_value_from_doc = control.doc ? control.doc[control.df.fieldname] : $input.val();
        // ...and then call our NEW set_value function to format it correctly.
        control.set_value(raw_value_from_doc);
        // --- END: DEFINITIVE FIX ---

    }, 100);
};
   
    // **********************************************
    // * Custom Validation Functions
    // **********************************************
   
    const validate_email = (value) => {
        if (!value) return { passed: true, message: '' };
        // Standard basic email regex
        const email_regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!email_regex.test(value)) {
            return { passed: false, message: 'Please enter a valid email address.' };
        }
        return { passed: true, message: '' };
    };
    const validate_dob = (date_string) => {
        if (!date_string) return { passed: true, message: '' };
        const date_of_birth = moment(date_string, 'YYYY-MM-DD');
        const now = moment().startOf('day');
        if (date_of_birth.isAfter(now)) {
            return { passed: false, message: 'Date of Birth cannot be a future date.' };
        }
        return { passed: true, message: '' };
    };
    // Validate Future Date
    const validate_future_date = (date_string) => {
        if (!date_string) return { passed: true, message: '' };
        const now = moment().format('YYYY-MM-DD');
        if (date_string > now) { return { passed: true, message: '' }; }
        return { passed: false, message: 'Expiry Date must be a future date.' };
    };
   
    const validate_passport_chars = (value) => {
        if (!value) return { passed: true, message: '' };
        if (/[^a-zA-Z0-9]/.test(value)) {
            return { passed: false, message: 'Passport Number cannot contain special characters.' };
        }
        return { passed: true, message: '' };
    };

    // NEW: Validate UAE Phone Number (9 digits after +971)
    const validate_uae_phone = (value) => {
        if (!value) return { passed: true, message: '' };
        // Extract digits after +971 (assuming value includes prefix)
        const digits = value.replace(/\D/g, '');
        if (digits.length !== 12 || !digits.startsWith('971')) { // +971 + 9 digits = 12 digits total
            return { passed: false, message: 'UAE phone number must be exactly 9 digits after +971 (e.g., +971501234567).' };
        }
        return { passed: true, message: '' };
    };
    const validate_unit_number = (value) => {
        if (!value) return { passed: true, message: '' };
        // Allows alphanumeric, space, hyphen, and '#'
        if (/[^a-zA-Z0-9\s#\-]/.test(value)) {
            return { passed: false, message: 'Unit Number can only contain letters, numbers, spaces, hyphens, and the "#" symbol.' };
        }
        return { passed: true, message: '' };
    };

    // NEW: Validate Main Phone Number (based on AE country code, 9 digits)
    const validate_main_phone = (value) => {
        if (!value) return { passed: true, message: '' };
        // For Phone field, value includes country code
        const digits = value.replace(/\D/g, '');
        if (digits.length !== 12 || !digits.startsWith('971')) {
            return { passed: false, message: 'Main phone number must be a valid UAE number (9 digits after +971).' };
        }
        return { passed: true, message: '' };
    };
   // **********************************************
// * NEW HELPER: Force File Type Validation
// **********************************************
// *******************************************************************
// * DEFINITIVE HELPER: Force File Type Restrictions on Attach Fields
// *******************************************************************
// NEW: Validate Attachment File Type
const validate_attachment = (file_url) => {
    // This function checks if a given file URL has a valid extension.
    if (!file_url) {
        // If there's no file, it's not this function's job to say it's required.
        // That's handled by the 'reqd' check. So we pass validation here.
        return { passed: true, message: '' };
    }
    
    const allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png'];
    const file_name = file_url.toLowerCase();
    
    const is_valid = allowed_extensions.some(ext => file_name.endsWith(ext));
    
    if (!is_valid) {
        // If the extension is not in our allowed list, fail validation.
        return {
            passed: false,
            message: 'Invalid file type. Only PDF, JPG, and PNG are allowed.'
        };
    }
    
    // If the extension is valid, pass validation.
    return { passed: true, message: '' };
};
const apply_strict_file_validation = (control) => {
    // This function provides two layers of protection:
    // 1. It sets the browser-native 'accept' attribute to filter the file picker dialog.
    // 2. It adds an immediate 'change' event to validate the file in case the user bypasses the filter.

    setTimeout(() => {
        const $file_input = $(control.wrapper).find('input[type="file"]');
        if (!$file_input.length) return; // Exit if the element isn't found

        const allowed_types_string = '.pdf,.jpg,.jpeg,.png';
        const allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png'];

        // --- LAYER 1: NATIVE BROWSER FILTER ---
        // This is the most important first step. It restricts the file selection dialog.
        $file_input.attr('accept', allowed_types_string);

        // --- LAYER 2: JAVASCRIPT VALIDATION BLOCKER ---
        // We bind the event handler directly and immediately.
        $file_input.off('change.filetype_blocker').on('change.filetype_blocker', function(e) {
            if (!this.files || this.files.length === 0) {
                return; // No file was selected
            }

            const file = this.files[0];
            const file_name = file.name.toLowerCase();
            const is_valid = allowed_extensions.some(ext => file_name.endsWith(ext));

            if (!is_valid) {
                // If the file is invalid, show a blocking error and reset the input.
                frappe.msgprint({
                    title: __('Upload Blocked: Invalid File Type'),
                    indicator: 'red',
                    message: __('You can only upload PDF, JPG, or PNG files. The selected file was not uploaded.')
                });
                
                // CRITICAL: This clears the selection and stops the upload cold.
                $(this).val('');
                // This is necessary to ensure the 'change' event fires again if the user
                // tries to upload the same invalid file twice.
                return false;
            }
        });
    }, 250); // A safe delay to ensure the control is fully rendered in the DOM.
};
    // Global validation handler for individual controls - LOCAL ERROR DISPLAY (IMPROVED BLUR/CHANGE HANDLER)
    const attach_validation_onchange = (control, validation_func) => {
        if (!control) return;
       
        let $elements_to_check = [];
        $elements_to_check.push($(control.input));
        if (control.fieldtype === 'Link') { $elements_to_check.push($(control.wrapper).find('.btn-link')); }
        if (control.fieldtype === 'Attach') { $elements_to_check.push($(control.wrapper).find('.attach-button')); }
        if (control.fieldtype === 'Select' || control.fieldtype === 'Phone') { $elements_to_check.push($(control.select) || $(control.input)); }
        // Remove previous handlers to prevent double triggering
        for (const $element of $elements_to_check) {
            $element.off('blur.customvalidate change.customvalidate');
        }
        for (const $element of $elements_to_check) {
            $element.on('blur.customvalidate change.customvalidate', (e) => {
               
                const is_attach = control.fieldtype === 'Attach';
               
                const value = control.get_value();
               
                const result = validation_func(value);
                const $wrapper = $(control.wrapper);
                $wrapper.find('.local-error-message').remove();
               
                // Determine target element for red border
                const $target_border = is_attach ? $wrapper.find('.attach-button').closest('.input-with-feedback') : $(control.input).length ? $(control.input) : $wrapper.find('.control-input');
                $target_border.css('border-color', '');
                if (!result.passed) {
                    $wrapper.append(`<p class="local-error-message" style="color: red; font-size: 11px; margin-top: 5px;">${result.message}</p>`);
                    $target_border.css('border-color', 'red');
                } else {
                     $wrapper.find('.control-label').css('color', 'inherit');
                }
            });
        }
    }
    // **********************************************
   
    // ** CUSTOM CLOSE CONFIRMATION DIALOG FUNCTION **
    const show_custom_close_confirmation = () => {
        save_draft();
       
        const close_dialog = new frappe.ui.Dialog({
            title: __('Close Confirmation'),
            size: 'small',
            fields: [
                {
                    fieldtype: 'HTML',
                    options: `
                        <div style="padding-bottom: 10px;">
                            <h4>${__('Unsaved changes detected. What would you like to do?')}</h4>
                        </div>
                        <div style="margin-top: 20px; text-align: right; width: 100%;">
                            <button id="discard-close-btn" class="btn btn-sm btn-default" style="margin-right: 10px;">
                                ${__('Discard Data & Close')}
                            </button>
                            <button id="save-close-btn" class="btn btn-sm btn-primary">
                                ${__('Save Draft & Close')}
                            </button>
                        </div>
                    `
                }
            ],
            actions: []
        });
        close_dialog.$wrapper.on('click', '#save-close-btn', () => {
            save_draft();
            clearInterval(dialog.draft_saver);
            close_dialog.hide();
            dialog.hide();
        });
        close_dialog.$wrapper.on('click', '#discard-close-btn', () => {
            clear_draft();
            clearInterval(dialog.draft_saver);
            close_dialog.hide();
            dialog.hide();
        });
        if (close_dialog.modal_close) {
             close_dialog.modal_close.off('click').on('click', () => { close_dialog.hide() });
        } else {
             close_dialog.$wrapper.find('.modal-header .close').off('click').on('click', () => { close_dialog.hide() });
        }
       
        close_dialog.show();
    }
    // **********************************************
    const dialog = new frappe.ui.Dialog({
        title: __("Create Sales Registration"),
        size: 'large',
        static: true,
    });
   
    // FIX 1: INCREASE DIALOG WIDTH
    dialog.get_full_width = true;
    dialog.$wrapper.find('.modal-dialog').css({
        'max-width': '90vw',
        'width': '90vw'
    });
    const wrapper = $(dialog.body);
    const alignment_fix_style = `
        <style id="phone-alignment-fix-final">
            .modal-body .frappe-control[data-fieldtype=Phone] .selected-phone {
                /* Neutralize the top:calc(50%...) rule by forcing a top alignment */
                top: 0 !important; /* Forces a high-priority top alignment */
                transform: unset !important;
            }
        </style>
    `;
    if ($('#phone-alignment-fix-final').length === 0) {
         $('head').append(alignment_fix_style);
    }
    // REORGANIZED TABS HTML
    wrapper.html(`
        <div>
            <ul class="nav nav-tabs" role="tablist">
                <li class="nav-item"><a class="nav-link active" data-target="#tab-client" href="#">1. Client Information</a></li>
                <li class="nav-item"><a class="nav-link" data-target="#tab-joint-owners" href="#">2. Joint Owners</a></li>
                <li class="nav-item"><a class="nav-link" data-target="#tab-unit" href="#">3. Unit & Sale Details</a></li>
                <li class="nav-item"><a class="nav-link" data-target="#tab-screening" href="#">4. Screening & KYC</a></li>
                <li class="nav-item"><a class="nav-link" data-target="#tab-remarks" href="#">5. Remarks & Files</a></li>
            </ul>
            <div class="tab-content" style="padding-top: 15px;">
                <!-- 1. Client Information (Main Client only) - 3 COLUMNS -->
                <div class="tab-pane fade show active" id="tab-client" role="tabpanel">
                    <h4>Main Client Details</h4><hr><div class="row"><div class="col-md-4" id="client-col-1"></div><div class="col-md-4" id="client-col-2"></div><div class="col-md-4" id="client-col-3"></div><div class="col-md-12" id="client-col-4"></div></div>
                </div>
                <!-- 2. Joint Owners (Dedicated Tab) -->
                <div class="tab-pane fade" id="tab-joint-owners" role="tabpanel">
                    <h4>Joint Owners</h4><hr><div id="joint-owners-section"></div>
                </div>
                <!-- 3. Unit & Sale Details - NOW 3 COLUMNS -->
                <div class="tab-pane fade" id="tab-unit" role="tabpanel">
   
    <!-- This row is for the 3 columns of controls -->
    <div class="row">
        <div class="col-md-4" id="unit-col-1"></div>
        <div class="col-md-4" id="unit-col-2"></div>
        <div class="col-md-4" id="unit-col-3"></div>
    </div>
   
    <!-- START OF FIX: Add new full-width placeholders below the row -->
    <div id="receipts_section_placeholder"></div>
    <div id="receipts_table_placeholder"></div>
    <!-- END OF FIX -->
</div>
               
                <!-- 4. Screening & KYC (IMPROVED COMPACT LAYOUT) -->
                <div class="tab-pane fade" id="tab-screening" role="tabpanel">
                    <h4>Client Screening</h4><hr>
                    
                    <!-- MASTER ROW with 4 columns: Field 1 (Always Visible), Field 2/3 (Mutually Exclusive), Field 4 (Visible on No), Field 5 (Visible on No) -->
                    <div class="row">
                        <!-- 1. Main Select (Always visible - col-md-3) -->
                        <div class="col-md-5" id="screen-q-col"></div> 
                        
                        <!-- 2 & 3. MUTUALLY EXCLUSIVE COLUMN (col-md-3) -->
                        <div class="col-md-4">
                            <div id="screen-yes-attach-wrap"></div> <!-- Inner div for Screenshot of green light -->
                            <div id="screen-no-date-wrap"></div>  <!-- Inner div for Date/time of screening -->
                        </div>

                        <!-- 4. NO Conditional Select Field (col-md-3) -->
                        <div class="col-md-3" id="screen-no-result-col"></div> 

                        <!-- 5. NO Conditional Attach Field (col-md-3) -->
                        <div class="col-md-4" id="screen-no-attach-col"></div> 
                        
                    </div>
                    
                    <!-- FULL-WIDTH REASON FIELD (Conditional on "No", sits on new line) -->
                    <div id="screening-reason-row" class="row mt-2" style="display:none;">
                        <div class="col-md-12" id="screen-reason-col"></div>
                    </div>
                   

                    <h4 class="mt-4">Main Client KYC Uploads</h4><hr>
                    <!-- Main Client KYC: Refactored to 2-column layout -->
                    <div id="main-kyc-placeholder" class="row">
                        <div class="col-md-6" id="main-kyc-col-1"></div>
                        <div class="col-md-6" id="main-kyc-col-2"></div>
                    </div>

                    <h4 class="mt-4">Joint Owners KYC Uploads</h4><hr><div id="joint-owners-kyc-placeholder"></div>
                </div>
                <!-- 5. Remarks & Files -->
                <div class="tab-pane fade" id="tab-remarks" role="tabpanel">
                    <div class="row">
                        <div class="col-md-6" id="remarks-col-1"></div> <!-- for remark_title -->
                        <div class="col-md-6" id="remarks-col-2"></div> <!-- for remark_files -->
                    </div>
                    
                    <!-- Description on a separate row (Full Width) -->
                    <div id="remarks-description-section"></div>                
                <h4 class="mt-4">Additional Files (Optional)</h4><hr><div id="files-section" class="row"><div class="col-md-6"></div><div class="col-md-6"></div></div></div>
            </div>
        </div>
    `);
   
    const make_control = (df, parent_id) => {
        const parent_element = wrapper.find(`#${parent_id}`);
        if (!parent_element.length) return;
        const control = frappe.ui.form.make_control({ df, parent: parent_element, render_input: true });
        controls[df.fieldname] = control;
        if (['Currency', 'Float', 'Int'].includes(df.fieldtype)) {
            setTimeout(() => {
                const $input = $(control.input);
                const MAX_DIGITS = 15;         // Max 15 characters
                const MAX_VALUE = 100000000000; // Max 100 Billion

                // A. Block "e", "+", "-" (Prevents scientific notation input)
                $input.on('keydown', function(e) {
                    if (['e', 'E', '+'].includes(e.key)) {
                        e.preventDefault();
                    }
                });

                // B. Validate on Input (Restrict length)
                $input.on('input', function() {
                    let val = $(this).val().toString();
                    // Remove 'e' or '+' if they somehow got pasted in
                    if (val.includes('e') || val.includes('+')) {
                        val = val.replace(/[eE\+]/g, '');
                        $(this).val(val);
                    }
                    // Cut off if too long
                    if (val.length > MAX_DIGITS) {
                         $(this).val(val.slice(0, MAX_DIGITS));
                    }
                });

                // C. Validate on Change (Check Value)
                $input.on('change blur', function() {
                    let val = parseFloat(control.get_value()) || 0;
                    if (val > MAX_VALUE) {
                        frappe.show_alert({ message: 'Reached maximum limit', indicator: 'orange' });
                        control.set_value(0); // Reset to 0 or set to MAX_VALUE
                    }
                });
            }, 100);
        }
        if (['Date', 'Datetime'].includes(df.fieldtype)) {
            setTimeout(() => {
                // Check if Frappe has initialized the datepicker object
                if (control.datepicker && control.datepicker.opts) {
                    const $input = $(control.input);
                    
                    // When clicked or focused, check screen position
                    $input.on('click focus', function() {
                        const rect = this.getBoundingClientRect();
                        const window_height = window.innerHeight;
                        const space_below = window_height - rect.bottom;
                        
                        // If less than 320px space below, force calendar to show on TOP
                        // standard calendar height is around ~280px-300px
                        if (space_below < 320) {
                            control.datepicker.opts.position = 'top left';
                        } else {
                            control.datepicker.opts.position = 'bottom left';
                        }
                    });
                }
            }, 500); // Slight delay to ensure Datepicker is fully loaded
        }


        if (df.fieldtype === 'Link') {
            setTimeout(() => {
                // Locate the label inside this specific control
                const $label = $(control.wrapper).find('.control-label');
                
                // Only add if not already added (safety check)
                if ($label.find('.link-icon-hint').length === 0) {
                    $label.append(`
                        <span class="link-icon-hint" style="margin-left: 6px; color: #8d99a6; font-size: 12px; cursor: pointer;">
                            <i class="fa fa-chevron-circle-down" title="Select from options"></i>
                        </span>
                    `);
                    
                    // Bonus: Make clicking the icon focus the field (opens the dropdown)
                    $label.find('.link-icon-hint').on('click', () => {
                        if (control.input) $(control.input).focus();
                    });
                }
            }, 100); // Slight delay ensures HTML is rendered
        }
        if (df.fieldtype === 'Attach') {
            const clean_attach_display = () => {
                setTimeout(() => {
                    const $wrapper = $(control.wrapper);

                    // A. HIDE 'Reload File' BUTTON ---------------------
                    // We search for 'a' tags or buttons that contain the exact text "Reload File"
                    $wrapper.find('a, button, span').filter(function() {
                        return $(this).text().trim() === "Reload File";
                    }).hide();
                    // --------------------------------------------------

                    // B. CLEAN FILENAME (Your existing logic) ----------
                    const $link = $wrapper.find('.attached-file-link, a[target="_blank"]');
                    $link.each(function() {
                        const $this = $(this);
                        const url = $this.attr('href'); 
                        const current_text = $this.text();
                        
                        if (url) {
                            let filename = decodeURIComponent(url.split('/').pop().split('?')[0]);
                            if (current_text !== filename) {
                                $this.text(filename);
                            }
                        }
                    });
                }, 200); 
            };

            // Trigger cleanup on Load, Change, and Upload events
            const original_set_value = control.set_value.bind(control);
            control.set_value = function(value) {
                original_set_value(value);
                clean_attach_display();
            };
            $(control.wrapper).on('click change', '.attach-btn, .remove-btn', clean_attach_display);
            
            // Initial Run
            clean_attach_display();
        }
        return control;
    };
   
    // **********************************************
    // * Main Client Field Creation
    // **********************************************
    // Client Col 1
    make_control({ fieldname: 'form_type', label: 'Type of Register', fieldtype: 'Select', reqd: 1, options: ['Expression of Interest (EOI)', 'Completed Sale'] }, 'client-col-1');
    make_control({ fieldname: 'first_name', label: 'First Name', fieldtype: 'Data', reqd: 1 }, 'client-col-1');
    make_control({ fieldname: 'last_name', label: 'Last Name', fieldtype: 'Data', reqd: 1 }, 'client-col-1');
    const main_email_control = make_control({ fieldname: 'email', label: 'Email', fieldtype: 'Data', options: 'Email', reqd: 1 }, 'client-col-1');
    attach_validation_onchange(main_email_control, validate_email);
const dob_control = make_control({ fieldname: 'date_of_birth', label: 'Date of Birth', fieldtype: 'Date', reqd: 1 }, 'client-col-1');
    attach_validation_onchange(dob_control, validate_dob);    // Client Col 2
    const main_phone_control = make_control({
        fieldname: 'main_phone_number',
        label: 'Main Phone Number',
        fieldtype: 'Phone',
        reqd: 1,
        options: {
            onlyCountries: ['ae'],
            initialCountry: 'ae',
            separateDialCode: true
        }
    }, 'client-col-2');
   
    // *** FIX: FORCE +971- VALUE IMMEDIATELY AFTER CREATION FOR VISUAL DEFAULT ***
    setTimeout(() => {
        if (main_phone_control && !main_phone_control.get_value()) {
            main_phone_control.set_value('+971-');
        }
    }, 100);
    // --------------------------------------------------------------------------
    // NEW: Attach phone validation for main_phone_number
    attach_validation_onchange(main_phone_control, validate_main_phone);
    
    // --------------------------------------------------------------------------
    // NEW: Prevent browser hang on _ or other special characters in mobile number
    // main_phone_control.input.on('input', e => {
    //     const inputVal = e.target.value;
    //     const isSpecialChar = inputVal.match(/[^a-zA-Z0-9\+\-\(\)\s]/g);
    //     if (isSpecialChar) {
    //         e.target.value = inputVal.replace(/[^a-zA-Z0-9\+\-\(\)\s]/g, '');
    //     }
    // });
    // --------------------------------------------------------------------------
    // Prevent error: TypeError: Cannot read properties of undefined (reading 'on')
    if (main_phone_control && main_phone_control.input) {
    main_phone_control.input.on('input', function(e) {
        // Get the current value from the input field
        const currentValue = $(this).val();

        // Sanitize the value by removing all characters that are not digits or a plus sign.
        // This is a much safer and more efficient way to clean phone number input.
        const sanitizedValue = currentValue.replace(/[^0-9+]/g, '');

        // CRITICAL: Only update the input field's value if it has actually changed.
        // This check is what prevents the infinite loop and browser freeze.
        if (currentValue !== sanitizedValue) {
            $(this).val(sanitizedValue);
        }
    });
}

    // --------------------------------------------------------------------------
    // NEW: Attach phone validation for main_phone_number
    // attach_validation_onchange(main_phone_control, validate_main_phone);

    const uae_phone_control = make_control({ fieldname: 'uae_phone_number', label: 'UAE Phone Number', fieldtype: 'Data', description: 'Fixed to +971 for UAE' }, 'client-col-2');
    setup_uae_phone_data_control(uae_phone_control);
    // NEW: Attach UAE phone validation
    attach_validation_onchange(uae_phone_control, validate_uae_phone);
   
    const passport_num_control = make_control({ fieldname: 'passport_number', label: 'Passport Number', fieldtype: 'Data', reqd: 1 }, 'client-col-2');
    attach_validation_onchange(passport_num_control, validate_passport_chars);
   
    const passport_expiry_control = make_control({ fieldname: 'passport_expiry_date', label: 'Passport Expiry Date', fieldtype: 'Date', reqd: 1 }, 'client-col-2');
    attach_validation_onchange(passport_expiry_control, validate_future_date);
   
const passport_copy_control = make_control({ fieldname: 'passport_copy', label: 'Passport Copy (PDF/JPG/PNG)', fieldtype: 'Attach', reqd: 1 }, 'client-col-2');
attach_validation_onchange(passport_copy_control, validate_attachment);
    // Client Col 3
    const country_origin_control = make_control({ fieldname: 'country_of_origin', label: 'Country of Origin', fieldtype: 'Link', options: 'Country', reqd: 1 }, 'client-col-3');
    attach_validation_onchange(country_origin_control, (v) => ({ passed: v, message: 'Country is required' }));
   
    const country_residence_control = make_control({ fieldname: 'country_of_residence', label: 'Country of Residence', fieldtype: 'Link', options: 'Country', reqd: 1 }, 'client-col-3');
    attach_validation_onchange(country_residence_control, (v) => ({ passed: v, message: 'Country is required' }));
   
    make_control({ fieldname: 'age_range', label: 'Age Range', fieldtype: 'Select', options: ['\n21–29', '30–45', '46–55', '56–70', '+70'], reqd: 1 }, 'client-col-3');
    make_control({ fieldname: 'yearly_estimated_income', label: 'Yearly Estimated Income (AED)', fieldtype: 'Currency', reqd: 1 }, 'client-col-3');
   
    // Client Col 4 (12 column address fields)
    make_control({ fieldname: 'home_address', label: 'Home Address', fieldtype: 'Small Text', reqd: 1 }, 'client-col-4');
    make_control({ fieldname: 'uae_address', label: 'Address in UAE (Optional)', fieldtype: 'Small Text' }, 'client-col-4');
   
    // Unit Details fields...
    make_control({ fieldname: 'unit_sale_type', label: 'Unit Category', fieldtype: 'Select', reqd: 1, options: ['Off-Plan', 'Secondary'] }, 'unit-col-1');
    const developer_control = make_control({ 
        fieldname: 'developer', 
        label: 'Developer', 
        fieldtype: 'Link', 
        options: 'Developer', 
        reqd: 1 
    }, 'unit-col-1');
    const project_control = make_control({
        fieldname: 'project',
        label: 'Project',
        fieldtype: 'Link',
        options: 'Project List',
        reqd: 1,
        onchange: () => {
            const project_name = project_control.get_value();
            const unit_floor_control = controls['unit_floor'];
            unit_floor_control.set_value("");
            unit_floor_control.df.options = [];
            unit_floor_control.refresh();
            if (!project_name) { return; }
            frappe.call({
                method: "joel_living.custom_lead.get_project_floor_details",
                args: { project_name: project_name },
                callback: function(r) {
                    if (r.message) {
                        const details = r.message;
                        const number_of_floors_raw = details.no_of_floors || 0;
                        const has_mezzanine = details.include_mezzanine_floor;
                        const has_ground_floor = details.include_ground_floor;
                       
                        let floor_options = [];
                        let numbered_floor_count = number_of_floors_raw;
                        if (has_ground_floor) { floor_options.push('G'); numbered_floor_count--; }
                        if (has_mezzanine) { floor_options.push('M'); numbered_floor_count--; }
                       
                        if (numbered_floor_count < 0) { numbered_floor_count = 0; }
                        for (let i = 1; i <= numbered_floor_count; i++) { floor_options.push(String(i)); }
                        unit_floor_control.df.options = floor_options;
                        unit_floor_control.refresh();
                    }
                }
            });
        }
    }, 'unit-col-1');
    make_control({ fieldname: 'unit_floor', label: 'Unit Floor', fieldtype: 'Select', reqd: 1 }, 'unit-col-1');
    make_control({ fieldname: 'unit_view', label: 'Unit View', fieldtype: 'Data', reqd: 1 }, 'unit-col-1');
   
    // Unit Col 2
    const dev_sales_rep_control = make_control({ 
        fieldname: 'developer_sales_rep', 
        label: 'Developer Sales Representative', 
        fieldtype: 'Link', 
        // IMPORTANT: Ensure this is the correct name of the Child DocType in your system.
        options: 'Multiselect Sales Representative' 
    }, 'unit-col-2');

    // --- START: DYNAMIC FILTERING LOGIC ---
    dev_sales_rep_control.df.get_query = function() {
    const developer_name = developer_control.get_value() || "";

    return {
        query: 'joel_living.lead_permission.search_sales_reps',
        filters: { parent: developer_name }
    };
};

   
const unit_number_control = make_control({ fieldname: 'unit_number', label: 'Unit Number', fieldtype: 'Data', reqd: 1 }, 'unit-col-2');
    attach_validation_onchange(unit_number_control, validate_unit_number); 
        make_control({ fieldname: 'unit_type', label: 'Unit Type (e.g., 1BR, Studio)', fieldtype: 'Data', reqd: 1 }, 'unit-col-2');
    make_control({ fieldname: 'unit_price', label: 'Unit Price (AED)', fieldtype: 'Currency', reqd: 1 }, 'unit-col-2');
make_control({ fieldname: 'unit_area', label: 'Unit Area (SQFT)', fieldtype: 'Float', reqd: 1, precision: '2' }, 'unit-col-2');    // Unit Col 3
      
    make_control({ fieldname: 'booking_eoi_paid_amount', label: 'Booking/EOI Paid Amount (AED)', fieldtype: 'Currency', reqd: 1 }, 'unit-col-3');
    make_control({ fieldname: 'booking_form_signed', label: 'Booking Form Signed', fieldtype: 'Select', options: ['\nYes', '\nNo'], reqd: 1 }, 'unit-col-3');
    const booking_form_upload_control = make_control({ fieldname: 'booking_form_upload', label: 'Booking Form Upload', fieldtype: 'Attach' }, 'unit-col-3');
attach_validation_onchange(booking_form_upload_control, validate_attachment);
    make_control({ fieldname: 'spa_signed', label: 'SPA Signed', fieldtype: 'Select', options: ['\nYes', '\nNo']}, 'unit-col-3');

const spa_upload_control = make_control({ fieldname: 'spa_upload', label: 'SPA Upload', fieldtype: 'Attach' }, 'unit-col-3');
attach_validation_onchange(spa_upload_control, validate_attachment);

const soa_upload_control = make_control({ fieldname: 'soa_upload', label: 'SOA Upload', fieldtype: 'Attach' }, 'unit-col-3');
attach_validation_onchange(soa_upload_control, validate_attachment);
    // make_control({ fieldname: 'spa_upload', label: 'SPA Upload', fieldtype: 'Attach' }, 'unit-col-3');
    // make_control({ fieldname: 'soa_upload', label: 'SOA Upload', fieldtype: 'Attach' }, 'unit-col-3');
   
    // Receipts Section Title (use HTML instead of unsupported Section Break)
    make_control({
        fieldname: 'receipts_section_title',
        fieldtype: 'HTML',
        options: '<h4 style="margin-top:10px;">Receipts</h4>'
    }, 'receipts_section_placeholder');
    // This creates the table in its correct placeholder.
    // make_control({
    // fieldname: 'receipts',
    // label: 'Receipts',
    // fieldtype: 'Table',
    // fields: [
    // { fieldname: 'receipt_date', label: 'Date', fieldtype: 'Date', in_list_view: 1, reqd: 1 },
    // { fieldname: 'receipt_amount', label: 'Amount (AED)', fieldtype: 'Currency', in_list_view: 1, reqd: 1 },
    // { fieldname: 'receipt_proof', label: 'Proof of Payment', fieldtype: 'Attach', reqd: 1, in_list_view: 1 }
    // ]
    // }, 'receipts_table_placeholder');
   
    // Screening fields...
   // ... (omitting fields up to screening)
   
    // Screening fields... (FIELD ASSIGNMENTS MAPPING TO NEW SHARED COLUMN LAYOUT)
    
    // 1. Main Select Control (3 units)
    const screening_select = make_control({
        fieldname: 'screened_before_payment',
        label: 'Is the client screened by admin before the first payment?',
        fieldtype: 'Select', options: ['', '\nYes', '\nNo'], reqd: 1
    }, 'screen-q-col'); 
    
    // 2. Screenshot Attach Control (3 units - YES CONDITION - placed in wrap)
    const screenshot_attach = make_control({ fieldname: 'screenshot_of_green_light', label: 'Screenshot of green light', fieldtype: 'Attach', reqd: 1 }, 'screen-yes-attach-wrap');
attach_validation_onchange(screenshot_attach, validate_attachment); // <- TARGETING INNER WRAPPER

    // 3. Datetime Field (3 units - NO CONDITION - placed in wrap)
    const screening_date_time = make_control({ 
        fieldname: 'screening_date_time', 
        label: 'Date and time of screening', 
        fieldtype: 'Datetime', 
        reqd: 1 
    }, 'screen-no-date-wrap'); // <- TARGETING INNER WRAPPER

    // 4. Results Select Field (3 units - NO CONDITION)
    const screening_result = make_control({ 
        fieldname: 'screening_result', 
        label: 'Results of screening', 
        fieldtype: 'Select', 
        options: ['\nGreen', '\nRed'], 
        reqd: 1 
    }, 'screen-no-result-col'); 

    // 5. Screenshot Final Attach (3 units - NO CONDITION)
    const final_screenshot_attach = make_control({ fieldname: 'final_screening_screenshot', label: 'Screenshot of final screening result', fieldtype: 'Attach', reqd: 1 }, 'screen-no-attach-col');
attach_validation_onchange(final_screenshot_attach, validate_attachment);
    
    // 6. Reason for Late Screening (Full width - NO CONDITION)
    const reason_for_late_screening = make_control({ 
        fieldname: 'reason_for_late_screening', 
        label: 'Reason for late screening', 
        fieldtype: 'Small Text', 
        reqd: 1 
    }, 'screen-reason-col');


    // CONDITIONAL DISPLAY LOGIC - MUST BE UPDATED FOR NEW WRAPS
    $(screening_select.input).on('change', function() {
        const val = screening_select.get_value();
        const trimmed_val = (val || '').trim();
        const show_yes = (trimmed_val === 'Yes');
        const show_no = (trimmed_val === 'No');
        
        // 1. MUTUALLY EXCLUSIVE COLUMNS (Green Light vs. Date/Time)
        wrapper.find('#screen-yes-attach-wrap').toggle(show_yes); // Only show Yes Attach when 'Yes'
        wrapper.find('#screen-no-date-wrap').toggle(show_no);     // Only show No Datetime when 'No'

        // 2. REMAINING 'NO' COLUMNS
        wrapper.find('#screen-no-result-col').toggle(show_no);  
        wrapper.find('#screen-no-attach-col').toggle(show_no);

        // 3. Reason Row Visibility
        wrapper.find('#screening-reason-row').toggle(show_no);
        
        // 4. Conditional Requirement Flag Setting (Essential for Validation)
        // Set required to 1 only when section is active (important for hidden/disabled validation handling)
        if (screenshot_attach) screenshot_attach.df.reqd = show_yes ? 1 : 0;
        if (screening_date_time) screening_date_time.df.reqd = show_no ? 1 : 0;
        if (screening_result) screening_result.df.reqd = show_no ? 1 : 0;
        if (final_screenshot_attach) final_screenshot_attach.df.reqd = show_no ? 1 : 0;
        if (reason_for_late_screening) reason_for_late_screening.df.reqd = show_no ? 1 : 0;
        
    }).trigger('change');

    // Remarks & Files fields...
    make_control({ fieldname: 'remark_title', label: 'Title', fieldtype: 'Data' }, 'remarks-col-1');
const remark_files_control = make_control({ fieldname: 'remark_files', label: 'Attachments', fieldtype: 'Attach' }, 'remarks-col-2');
attach_validation_onchange(remark_files_control, validate_attachment); 
   make_control({ fieldname: 'remark_description', label: 'Description', fieldtype: 'Small Text' }, 'remarks-description-section');
    make_control({ fieldname: 'file_title', label: 'File Title', fieldtype: 'Data' }, 'files-section .col-md-6:first-child');
const additional_file_upload_control = make_control({ fieldname: 'file_upload', label: 'File Upload', fieldtype: 'Attach' }, 'files-section .col-md-6:last-child');
attach_validation_onchange(additional_file_upload_control, validate_attachment);   
   
    // RENDER DYNAMIC FIELDS
    const render_dynamic_fields = () => {
        // Read the current value of the select control
        const new_count = parseInt(controls.extra_joint_owners.get_value(), 10) || 0;
        const owners_placeholder = wrapper.find('#joint-owners-placeholder');
        const kyc_placeholder = wrapper.find('#joint-owners-kyc-placeholder');
        const current_count = owners_placeholder.find('.panel-group').length;
        if (new_count > current_count) {
            for (let i = current_count; i < new_count; i++) {
                const owner_num = i + 1, prefix = `jo${i}`;
               
                // *** Collapsible Accordion Setup (for Owner Info) ***
                const collapse_id = `jo-collapse-${i}`;
                const owner_section = $(`
                    <div class="panel-group" id="jo-accordion-${i}" role="tablist" aria-multiselectable="true">
                        <div class="panel panel-default">
                            <div class="panel-heading" role="tab" id="heading-${collapse_id}" style="padding: 10px; cursor: pointer; background-color: #f7f9fa; border-bottom: 1px solid #d1d8dd;">
                                 <h5 class="panel-title collapsed" data-toggle="collapse" data-parent="#jo-accordion-${i}" href="#${collapse_id}" aria-expanded="false" aria-controls="${collapse_id}">
                                    <i class="fa fa-user mr-1"></i> Joint Owner ${owner_num} Details
                                    <span class="pull-down">
                                        <i class="fa fa-caret-down panel-collapse-indicator-${collapse_id}"></i>
                                    </span>
                                </h5>
                            </div>
                            <div id="${collapse_id}" class="panel-collapse collapse joint-owner-wrapper" role="tabpanel" aria-labelledby="heading-${collapse_id}" data-idx="${i}" style="padding:15px; border:1px solid #d1d8dd; border-top: none;">
                                <div class="row">
                                    <div class="col-md-4" id="${prefix}_col1"></div>
                                    <div class="col-md-4" id="${prefix}_col2"></div>
                                    <div class="col-md-4" id="${prefix}_col3"></div>
                                    <div class="col-md-12" id="${prefix}_col4"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                `);
                owners_placeholder.append(owner_section);
                
                // * End Collapsible Setup *
                // *** KYC Section Setup (in Screening & KYC Tab) ***
                const kyc_html = $(`<div class="kyc-section joint-owner-kyc-wrapper row mt-3" data-idx="${i}"><div class="col-md-12"><h6>KYC for Joint Owner ${owner_num}</h6></div><div class="col-md-6" id="${prefix}_kyc_date"></div><div class="col-md-6" id="${prefix}_kyc_file"></div></div>`);
                kyc_placeholder.append(kyc_html);
               
                // Column 1
                make_control({ fieldname: `${prefix}_first_name`, label: 'First Name', fieldtype: 'Data', reqd: 1 }, `${prefix}_col1`);
                make_control({ fieldname: `${prefix}_last_name`, label: 'Last Name', fieldtype: 'Data', reqd: 1 }, `${prefix}_col1`);
const jo_email_control = make_control({ fieldname: `${prefix}_email`, label: 'Email', fieldtype: 'Data', options: 'Email', reqd: 1 }, `${prefix}_col1`);
attach_validation_onchange(jo_email_control, validate_email);
const jo_dob_control = make_control({ fieldname: `${prefix}_date_of_birth`, label: 'Date of Birth', fieldtype: 'Date', reqd: 1 }, `${prefix}_col1`);
                attach_validation_onchange(jo_dob_control, validate_dob)                // Column 2
                const jo_phone_control = make_control({
                    fieldname: `${prefix}_main_phone_number`,
                    label: 'Main Phone Number',
                    fieldtype: 'Phone',
                    reqd: 1,
                    options: {
                        onlyCountries: ['ae'],
                        initialCountry: 'ae',
                        separateDialCode: true
                    }
                }, `${prefix}_col2`);
                // Set default +971- for Joint Owner Phone
                setTimeout(() => {
                    if (jo_phone_control) {
                        // $(jo_phone_control.wrapper).find('.input-with-feedback').css({'vertical-align': 'top', 'line-height': 'normal', 'padding': '0px'});
                        // $(jo_phone_control.wrapper).find('.form-control').css('height', '36px');
                        // assign original getter safely
                        jo_phone_control._original_get_value = jo_phone_control.get_value.bind(jo_phone_control);

                        // robust getter: return '' for placeholder/corrupt states (avoid returning null)
                        jo_phone_control.get_value = () => {
                            let val = jo_phone_control._original_get_value();
                            if (val === undefined || val === null) return '';
                            const valString = String(val).trim().toLowerCase();
                            if (valString === 'null' || valString === '+971-' || valString === '+971' || valString.includes('null')) {
                                return '';
                            }
                            return val;
                        };

                        // prefer true-empty internal state — don't set internal to '+971-' placeholder
                        if (!jo_phone_control.get_value()) {
                            jo_phone_control.set_value('');            // internal value empty
                            $(jo_phone_control.input).val('');        // visible input empty; the UI +971 addon will show prefix
                            $(jo_phone_control.input).attr('placeholder', '-'); // optional hint
                        }

    }
}, 50);
                // NEW: Attach main phone validation for joint owner
                // attach_validation_onchange(jo_phone_control, validate_main_phone);

                const jo_uae_phone_control = make_control({ fieldname: `${prefix}_uae_phone_number`, label: 'UAE Phone Number', fieldtype: 'Data', description: 'Fixed to +971 for UAE' }, `${prefix}_col2`);
                setup_uae_phone_data_control(jo_uae_phone_control);
                // NEW: Attach UAE phone validation for joint owner
                attach_validation_onchange(jo_uae_phone_control, validate_uae_phone);
               
                const jo_passport_num_control = make_control({ fieldname: `${prefix}_passport_number`, label: 'Passport Number', fieldtype: 'Data', reqd: 1 }, `${prefix}_col2`);
                attach_validation_onchange(jo_passport_num_control, validate_passport_chars);
               
                const jo_passport_expiry_control = make_control({ fieldname: `${prefix}_passport_expiry_date`, label: 'Passport Expiry Date', fieldtype: 'Date', reqd: 1 }, `${prefix}_col2`);
                attach_validation_onchange(jo_passport_expiry_control, validate_future_date);
               
const jo_passport_copy_control = make_control({ fieldname: `${prefix}_passport_copy`, label: 'Passport Copy (PDF/JPG/PNG)', fieldtype: 'Attach', reqd: 1 }, `${prefix}_col2`);
attach_validation_onchange(jo_passport_copy_control, validate_attachment);                // Column 3
                const jo_country_origin_control = make_control({ fieldname: `${prefix}_country_of_origin`, label: 'Country of Origin', fieldtype: 'Link', options: 'Country', reqd: 1 }, `${prefix}_col3`);
                attach_validation_onchange(jo_country_origin_control, (v) => ({ passed: v, message: 'Country is required' }));
                const jo_country_residence_control = make_control({ fieldname: `${prefix}_country_of_residence`, label: 'Country of Residence', fieldtype: 'Link', options: 'Country', reqd: 1 }, `${prefix}_col3`);
                attach_validation_onchange(jo_country_residence_control, (v) => ({ passed: v, message: 'Country is required' }));
                make_control({ fieldname: `${prefix}_age_range`, label: 'Age Range', fieldtype: 'Select', reqd: 1, options: ['\n21–29', '30–45', '46–55', '56–70', '+70'], reqd: 1 }, `${prefix}_col3`);
                make_control({ fieldname: `${prefix}_yearly_estimated_income`, label: 'Yearly Estimated Income (AED)', fieldtype: 'Currency', reqd: 1 }, `${prefix}_col3`);
                // Column 4 (12 column address)
                make_control({ fieldname: `${prefix}_home_address`, label: 'Home Address', fieldtype: 'Small Text', reqd: 1 }, `${prefix}_col4`);
                make_control({ fieldname: `${prefix}_uae_address`, label: 'Address in UAE (Optional)', fieldtype: 'Small Text' }, `${prefix}_col4`);
               
                // KYC placeholders (in the Screening & KYC Tab)
                const kyc_date_control = make_control({ fieldname: `${prefix}_kyc_date`, label: 'Date of KYC Entry', fieldtype: 'Date', reqd: 1 }, `${prefix}_kyc_date`);
                const kyc_file_control = make_control({ fieldname: `${prefix}_kyc_file`, label: 'KYC File Upload', fieldtype: 'Attach', reqd: 1 }, `${prefix}_kyc_file`);
                attach_validation_onchange(kyc_file_control, validate_attachment);
                // P1 FIX: Attach Live Validation to ALL newly created controls
                const new_owner_controls = [
                    `${prefix}_first_name`, `${prefix}_last_name`, `${prefix}_email`, `${prefix}_date_of_birth`,
                    `${prefix}_main_phone_number`, `${prefix}_uae_phone_number`, `${prefix}_passport_number`,
                    `${prefix}_passport_expiry_date`, `${prefix}_passport_copy`, `${prefix}_country_of_origin`,
                    `${prefix}_country_of_residence`, `${prefix}_age_range`, `${prefix}_yearly_estimated_income`,
                    `${prefix}_home_address`, `${prefix}_uae_address`, `${prefix}_kyc_date`, `${prefix}_kyc_file`
                ];
                new_owner_controls.forEach(key => {
                    if(controls[key]) attachLiveValidation(controls[key]);
                });
               
                // Collapse the section by default
                owner_section.find(`#${collapse_id}`).collapse('hide');
            }
        }
        else if (new_count < current_count) {
            for (let i = new_count; i < current_count; i++) {
                const prefix = `jo${i}`;
                owners_placeholder.find(`#jo-accordion-${i}`).remove();
                kyc_placeholder.find(`.joint-owner-kyc-wrapper[data-idx="${i}"]`).remove();
               
                const fields_to_remove = [
                    `${prefix}_first_name`, `${prefix}_last_name`, `${prefix}_email`, `${prefix}_main_phone_number`, `${prefix}_uae_phone_number`,
                    `${prefix}_passport_number`, `${prefix}_passport_expiry_date`, `${prefix}_date_of_birth`, `${prefix}_passport_copy`,
                    `${prefix}_country_of_origin`, `${prefix}_country_of_residence`, `${prefix}_age_range`, `${prefix}_yearly_estimated_income`,
                    `${prefix}_home_address`, `${prefix}_uae_address`,
                    `${prefix}_kyc_date`, `${prefix}_kyc_file`
                ];
                fields_to_remove.forEach(fieldname => { delete controls[fieldname]; });
            }
        }
    };
    // --- Live validation cleanup (for all field types) ---
function attachLiveValidation(control) {
    const $wrapper = $(control.wrapper);
    const $input = $(control.input);
    // For basic input fields (Data, Date, Int, Float, etc.)
    if (["Data", "Date", "Int", "Float", "Small Text", "Text", "Text Editor", "Datetime", "Currency"].includes(control.df.fieldtype)) {
        $input.off("input.fieldvalidate change.fieldvalidate")
            .on("input.fieldvalidate change.fieldvalidate", function () {
                if ($(this).val() && String($(this).val()).trim() !== "") {
                    $wrapper.find('.field-error').remove();
                    $wrapper.find('.control-input').css('border-color', '');
                    $input.css('border-color', ''); // Ensure input element border is cleared
                }
            });
    }
    // For Select fields
    if (control.df.fieldtype === "Select") {
        $wrapper.find("select").off("change.fieldvalidate").on("change.fieldvalidate", function () {
            if ($(this).val()) {
                $wrapper.find('.field-error').remove();
                $wrapper.find('.select-container').css('border', '');
            }
        });
    }
    // For Link fields
    if (control.df.fieldtype === "Link") {
        // Use a safe onchange for validation error cleanup
        const original_onchange = control.df.onchange;
        control.df.onchange = () => {
            const val = control.get_value();
            if (val && val.trim() !== "") {
                $wrapper.find('.field-error').remove();
                $input.css('border-color', '');
            }
            if(original_onchange) original_onchange();
        };
    }
    // For Attach fields
    if (control.df.fieldtype === "Attach") {
        // Attaching to the `on` call in control, triggered after a successful file attach
        control.$wrapper.off("attachment_add").on("attachment_add", function () {
            $wrapper.find('.field-error').remove();
            $wrapper.find('.attach-button').closest('.input-with-feedback').css('border-color', '');
        });
       
    }
}
    // --- UI EVENT HANDLERS & BUTTONS ---
    // 1. Manually Inject Close Button HTML into Header (Top Right Button)
    const close_button_html = `
        <a href="#" class="btn btn-xs btn-default" id="custom-close-dialog"
           style="position: absolute; right: 15px; top: 12px; color: #1e88e5; border-color: #bbdefb; background-color: #e3f2fd; font-weight: bold; padding: 4px 10px;">
            Close
        </a>`;
    dialog.header.find('.modal-title').closest('.modal-header').append(close_button_html);
   
    // 2. Attach action to the new manual close button - Dual Confirmation (calls functional small dialog)
    dialog.header.find('#custom-close-dialog').on('click', (e) => {
        e.preventDefault();
        show_custom_close_confirmation();
    });
    // This MUST also be updated to ensure the single browser prompt doesn't overwrite your custom dialog on native X-click
    dialog.header.find('.modal-close').off('click').on('click', (e) => {
        e.preventDefault();
        show_custom_close_confirmation();
    });
    // CRITICAL FIX FOR TAB SWITCHING RELIABILITY (Replace default bootstrap logic with custom)
    wrapper.find('.nav-link').on('click', function(e) {
        e.preventDefault();
        const target = $(this).data('target');
        // Remove active class from all links and content
        wrapper.find('.nav-link').removeClass('active');
        wrapper.find('.tab-pane').removeClass('show active');
       
        // Add active class to clicked link and target content
        $(this).addClass('active');
        wrapper.find(target).addClass('show active');
        // Force scroll to top of the dialog after tab change
        frappe.utils.scroll_to(dialog.body, true, 0);
        if (target === '#tab-unit') {
        // Use a timeout to guarantee the tab is visually 'open' before filling its HTML
        setTimeout(() => {
            render_receipt_rows();
        }, 100);
    }
    });
  
    // Dialog cleanup logic
    dialog.on_hide = () => { clearInterval(dialog.draft_saver); };
    dialog.draft_saver = setInterval(save_draft, 3000);
   
    // 3. Define the bottom button (Create Registration) - Primary Action
    dialog.set_primary_action(__("Create Registration"), () => {
    const values = {};
    let first_invalid_control = null;
    let is_valid = true;
     receipts_data = get_receipt_values();
    // Clear any previous error messages and borders
    wrapper.find(".field-error").remove();
    wrapper.find(".local-error-message").remove();
    wrapper.find('input, select, textarea').css('border-color', '');
    wrapper.find('.attach-button').closest('.input-with-feedback').css('border-color', '');
    wrapper.find('.select-container').css('border', '');

    // --- Conditional Required State Check ---
    const screening_status_val = controls.screened_before_payment ? (controls.screened_before_payment.get_value() || '').trim() : '';
    const is_yes_required = screening_status_val === 'Yes';
    const is_no_required = screening_status_val === 'No';

    const YES_FIELDS = ['screenshot_of_green_light'];
    const NO_FIELDS = ['screening_date_time', 'screening_result', 'reason_for_late_screening', 'final_screening_screenshot'];

    // Loop through all controls in dialog (Validation Check)
    for (let key in controls) {
        if (controls[key]) {
            const control = controls[key];
            const value = control.get_value();
            let failed_validation = false;
            let validation_message = "";

            // --- 1. Custom Field Validations ---
            // (This block is already correct and remains unchanged)
            let custom_validation_result = { passed: true, message: "" };
            if (key.endsWith('passport_expiry_date') && value) { custom_validation_result = validate_future_date(value); }
            else if (key.endsWith('passport_number') && value) { custom_validation_result = validate_passport_chars(value); }
            else if ((key === 'date_of_birth' || key.endsWith('_date_of_birth')) && value) { custom_validation_result = validate_dob(value); }
            else if (key === 'unit_number' && value) { custom_validation_result = validate_unit_number(value); }
            else if ((key === 'email' || key.endsWith('_email')) && value) { custom_validation_result = validate_email(value); }
            else if (key === 'final_screening_screenshot' && value) { custom_validation_result = validate_attachment(value); }
            else if (key === 'screenshot_of_green_light' && value) { custom_validation_result = validate_attachment(value); }
            
            else if ((key === 'uae_phone_number' || key.endsWith('_uae_phone_number')) && value) { custom_validation_result = validate_uae_phone(value); }
            else if (key.endsWith('passport_copy') && value) { custom_validation_result = validate_attachment(value); }
            else if (key === 'spa_upload' && value) { custom_validation_result = validate_attachment(value); }
            else if (key === 'soa_upload' && value) { custom_validation_result = validate_attachment(value); }
            else if (key === 'remark_files' && value) { custom_validation_result = validate_attachment(value); }
            else if (key === 'additional_file_upload' && value) { custom_validation_result = validate_attachment(value); }
            else if (key === 'main_client_kyc_file' && value) { custom_validation_result = validate_attachment(value); }
            else if (key === 'booking_form_upload' && value) { custom_validation_result = validate_attachment(value); }
            else if (key === 'jo0_kyc_file' && value) { custom_validation_result = validate_attachment(value); }
            else if (key === 'jo1_kyc_file' && value) { custom_validation_result = validate_attachment(value); }
            else if (key === 'jo2_kyc_file' && value) { custom_validation_result = validate_attachment(value); }
          
            if (!custom_validation_result.passed) {
                failed_validation = true;
                validation_message = custom_validation_result.message;
            }

            // --- 2. Required Field Validation ---
            if (!failed_validation && control.df.reqd) {
                let is_empty = false;
                const trimmed_value = String(value || '').trim();

                if (!value || (Array.isArray(value) && value.length === 0)) {
                    is_empty = true;
                } else if (control.fieldtype === 'Phone' && (trimmed_value === '+971-' || trimmed_value === '+971')) {
                    is_empty = true;
                }

                let should_check_required = true;
                if ((YES_FIELDS.includes(key) && !is_yes_required) || (NO_FIELDS.includes(key) && !is_no_required)) {
                    should_check_required = false;
                }

                if (should_check_required && is_empty) {
                    failed_validation = true;
                    // Get the label (e.g. "Passport Number") from the control definition
                    const field_label = control.df.label || "This field"; 
                    validation_message = `${field_label} is required.`;
                }
            }

            // --- 3. Handle Failure: Apply UI Error ---
            if (failed_validation) {
                is_valid = false;
                const $wrapper = $(control.wrapper);
                $wrapper.find('.field-error, .local-error-message').remove(); // Clear old errors

                const error_html = `<div class="field-error local-error-message" style="color: red; font-size: 11px; margin-top: 5px;">${validation_message}</div>`;

                // --- START: DEFINITIVE FIX FOR ERROR MESSAGE PLACEMENT ---
                if (control.fieldtype === 'Attach') {
                    // For Attach fields, append the error directly to the 'control-input-wrapper'
                    // This ensures it appears right below the attach button and file link.
                    $wrapper.find('.control-input-wrapper').append(error_html);
                } else {
                    // For all other field types, appending to the main wrapper is correct.
                    $wrapper.append(error_html);
                }
                // --- END: DEFINITIVE FIX FOR ERROR MESSAGE PLACEMENT ---

                // This logic for applying the red border is correct.
                const $target_border = (control.fieldtype === 'Attach')
                    ? $wrapper.find('.attach-button').closest('.input-with-feedback')
                    : ($(control.input).length ? $(control.input) : $wrapper.find('.control-input'));

                if (control.fieldtype === 'Select') {
                    $wrapper.find('.select-container').css('border', '1px solid red');
                } else {
                    $target_border.css('border-color', 'red');
                }

                if (!first_invalid_control) {
                    first_invalid_control = control;
                }
            }
            values[key] = value;
        }
    }

    // --- FINAL CHECK AND ACTION ---
    values.receipts = receipts_data;
    if (!is_valid) { // Block submission if validation failed
            const control = first_invalid_control;
            
            // --- NEW/UPDATED FIX: COLLAPSE AND SCROLL/FOCUS LOGIC ---
            if (control) {
                // Check if the field is inside a dynamic joint owner collapsible wrapper
                const joint_owner_wrapper = $(control.wrapper).closest('.joint-owner-wrapper');
                const tab_pane = $(control.wrapper).closest('.tab-pane');
                
                // 1. Show the parent JO collapsible section if needed
                if (joint_owner_wrapper.length) {
                    const collapse_id = joint_owner_wrapper.attr('id');
                    $(`#${collapse_id}`).collapse('show'); // Opens the specific joint owner panel
                }
                
                // 2. Switch to the parent Tab
                if (tab_pane.length) {
                    const tab_id = tab_pane.attr('id');
                    const tab_link = wrapper.find(`.nav-link[data-target="#${tab_id}"]`);
                    if (tab_link.length && !tab_link.hasClass('active')) {
                        tab_link.trigger('click'); // Switches the tab
                    }
                }
            }

            // Scroll and focus on the first invalid field
            setTimeout(() => {
                 if (control) {
                    frappe.utils.scroll_to($(control.wrapper), true, 150);
                    // Use focus on input, otherwise fallback to generic set_focus
                    if (control.input && $(control.input).is(':visible')) control.input.focus();
                    else control.set_focus();
                 }
            }, 500); // Increased timeout to 500ms to allow collapse/tab animation to finish
            return;
        }
        // const confirm_dialog = new frappe.ui.Dialog({
        //     title: __('Confirm Submission'),
        //     fields: [
        //         {
        //             fieldtype: 'HTML',
        //             options: `<h4>${__('Are you sure you want to create the Sales Registration?')}</h4>`
        //         }
        //     ],
        //     primary_action_label: __('Confirm & Submit'),
        //     primary_action: () => {
        //         confirm_dialog.hide();
               
        //         const primary_btn = dialog.get_primary_btn();
        //         primary_btn.prop('disabled', true);
               
        //         console.log('Submitting values:', values);
        //         frappe.call({
        //             method: "joel_living.custom_lead.create_sales_registration",
        //             args: {
        //                 lead_name: me.frm.doc.name,
        //                 data: values,
        //             },
        //             callback: (r) => {
        //                 if (r.message) {
        //                     dialog.hide();
        //                     // clear_draft(); // NEW: Clear draft on success
        //                     me.frm.reload_doc().then(() => {
        //                         // Update custom_lead_status to "Sales Completed"
        //                         me.frm.set_value('custom_lead_status', 'Sales Completed');
        //                         me.frm.save().then(() => {
        //                             // Optionally re-apply/reload to reflect changes
        //                             me.frm.reload_doc();
        //                         }).catch((err) => {
        //                             console.error('Failed to save custom_lead_status:', err);
        //                             frappe.msgprint(__('Failed to update Lead status. Please try again.'));
        //                         });
        //                     });
        //                 }
        //             },
        //             always: () => {
        //                 primary_btn.prop('disabled', false);
        //             },
        //         });
        //     }
        // });


    //      const handle_submission = (action_type) => {
    //     confirm_dialog.hide();

    //     const primary_btn = dialog.get_primary_btn();
    //     primary_btn.prop('disabled', true);

    //     frappe.call({
    //         method: "joel_living.custom_lead.create_sales_registration",
    //         args: {
    //             lead_name: me.frm.doc.name,
    //             data: values,
    //             action: action_type // Pass the chosen action ('save_draft' or 'submit_for_approval')
    //         },
    //         callback: (r) => {
    //             if (r.message) {
    //                 dialog.hide();
    //                 clear_draft(); // Clear draft on success
    //                 me.frm.reload_doc().then(() => {
    //                     me.frm.set_value('custom_lead_status', 'Sales Completed');
    //                     me.frm.save().then(() => {
    //                         me.frm.reload_doc();
    //                     }).catch((err) => {
    //                         console.error('Failed to save custom_lead_status:', err);
    //                         frappe.msgprint(__('Failed to update Lead status. Please try again.'));
    //                     });
    //                 });
    //             }
    //         },
    //         always: () => {
    //             primary_btn.prop('disabled', false);
    //         },
    //     });
    // };
   const handle_submission = (action_type) => {
    // 1. UI LOCKING
    confirm_dialog.hide();
    const primary_btn = dialog.get_primary_btn();
    primary_btn.prop('disabled', true);

    frappe.call({
        method: "joel_living.custom_lead.create_sales_registration",
        args: {
            lead_name: me.frm.doc.name,
            data: values,
            action: action_type
        },
        callback: (r) => {
            if (r.message) {
                dialog.hide();
                clear_draft();
                frappe.msgprint({ title: 'Success', message: 'Registration Created', indicator: 'green' });
                me.frm.reload_doc().then(() => me.frm.save());
            }
        },
        error: (r) => {
            // 2. UI CLEANUP - Hide initial system popup immediately
            frappe.hide_msgprint(true);
            primary_btn.prop('disabled', false);

            // Clear internal highlighting
            wrapper.find('.form-group').removeClass('has-error');
            wrapper.find('.control-input').css('border-color', '');
            wrapper.find('.local-error-message').remove();
            wrapper.find('.field-error').remove();

            // 3. EXTRACT & CLEAN ERROR MESSAGE
            let raw_error = "";
            
            // Attempt to parse _server_messages (which is usually a JSON string ARRAY)
            if (r._server_messages) {
                try {
                    const messages = JSON.parse(r._server_messages);
                    const combined = JSON.parse(messages.join(" ")); // Sometimes it's double-encoded
                    raw_error = combined.message || combined;
                } catch (e) {
                    // Fallback if not valid JSON
                    try {
                        raw_error = JSON.parse(r._server_messages).join(" ");
                    } catch(e2) {
                        raw_error = r.message || "Unknown Error";
                    }
                }
            } else {
                raw_error = r.message || "";
            }

            // STRING HTML: Remove <b>, <strong>, etc for matching
            let clean_error_text = String(raw_error).replace(/<\/?[^>]+(>|$)/g, "");

            // 4. TARGET IDENTIFICATION LOGIC
            let target = null;
            
            // RegEx to capture the number. Matches: "Phone Number +91-955... is invalid"
            const match_val = clean_error_text.match(/Phone Number\s+([0-9+\-\(\)\s]+?)\s+(?:set|is)/i);

            if (match_val && match_val[1]) {
                // Get pure digits from error for comparison (e.g., "91955107870")
                const error_digits = match_val[1].replace(/[^0-9]/g, "");
                const allKeys = Object.keys(controls); 

                for (let key of allKeys) {
                    const control = controls[key];
                    if (!control) continue;
                    if (['Phone', 'Data'].includes(control.df.fieldtype) || key.includes('phone')) {
                        const val = control.get_value();
                        if (!val) continue;
                        
                        const val_digits = String(val).replace(/[^0-9]/g, "");

                        // EXACT MATCH (100% confidence)
                        if (val_digits === error_digits) {
                            target = control;
                            break; 
                        }
                        // SUBSTRING MATCH (Backup, check if length > 5 to avoid tiny matches)
                        if (!target && error_digits.length > 5 && val_digits.includes(error_digits)) {
                            target = control;
                        }
                    }
                }
            }

            // Fallback: Check for field name
            if (!target) {
                const match_field = clean_error_text.match(/field\s+([a-zA-Z0-9_]+)/i);
                if (match_field && match_field[1] && controls[match_field[1]]) {
                    target = controls[match_field[1]];
                }
            }

            // 5. HIGHLIGHT TARGET & DISPLAY ERROR
            if (target) {
                const $wrapper = $(target.wrapper);
                
                // Tabs & Accordion logic
                const $panelCollapse = $wrapper.closest('.panel-collapse');
                if ($panelCollapse.length && !$panelCollapse.hasClass('show')) $panelCollapse.collapse('show');
                
                const tabPane = $wrapper.closest('.tab-pane');
                if (tabPane.length) {
                    const tabId = tabPane.attr('id');
                    const $tabBtn = wrapper.find(`.nav-link[data-target="#${tabId}"]`);
                    if ($tabBtn.length && !$tabBtn.hasClass('active')) $tabBtn.trigger('click');
                }

                // Display logic with small delay
                setTimeout(() => {
                    // A. Scroll & Focus
                    if (target.input) {
                        target.input.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        $(target.input).focus();
                    }

                    // B. Red Border styling
                    $wrapper.closest('.form-group').addClass('has-error');
                    $wrapper.find('input, select, .input-with-feedback').css({
                        'border': '2px solid #d9534f', 
                        'background-color': '#fff5f5'
                    });

                    // C. Inline Error (This was working fine)
                    const display_num = match_val ? match_val[1].trim() : "entered";
                    $wrapper.find('.control-input-wrapper').append(
                        `<div class="local-error-message" style="color:#d9534f; font-size:12px; margin-top:5px; font-weight:bold;">
                             <i class="fa fa-exclamation-circle"></i> Value ${display_num} is invalid.
                        </div>`
                    );

                    // D. GLOBAL ALERT (Fixed: using simple text string)
                    // We don't put HTML in the message to avoid the blank box issue
                    frappe.msgprint({
                        title: __('Validation Failed'), // Explicit title
                        indicator: 'red',
                        message: __('Please check the highlighted field: <b>{0}</b> contains an invalid number.', [target.df.label])
                    });

                }, 350);
            } else {
                // Generic Fallback
                let fallback_msg = clean_error_text
                    .replace(/__frappe_exc_id.*/, '')
                    .replace("frappe.exceptions.InvalidPhoneNumberError:", "")
                    .replace("frappe.exceptions.ValidationError:", "")
                    .trim();

                if (fallback_msg.length < 5) fallback_msg = "Validation Error. Please check your data.";

                frappe.msgprint({
                    title: __('Error'),
                    indicator: 'red',
                    message: fallback_msg
                });
            }
        }
    });
};

    const confirm_dialog = new frappe.ui.Dialog({
        title: __('Confirm Submission'),
        fields: [{
            fieldtype: 'HTML',
            options: `
                <div style="padding-bottom: 10px;">
                    <h4>${__('What would you like to do?')}</h4>
                </div>
                <div style="margin-top: 20px; text-align: right; width: 100%;">
                    <button id="save-draft-btn" class="btn btn-sm btn-default" style="margin-right: 10px;">
                        ${__('Save as Draft')}
                    </button>
                    <button id="submit-approval-btn" class="btn btn-sm btn-primary">
                        ${__('Confirm & Send for Approval')}
                    </button>
                </div>
            `
        }],
        actions: [] // Disable standard footer buttons
    });
confirm_dialog.$wrapper.on('click', '#save-draft-btn', () => {
        handle_submission('save_draft');
    });

    confirm_dialog.$wrapper.on('click', '#submit-approval-btn', () => {
        handle_submission('submit_for_approval');
    });
       
        confirm_dialog.show();
    });
    dialog.show();
    // Create Main Client KYC only ONCE in its own safe placeholder
   make_control({ fieldname: `main_client_kyc_date`, label: 'Date of KYC Entry', fieldtype: 'Date', reqd: 1 }, 'main-kyc-col-1'); // <- CHANGED TARGET ID
const main_kyc_file_control = make_control({ fieldname: `main_client_kyc_file`, label: 'KYC File Upload', fieldtype: 'Attach', reqd: 1 }, 'main-kyc-col-2');
attach_validation_onchange(main_kyc_file_control, validate_attachment);    // Create the joint owner select control and attach its event handler
    const joint_owners_wrapper = wrapper.find('#joint-owners-section');
    joint_owners_wrapper.append('<div class="row"><div class="col-md-4" id="joint-owners-select"></div></div><div id="joint-owners-placeholder"></div>');
    make_control({fieldname: 'extra_joint_owners', label: 'Number of Additional Joint Owners', fieldtype: 'Select', options: '0\n1\n2\n3'}, 'joint-owners-select');
    controls.extra_joint_owners.df.onchange = render_dynamic_fields;
    // P1 FIX: Loop through ALL statically created controls to attach generic live validation for error clearing
    for (let key in controls) {
        if (controls[key]) {
            attachLiveValidation(controls[key]);
        }
    }
   
    // Load initial data trigger (calls load_draft and render_dynamic_fields)
    load_draft();
   
    render_dynamic_fields(); // Final initial render call (runs after initial load for fresh opens)
}























/////////////////////////////////////////////////////////////////////////


    apply_workflow_action(transition) {
        const me = this;
        
     
        
        return new Promise((resolve, reject) => {
            frappe.dom.freeze();
            me.frm.selected_workflow_action = transition.action;

            me.frm.script_manager.trigger("before_workflow_action").then(() => {
                frappe
                    .xcall("frappe.model.workflow.apply_workflow", {
                        doc: me.frm.doc,
                        action: transition.action
                    })
                    .then((doc) => {
                        frappe.model.sync(doc);
                        me.frm.refresh();
                        me.frm.selected_workflow_action = null;
                        me.frm.script_manager.trigger("after_workflow_action");
                        resolve();
                    })
                    .catch((error) => {
                        console.error(error);
                        reject(error);
                    })
                    .finally(() => {
                        frappe.dom.unfreeze();
                    });
            });
        });
    }
}


frappe.ui.form.States = WorkflowOverride;