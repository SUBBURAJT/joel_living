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
                                                        message: __("A Sales Completion Form {0} already exists for this lead and is pending approval.", [`<a href="/app/sales-registration-form/${r.message}" target="_blank">${r.message}</a>`])
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


show_sales_completion_dialog() {
    const me = this;
    const lead = me.frm.doc;
    let controls = {}; 

    // --- DRAFT MANAGEMENT (no change) ---
    const DRAFT_KEY = `sales_reg_draft_${frappe.session.user}_${lead.name}`;
    const save_draft = () => {
        const values = {};
        for (let key in controls) {
            if (controls[key] && controls[key].get_value) {
                const val = controls[key].get_value();
                if (val || key === 'extra_joint_owners' || key === 'unit_floor') { 
                     values[key] = val; 
                }
            }
        }
        if (Object.keys(values).length > 0) {
            localStorage.setItem(DRAFT_KEY, JSON.stringify(values));
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
            
            setTimeout(() => {
                for (let key in values) {
                    if (controls[key] && controls[key].set_value) {
                        controls[key].set_value(values[key]);
                    }
                }
                
                render_dynamic_fields();
                if(controls.screened_before_payment) $(controls.screened_before_payment.input).trigger('change');
            }, 300);
            
            loaded = true;
        } else {
             // NEW/CLEAN: ONLY apply data from the original Lead if no draft exists
             setTimeout(() => {
                if (controls.first_name) controls.first_name.set_value(lead.first_name);
                if (controls.last_name) controls.last_name.set_value(lead.last_name || lead.lead_name);
                if (controls.email) controls.email.set_value(lead.email_id);
                if (controls.main_phone_number) controls.main_phone_number.set_value(lead.mobile_no);
                if (controls.country_of_residence) controls.country_of_residence.set_value(lead.country);
                
                if (controls.extra_joint_owners) controls.extra_joint_owners.set_value('0');
                if (controls.screened_before_payment) controls.screened_before_payment.set_value('');
                
                render_dynamic_fields(); 
            }, 300);

        }

        return loaded;
    };
    
    // Function to set up the Data field to visually appear as a locked +971 phone number
    const setup_uae_phone_data_control = (control) => {
        const $input = $(control.input);
        const prefix = '+971';
        
        setTimeout(() => {
            let $input_group = $input.parent().is('.input-group') ? $input.parent() : null;
            
            if ($input.val() && $input.val().startsWith(prefix)) {
                $input.val($input.val().replace(prefix, ''));
            } else if (!$input.val()) {
                $input.val(''); 
            }
            
            if (!$input_group) {
                 $input.wrap('<div class="input-group" style="width: 100%;"></div>');
                 $input_group = $input.parent();
            }

            const $addon = $(`<span class="input-group-addon" style="font-weight: bold; background-color: #f7f9fa;">${prefix}</span>`);
            $input.before($addon);

            control.get_value = () => {
                let value = $input.val().trim();
                if (value && !value.startsWith(prefix)) {
                    return prefix + value;
                } else if (value.startsWith(prefix)) {
                    return value;
                }
                return '';
            }
        }, 50); 
    }
    
    // **********************************************
    // * Custom Validation Functions (unchanged logic)
    // **********************************************
    const validate_age = (date_string) => {
        if (!date_string) return { passed: true, message: '' };
        try {
            const today = moment();
            const birthDate = moment(date_string);
            const age = today.diff(birthDate, 'years');
            if (age >= 18) { return { passed: true, message: '' }; }
            return { passed: false, message: 'Client must be 18 years or older.' };
        } catch (e) {
            return { passed: false, message: 'Invalid date format for Date of Birth.' };
        }
    };
    
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
    }
    
    // Global validation handler for individual controls - LOCAL ERROR DISPLAY (IMPROVED BLUR/CHANGE HANDLER)
    const attach_validation_onchange = (control, validation_func) => {
        if (!control) return;
        
        let $elements_to_check = [];
        $elements_to_check.push($(control.input)); 
        if (control.fieldtype === 'Link') { $elements_to_check.push($(control.wrapper).find('.btn-link')); } 
        if (control.fieldtype === 'Attach') { $elements_to_check.push($(control.wrapper).find('.attach-button')); }
        if (control.fieldtype === 'Select' || control.fieldtype === 'Phone') { $elements_to_check.push($(control.select) || $(control.input)); }

        for (const $element of $elements_to_check) {
            $element.on('blur change', (e) => { 
                
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
                <div class="tab-pane fade" id="tab-unit" role="tabpanel"><div class="row"><div class="col-md-4" id="unit-col-1"></div><div class="col-md-4" id="unit-col-2"></div><div class="col-md-4" id="unit-col-3"></div></div></div>
                <!-- 4. Screening & KYC (includes Joint Owner KYC) -->
                <div class="tab-pane fade" id="tab-screening" role="tabpanel">
                    <h4>Client Screening</h4><hr><div id="screening-section"></div>
                    <div id="screening-yes-section" class="mt-3" style="display:none;"><div class="row"><div class="col-md-6"></div></div></div>
                    <div id="screening-no-section" class="mt-3" style="display:none;"><div class="row"><div class="col-md-6"></div><div class="col-md-6"></div><div class="col-md-12"></div></div></div>
                    <h4 class="mt-4">Main Client KYC Uploads</h4><hr>
                    <div id="main-kyc-placeholder"></div>
                    <h4 class="mt-4">Joint Owners KYC Uploads</h4><hr><div id="joint-owners-kyc-placeholder"></div>
                </div>
                <!-- 5. Remarks & Files -->
                <div class="tab-pane fade" id="tab-remarks" role="tabpanel"><h4>Remarks (Optional)</h4><hr><div id="remarks-section"></div><h4 class="mt-4">Additional Files (Optional)</h4><hr><div id="files-section" class="row"><div class="col-md-6"></div><div class="col-md-6"></div></div></div>
            </div>
        </div>
    `);
    
    const make_control = (df, parent_id) => {
        const parent_element = wrapper.find(`#${parent_id}`);
        if (!parent_element.length) return;
        const control = frappe.ui.form.make_control({ df, parent: parent_element, render_input: true });
        controls[df.fieldname] = control;
        return control;
    };
    
    // **********************************************
    // * Main Client Field Creation
    // **********************************************
    // Client Col 1
    make_control({ fieldname: 'form_type', label: 'Type of Register', fieldtype: 'Select', reqd: 1, options: ['Expression of Interest (EOI)', 'Completed Sale'] }, 'client-col-1');
    make_control({ fieldname: 'first_name', label: 'First Name', fieldtype: 'Data', reqd: 1 }, 'client-col-1');
    make_control({ fieldname: 'last_name', label: 'Last Name', fieldtype: 'Data', reqd: 1 }, 'client-col-1');
    make_control({ fieldname: 'email', label: 'Email', fieldtype: 'Data', options: 'Email', reqd: 1 }, 'client-col-1');
    const dob_control = make_control({ fieldname: 'date_of_birth', label: 'Date of Birth', fieldtype: 'Date', reqd: 1 }, 'client-col-1');
    attach_validation_onchange(dob_control, validate_age); 

    // Client Col 2
    const main_phone_control = make_control({ fieldname: 'main_phone_number', label: 'Main Phone Number', fieldtype: 'Phone', reqd: 1, options: 'AE' }, 'client-col-2'); 
    
    const uae_phone_control = make_control({ fieldname: 'uae_phone_number', label: 'UAE Phone Number', fieldtype: 'Data', description: 'Fixed to +971 for UAE' }, 'client-col-2'); 
    setup_uae_phone_data_control(uae_phone_control); 
    
    const passport_num_control = make_control({ fieldname: 'passport_number', label: 'Passport Number', fieldtype: 'Data', reqd: 1 }, 'client-col-2'); 
    attach_validation_onchange(passport_num_control, validate_passport_chars); 
    
    const passport_expiry_control = make_control({ fieldname: 'passport_expiry_date', label: 'Passport Expiry Date', fieldtype: 'Date', reqd: 1 }, 'client-col-2');
    attach_validation_onchange(passport_expiry_control, validate_future_date); 
    
    make_control({ fieldname: 'passport_copy', label: 'Passport Copy (PDF/JPG/PNG)', fieldtype: 'Attach', reqd: 1, options: { accepted_file_types: ['.pdf', '.jpg', '.jpeg', '.png'], show_preview: true } }, 'client-col-2');
    
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
    make_control({ fieldname: 'unit_sale_type', label: 'Unit Category', fieldtype: 'Select', options: ['Off-Plan', 'Secondary'], reqd: 1 }, 'unit-col-1');
    make_control({ fieldname: 'developer', label: 'Developer', fieldtype: 'Link', options: 'Developer', reqd: 1 }, 'unit-col-1');
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
    
    // Unit Col 2
    make_control({ fieldname: 'developer_sales_rep', label: 'Developer Sales Representative', fieldtype: 'Link', options: 'User' }, 'unit-col-2');
    make_control({ fieldname: 'unit_number', label: 'Unit Number', fieldtype: 'Data', reqd: 1 }, 'unit-col-2');
    make_control({ fieldname: 'unit_type', label: 'Unit Type (e.g., 1BR, Studio)', fieldtype: 'Data', reqd: 1 }, 'unit-col-2');
    make_control({ fieldname: 'unit_price', label: 'Unit Price (AED)', fieldtype: 'Currency', reqd: 1 }, 'unit-col-2');
    make_control({ fieldname: 'unit_area', label: 'Unit Area (SQFT)', fieldtype: 'Float', reqd: 1 }, 'unit-col-2');

    // Unit Col 3
    make_control({ fieldname: 'unit_view', label: 'Unit View', fieldtype: 'Data', reqd: 1 }, 'unit-col-3');
    make_control({ fieldname: 'unit_floor', label: 'Unit Floor', fieldtype: 'Select', reqd: 1 }, 'unit-col-3');    
    make_control({ fieldname: 'booking_eoi_paid_amount', label: 'Booking/EOI Paid Amount (AED)', fieldtype: 'Currency', reqd: 1 }, 'unit-col-3');
    make_control({ fieldname: 'booking_form_upload', label: 'Booking Form Upload', fieldtype: 'Attach' }, 'unit-col-3');
    make_control({ fieldname: 'spa_upload', label: 'SPA Upload', fieldtype: 'Attach' }, 'unit-col-3');
    make_control({ fieldname: 'soa_upload', label: 'SOA Upload', fieldtype: 'Attach' }, 'unit-col-3');

    // Screening fields... (unchanged)
    const screening_select = make_control({
        fieldname: 'screened_before_payment',
        label: 'Is the client screened by admin before the first payment?',
        fieldtype: 'Select', options: ['', '\nYes', '\nNo'], reqd: 1
    }, 'screening-section');

    make_control({ fieldname: 'screenshot_of_green_light', label: 'Screenshot of green light...', fieldtype: 'Attach', reqd: 1 }, 'screening-yes-section .col-md-6');
    make_control({ fieldname: 'screening_date_time', label: 'Date and time of screening', fieldtype: 'Datetime', reqd: 1 }, 'screening-no-section .col-md-6:first-child');
    make_control({ fieldname: 'screening_result', label: 'Results of screening', fieldtype: 'Select', options: ['\nGreen', '\nRed'], reqd: 1 }, 'screening-no-section .col-md-6:last-child');
    make_control({ fieldname: 'reason_for_late_screening', label: 'Reason for late screening', fieldtype: 'Small Text', reqd: 1 }, 'screening-no-section .col-md-12');
    make_control({ fieldname: 'final_screening_screenshot', label: 'Screenshot of final screening result...', fieldtype: 'Attach', reqd: 1 }, 'screening-no-section .col-md-12');

  
    $(screening_select.input).on('change', function() {
        const val = screening_select.get_value();
        let show_yes = false, show_no = false;
        if (val) {
            const trimmed_val = val.trim();
            if (trimmed_val === 'Yes') { show_yes = true; }
            else if (trimmed_val === 'No') { show_no = true; }
        }
        wrapper.find('#screening-yes-section').toggle(show_yes);
        wrapper.find('#screening-no-section').toggle(show_no);
    });
    // Remarks & Files fields... (unchanged)
    make_control({ fieldname: 'remark_title', label: 'Title', fieldtype: 'Data' }, 'remarks-section');
    make_control({ fieldname: 'remark_description', label: 'Description', fieldtype: 'Small Text' }, 'remarks-section');
    make_control({ fieldname: 'remark_files', label: 'Attachments (up to 3 files)', fieldtype: 'Attach' }, 'remarks-section');
    make_control({ fieldname: 'additional_file_title', label: 'File Title', fieldtype: 'Data' }, 'files-section .col-md-6:first-child');
    make_control({ fieldname: 'additional_file_upload', label: 'File Upload', fieldtype: 'Attach' }, 'files-section .col-md-6:last-child');
    

    
    // RENDER DYNAMIC FIELDS
    const render_dynamic_fields = () => {
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
                                <h5 class="panel-title" data-toggle="collapse" data-parent="#jo-accordion-${i}" href="#${collapse_id}" aria-expanded="true" aria-controls="${collapse_id}">
                                    Joint Owner ${owner_num} Details
                                </h5>
                            </div>
                            <div id="${collapse_id}" class="panel-collapse collapse in joint-owner-wrapper" role="tabpanel" aria-labelledby="heading-${collapse_id}" data-idx="${i}" style="padding:15px; border:1px solid #d1d8dd; border-top: none;">
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
                make_control({ fieldname: `${prefix}_email`, label: 'Email', fieldtype: 'Data', options: 'Email', reqd: 1 }, `${prefix}_col1`);
                
                const jo_dob_control = make_control({ fieldname: `${prefix}_date_of_birth`, label: 'Date of Birth', fieldtype: 'Date', reqd: 1 }, `${prefix}_col1`);
                attach_validation_onchange(jo_dob_control, validate_age); 

                // Column 2
                make_control({ fieldname: `${prefix}_main_phone_number`, label: 'Main Phone Number', fieldtype: 'Phone', reqd: 1, options: 'AE' }, `${prefix}_col2`);

                const jo_uae_phone_control = make_control({ fieldname: `${prefix}_uae_phone_number`, label: 'UAE Phone Number', fieldtype: 'Data', description: 'Fixed to +971 for UAE' }, `${prefix}_col2`);
                setup_uae_phone_data_control(jo_uae_phone_control);
                
                const jo_passport_num_control = make_control({ fieldname: `${prefix}_passport_number`, label: 'Passport Number', fieldtype: 'Data', reqd: 1 }, `${prefix}_col2`);
                attach_validation_onchange(jo_passport_num_control, validate_passport_chars);
                
                const jo_passport_expiry_control = make_control({ fieldname: `${prefix}_passport_expiry_date`, label: 'Passport Expiry Date', fieldtype: 'Date', reqd: 1 }, `${prefix}_col2`);
                attach_validation_onchange(jo_passport_expiry_control, validate_future_date);
                
                make_control({ fieldname: `${prefix}_passport_copy`, label: 'Passport Copy (PDF/JPG/PNG)', fieldtype: 'Attach', reqd: 1, options: { accepted_file_types: ['.pdf', '.jpg', '.jpeg', '.png'], show_preview: true } }, `${prefix}_col2`);

                // Column 3
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
                make_control({ fieldname: `${prefix}_kyc_date`, label: 'Date of KYC Entry', fieldtype: 'Date', reqd: 1 }, `${prefix}_kyc_date`);
                make_control({ fieldname: `${prefix}_kyc_file`, label: 'KYC File Upload', fieldtype: 'Attach', reqd: 1, options: { accepted_file_types: ['.pdf', '.jpg', '.jpeg', '.png'], show_preview: true } }, `${prefix}_kyc_file`);
                
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
    if (["Data", "Date", "Int", "Float", "Small Text", "Text", "Text Editor"].includes(control.df.fieldtype)) {
        $input.off("input.fieldvalidate change.fieldvalidate")
            .on("input.fieldvalidate change.fieldvalidate", function () {
                if ($(this).val() && String($(this).val()).trim() !== "") {
                    $wrapper.find('.field-error').remove();
                }
            });
    }

    // For Select fields
    if (control.df.fieldtype === "Select") {
        $wrapper.find("select").off("change.fieldvalidate").on("change.fieldvalidate", function () {
            if ($(this).val()) {
                $wrapper.find('.field-error').remove();
            }
        });
    }

    // For Link fields — use Frappe's event hooks safely
    if (control.df.fieldtype === "Link") {
        control.df.onchange = () => {
            const val = control.get_value();
            if (val && val.trim() !== "") {
                $wrapper.find('.field-error').remove();
            }
        };
    }

    // For Attach fields
    if (control.df.fieldtype === "Attach") {
        control.$wrapper.off("attach_complete.fieldvalidate").on("attach_complete.fieldvalidate", function () {
            $wrapper.find('.field-error').remove();
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
    });
    
    // Dialog cleanup logic
    dialog.on_hide = () => { clearInterval(dialog.draft_saver); };
    dialog.draft_saver = setInterval(save_draft, 3000);
    
    // 3. Define the bottom button (Create Registration) - Primary Action
    dialog.set_primary_action(__("Create Registration"), () => {
    const values = {};
    let first_invalid_control = null;

    // Clear any previous error messages
    wrapper.find(".field-error").remove();

    // Loop through all controls in dialog
    for (let key in controls) {
        if (controls[key]) {
            const control = controls[key];
            const $input = $(control.input);
            const value = control.get_value();

            // Validate required fields (even in hidden tabs)
            if (control.df.reqd && (value === undefined || value === null || value === "")) {
    const $error = $('<div class="field-error" style="color:red; font-size:12px; margin-top:4px;">This field is required.</div>');
    if (!$(control.wrapper).find(".field-error").length) {
        $(control.wrapper).append($error);
    }

    if (!first_invalid_control) {
        first_invalid_control = control;
    }

    attachLiveValidation(control);  // <--- NEW LINE
}


            values[key] = value;
        }
    }

    // Handle first invalid control
    if (first_invalid_control) {
        const control = first_invalid_control;

        // --- Switch tab if field is inside a tab ---
        const tab_pane = $(control.wrapper).closest('.tab-pane');
        if (tab_pane.length) {
            const tab_id = tab_pane.attr('id');
            const tab_link = wrapper.find(`.nav-link[data-target="#${tab_id}"]`);
            if (tab_link.length && !tab_link.hasClass('active')) {
                tab_link.trigger('click');
            }
        }

        // --- Scroll & focus ---
        frappe.utils.scroll_to($(control.wrapper), true, 150);
        control.set_focus();

        // Stop submission
        frappe.show_alert({
            message: __("Please fill all required fields before proceeding."),
            indicator: "red",
        });

        return;
    }

    // --- If all required fields filled, proceed to backend ---
    const primary_btn = dialog.get_primary_btn();
    primary_btn.prop('disabled', true);
    frappe.call({
        method: "joel_living.custom_lead.create_sales_registration",
        args: {
            lead_name: me.frm.doc.name,
            data: values,
        },
        callback: (r) => {
            if (r.message) {
                localStorage.removeItem(DRAFT_KEY);
                dialog.hide();
                frappe.set_route('Form', 'Sales Completion Form', r.message);
                me.frm.reload_doc();
            }
        },
        always: () => {
            primary_btn.prop('disabled', false);
        },
    });
});




    dialog.show();

    // Create Main Client KYC only ONCE in its own safe placeholder
    make_control({ fieldname: `main_client_kyc_date`, label: 'Date of KYC Entry', fieldtype: 'Date', reqd: 1 }, 'main-kyc-placeholder');
    make_control({ fieldname: `main_client_kyc_file`, label: 'KYC File Upload', fieldtype: 'Attach', reqd: 1, options: { accepted_file_types: ['.pdf', '.jpg', '.jpeg', '.png'], show_preview: true } }, 'main-kyc-placeholder');
    
    // Create the joint owner select control and attach its event handler
    const joint_owners_wrapper = wrapper.find('#joint-owners-section');
    joint_owners_wrapper.append('<div class="row"><div class="col-md-4" id="joint-owners-select"></div></div><div id="joint-owners-placeholder"></div>');
    make_control({fieldname: 'extra_joint_owners', label: 'Number of Additional Joint Owners', fieldtype: 'Select', options: '0\n1\n2\n3'}, 'joint-owners-select');
    controls.extra_joint_owners.df.onchange = render_dynamic_fields;

    // Load initial data trigger (calls load_draft and render_dynamic_fields)
    load_draft();
    
    render_dynamic_fields(); // Final initial render call
}


    // show_sales_completion_dialog(transition) {
    //     const me = this;

    //     // Define all the fields for the dialog based on the Sales Completion Form doctype
    //     const sales_form_fields = [
    //         { fieldname: 'type_register', label: __('Type Register'), fieldtype: 'Select', options: 'EOI\nCompleted Sale', reqd: 1 },
    //         { fieldtype: 'Section Break', label: 'Client(s) Information' },
    //         { fieldname: 'first_name', label: __('First Name'), fieldtype: 'Data' },
    //         { fieldname: 'last_name', label: __('Last Name'), fieldtype: 'Data' },
    //         { fieldname: 'passport_number', label: __('Passport Number'), fieldtype: 'Data' },
    //         { fieldname: 'passport_date_of_expiry', label: __('Passport Date of Expiry'), fieldtype: 'Date' },
    //         { fieldname: 'passport_copy', label: __('Passport Copy'), fieldtype: 'Attach' },
    //         { fieldtype: 'Column Break' },
    //         { fieldname: 'date_of_birth', label: __('Date of Birth'), fieldtype: 'Date' },
    //         { fieldname: 'main_phone_number', label: __('Main Phone Number'), fieldtype: 'Data' },
    //         { fieldname: 'uae_phone_number', label: __('UAE Phone Number'), fieldtype: 'Data' },
    //         { fieldname: 'email', label: __('Email'), fieldtype: 'Data' },
    //         { fieldtype: 'Column Break' },
    //         { fieldname: 'country_of_origin', label: __('Country of Origin'), fieldtype: 'Data' },
    //         { fieldname: 'country_of_residence', label: __('Country of Residence'), fieldtype: 'Data' },
    //         { fieldname: 'extra_joint_owners', label: __('Extra Joint Owners'), fieldtype: 'Select', options: 'No Joint Owners\n1\n2\n3' },
    //         { fieldtype: 'Column Break' },
    //         { fieldname: 'age_range', label: __('Age Range'), fieldtype: 'Select', options: '\n21-29\n30-45\n46-55\n56-70\n+70' },
    //         { fieldname: 'yearly_estimated_income_as_per_kyc', label: __('Yearly Estimated Income (as per KYC)'), fieldtype: 'Currency' },
    //         { fieldtype: 'Section Break', label: 'Address Info' },
    //         { fieldname: 'home_address', label: __('Home Address'), fieldtype: 'Text' },
    //         { fieldtype: 'Column Break' },
    //         { fieldname: 'address_in_uae', label: __('Address in UAE'), fieldtype: 'Text' },

    //         { fieldtype: 'Section Break', label: 'Unit Info' },
    //         { fieldname: 'type', label: __('Type'), fieldtype: 'Select', options: '\nOff-plan\nSecondary' },
    //         { fieldname: 'project', label: __('Project'), fieldtype: 'Data' },
    //         { fieldname: 'unit_number', label: __('Unit Number'), fieldtype: 'Int' },
    //         { fieldname: 'unit_area_sqft', label: __('Unit Area (SQFT)'), fieldtype: 'Float' },
    //         { fieldname: 'unit_view', label: __('Unit View'), fieldtype: 'Data' },
    //         { fieldtype: 'Column Break' },
    //         { fieldname: 'developer', label: __('Developer'), fieldtype: 'Data' },
    //         { fieldname: 'unit_type', label: __('Unit Type'), fieldtype: 'Data' },
    //         { fieldname: 'unit_floor', label: __('Unit Floor'), fieldtype: 'Data' },
    //         { fieldname: 'unit_price_aed', label: __('Unit Price (AED)'), fieldtype: 'Currency', reqd: 1 },
    //         { fieldname: 'developer_sales_representative', label: __('Developer Sales Representative'), fieldtype: 'Data' },
    //         { fieldtype: 'Column Break' },
    //         { fieldname: 'bookingeoi_paid', label: __('Booking/EOI Paid'), fieldtype: 'Currency' },
    //         { fieldname: 'bookingeoi_paid_amount_aed', label: __('Booking/EOI Paid Amount (AED)'), fieldtype: 'Currency' },
    //         { fieldname: 'booking_form_signed', label: __('Booking Form Signed'), fieldtype: 'Select', options: '\nYes\nNo' },
    //         { fieldname: 'upload_booking_form', label: __('Upload Booking Form'), fieldtype: 'Attach' },
    //         { fieldtype: 'Column Break' },
    //         { fieldname: 'spa_signed', label: __('SPA Signed'), fieldtype: 'Select', options: '\nYes\nNo' },
    //         { fieldname: 'spa_upload', label: __('SPA Upload'), fieldtype: 'Attach' },
    //         { fieldname: 'soa_upload', label: __('SOA Upload'), fieldtype: 'Attach' },
    //         { fieldtype: 'Section Break', label: 'Client Screening' },
    //         { fieldname: 'is_client_screened_before_payment', label: __('Is Client Screened Before Payment'), fieldtype: 'Select', options: '\nYes\nNo' },
    //         { fieldname: 'screening_date_and_time', label: __('Screening Date and Time'), fieldtype: 'Datetime' },
    //         { fieldname: 'screening_result', label: __('Screening Result'), fieldtype: 'Select', options: '\nGreen\nRed' },
    //         { fieldtype: 'Column Break' },
    //         { fieldname: 'screenshot_of_green_light', label: __('Screenshot of Green Light'), fieldtype: 'Attach' },
            
    //         { fieldname: 'screenshot_of_final_screening', label: __('Screenshot of Final Screening'), fieldtype: 'Attach' },
    //         { fieldtype: 'Section Break'},
    //         { fieldname: 'reason_for_late_screening', label: __('Reason for Late Screening'), fieldtype: 'Text' },
    //     ];

    //     // Create and show the dialog
    //     const dialog = new frappe.ui.Dialog({
    //         title: __('Sales Completion Form'),
    //         fields: sales_form_fields,
    //         primary_action_label: __('Submit'),
    //         primary_action(values) {
    //             // Freeze the UI during processing
    //             frappe.dom.freeze(__("Submitting..."));

    //             // Use frappe.call to insert the new document
    //             frappe.call({
    //                 method: 'frappe.client.insert',
    //                 args: {
    //                     doc: {
    //         doctype: 'Sales Completion Form',
            
    //         // Explicitly mapping every single field from the 'values' object
    //         type_register: values.type_register,
    //         first_name: values.first_name,
    //         last_name: values.last_name,
    //         passport_number: values.passport_number,
    //         passport_date_of_expiry: values.passport_date_of_expiry,
    //         main_phone_number: values.main_phone_number,
    //         uae_phone_number: values.uae_phone_number,
    //         home_address: values.home_address,
    //         address_in_uae: values.address_in_uae,
    //         country_of_origin: values.country_of_origin,
    //         country_of_residence: values.country_of_residence,
    //         extra_joint_owners: values.extra_joint_owners,
    //         passport_copy: values.passport_copy,
    //         date_of_birth: values.date_of_birth,
    //         email: values.email,
    //         age_range: values.age_range,
    //         yearly_estimated_income_as_per_kyc: values.yearly_estimated_income_as_per_kyc,
    //         type: values.type,
    //         project: values.project,
    //         unit_area_sqft: values.unit_area_sqft,
    //         unit_price_aed: values.unit_price_aed,
    //         upload_booking_form: values.upload_booking_form,
    //         soa_upload: values.soa_upload,
    //         unit_number: values.unit_number,
    //         developer_sales_representative: values.developer_sales_representative,
    //         unit_view: values.unit_view,
    //         bookingeoi_paid: values.bookingeoi_paid,
    //         spa_signed: values.spa_signed,
    //         bookingeoi_paid_amount_aed: values.bookingeoi_paid_amount_aed,
    //         developer: values.developer,
    //         unit_type: values.unit_type,
    //         unit_floor: values.unit_floor,
    //         booking_form_signed: values.booking_form_signed,
    //         spa_upload: values.spa_upload,
    //         is_client_screened_before_payment: values.is_client_screened_before_payment,
    //         screening_result: values.screening_result,
    //         screenshot_of_green_light: values.screenshot_of_green_light,
    //         reason_for_late_screening: values.reason_for_late_screening,
    //         screening_date_and_time: values.screening_date_and_time,
    //         screenshot_of_final_screening: values.screenshot_of_final_screening,
    //         lead_id: me.frm.doc.name,
    //     }
    //                 },
    //                 callback: function (r) {
    //                     frappe.dom.unfreeze();
    //                     if (!r.exc) {
    //                          // Hide the dialog.
    //                         dialog.hide();
                            
    //                         // Immediately show the confirmation message.
    //                         frappe.msgprint({
    //                             message: __("Sales Completion Form {0} has been created. The lead will be closed upon its approval.", [`<a href="/app/sales-completion-form/${r.message.name}" target="_blank">${r.message.name}</a>`]),
    //                             title: __('Action Required'),
    //                             indicator: 'green' 
    //                         });
                            
    //                         // Refresh the form to ensure a clean state.
    //                         me.frm.refresh();
    //                     }
    //                     // Frappe handles errors (r.exc) automatically
    //                 }
    //             });
    //         }
    //     });
    //     dialog.show();
    // }


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