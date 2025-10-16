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
                if (frappe.user_roles.includes(d.allowed)) {
                    // console.log("User has access to transition:", d.action);
                    added = true;
                    me.frm.page.add_action_item(__(d.action), function () {
                        // console.log("Workflow action triggered:", d.action);
                        if (me.frm.doc.doctype === "Lead") {
                            frappe.confirm(
                                __(`Are you sure you want to proceed with ${d.action}?`),
                                () => {
                                    // console.log("User confirmed:", d.action);
                                    
                                 



                                    if (d.action === "Close") {
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
                                                        message: __("A Sales Completion Form {0} already exists for this lead and is pending approval.", [`<a href="/app/sales-completion-form/${r.message}" target="_blank">${r.message}</a>`])
                                                    });
                                                } else {
                                                    // No form exists, so proceed with showing the dialog.
                                                    me.show_sales_completion_dialog();
                                                }
                                            }
                                        });
                                    } else {
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
                }
            });

            this.setup_btn(added);
        });
    }



    show_sales_completion_dialog(transition) {
        const me = this;

        // Define all the fields for the dialog based on the Sales Completion Form doctype
        const sales_form_fields = [
            { fieldname: 'type_register', label: __('Type Register'), fieldtype: 'Select', options: 'EOI\nCompleted Sale', reqd: 1 },
            { fieldtype: 'Section Break', label: 'Client(s) Information' },
            { fieldname: 'first_name', label: __('First Name'), fieldtype: 'Data' },
            { fieldname: 'last_name', label: __('Last Name'), fieldtype: 'Data' },
            { fieldname: 'passport_number', label: __('Passport Number'), fieldtype: 'Data' },
            { fieldname: 'passport_date_of_expiry', label: __('Passport Date of Expiry'), fieldtype: 'Date' },
            { fieldname: 'passport_copy', label: __('Passport Copy'), fieldtype: 'Attach' },
            { fieldtype: 'Column Break' },
            { fieldname: 'date_of_birth', label: __('Date of Birth'), fieldtype: 'Date' },
            { fieldname: 'main_phone_number', label: __('Main Phone Number'), fieldtype: 'Data' },
            { fieldname: 'uae_phone_number', label: __('UAE Phone Number'), fieldtype: 'Data' },
            { fieldname: 'email', label: __('Email'), fieldtype: 'Data' },
            { fieldtype: 'Column Break' },
            { fieldname: 'country_of_origin', label: __('Country of Origin'), fieldtype: 'Data' },
            { fieldname: 'country_of_residence', label: __('Country of Residence'), fieldtype: 'Data' },
            { fieldname: 'extra_joint_owners', label: __('Extra Joint Owners'), fieldtype: 'Select', options: 'No Joint Owners\n1\n2\n3' },
            { fieldtype: 'Column Break' },
            { fieldname: 'age_range', label: __('Age Range'), fieldtype: 'Select', options: '\n21-29\n30-45\n46-55\n56-70\n+70' },
            { fieldname: 'yearly_estimated_income_as_per_kyc', label: __('Yearly Estimated Income (as per KYC)'), fieldtype: 'Currency' },
            { fieldtype: 'Section Break', label: 'Address Info' },
            { fieldname: 'home_address', label: __('Home Address'), fieldtype: 'Text' },
            { fieldtype: 'Column Break' },
            { fieldname: 'address_in_uae', label: __('Address in UAE'), fieldtype: 'Text' },

            { fieldtype: 'Section Break', label: 'Unit Info' },
            { fieldname: 'type', label: __('Type'), fieldtype: 'Select', options: '\nOff-plan\nSecondary' },
            { fieldname: 'project', label: __('Project'), fieldtype: 'Data' },
            { fieldname: 'unit_number', label: __('Unit Number'), fieldtype: 'Int' },
            { fieldname: 'unit_area_sqft', label: __('Unit Area (SQFT)'), fieldtype: 'Float' },
            { fieldname: 'unit_view', label: __('Unit View'), fieldtype: 'Data' },
            { fieldtype: 'Column Break' },
            { fieldname: 'developer', label: __('Developer'), fieldtype: 'Data' },
            { fieldname: 'unit_type', label: __('Unit Type'), fieldtype: 'Data' },
            { fieldname: 'unit_floor', label: __('Unit Floor'), fieldtype: 'Data' },
            { fieldname: 'unit_price_aed', label: __('Unit Price (AED)'), fieldtype: 'Currency', reqd: 1 },
            { fieldname: 'developer_sales_representative', label: __('Developer Sales Representative'), fieldtype: 'Data' },
            { fieldtype: 'Column Break' },
            { fieldname: 'bookingeoi_paid', label: __('Booking/EOI Paid'), fieldtype: 'Currency' },
            { fieldname: 'bookingeoi_paid_amount_aed', label: __('Booking/EOI Paid Amount (AED)'), fieldtype: 'Currency' },
            { fieldname: 'booking_form_signed', label: __('Booking Form Signed'), fieldtype: 'Select', options: '\nYes\nNo' },
            { fieldname: 'upload_booking_form', label: __('Upload Booking Form'), fieldtype: 'Attach' },
            { fieldtype: 'Column Break' },
            { fieldname: 'spa_signed', label: __('SPA Signed'), fieldtype: 'Select', options: '\nYes\nNo' },
            { fieldname: 'spa_upload', label: __('SPA Upload'), fieldtype: 'Attach' },
            { fieldname: 'soa_upload', label: __('SOA Upload'), fieldtype: 'Attach' },
            { fieldtype: 'Section Break', label: 'Client Screening' },
            { fieldname: 'is_client_screened_before_payment', label: __('Is Client Screened Before Payment'), fieldtype: 'Select', options: '\nYes\nNo' },
            { fieldname: 'screening_date_and_time', label: __('Screening Date and Time'), fieldtype: 'Datetime' },
            { fieldname: 'screening_result', label: __('Screening Result'), fieldtype: 'Select', options: '\nGreen\nRed' },
            { fieldtype: 'Column Break' },
            { fieldname: 'screenshot_of_green_light', label: __('Screenshot of Green Light'), fieldtype: 'Attach' },
            
            { fieldname: 'screenshot_of_final_screening', label: __('Screenshot of Final Screening'), fieldtype: 'Attach' },
            { fieldtype: 'Section Break'},
            { fieldname: 'reason_for_late_screening', label: __('Reason for Late Screening'), fieldtype: 'Text' },
        ];

        // Create and show the dialog
        const dialog = new frappe.ui.Dialog({
            title: __('Sales Completion Form'),
            fields: sales_form_fields,
            primary_action_label: __('Submit'),
            primary_action(values) {
                // Freeze the UI during processing
                frappe.dom.freeze(__("Submitting..."));

                // Use frappe.call to insert the new document
                frappe.call({
                    method: 'frappe.client.insert',
                    args: {
                        doc: {
            doctype: 'Sales Completion Form',
            
            // Explicitly mapping every single field from the 'values' object
            type_register: values.type_register,
            first_name: values.first_name,
            last_name: values.last_name,
            passport_number: values.passport_number,
            passport_date_of_expiry: values.passport_date_of_expiry,
            main_phone_number: values.main_phone_number,
            uae_phone_number: values.uae_phone_number,
            home_address: values.home_address,
            address_in_uae: values.address_in_uae,
            country_of_origin: values.country_of_origin,
            country_of_residence: values.country_of_residence,
            extra_joint_owners: values.extra_joint_owners,
            passport_copy: values.passport_copy,
            date_of_birth: values.date_of_birth,
            email: values.email,
            age_range: values.age_range,
            yearly_estimated_income_as_per_kyc: values.yearly_estimated_income_as_per_kyc,
            type: values.type,
            project: values.project,
            unit_area_sqft: values.unit_area_sqft,
            unit_price_aed: values.unit_price_aed,
            upload_booking_form: values.upload_booking_form,
            soa_upload: values.soa_upload,
            unit_number: values.unit_number,
            developer_sales_representative: values.developer_sales_representative,
            unit_view: values.unit_view,
            bookingeoi_paid: values.bookingeoi_paid,
            spa_signed: values.spa_signed,
            bookingeoi_paid_amount_aed: values.bookingeoi_paid_amount_aed,
            developer: values.developer,
            unit_type: values.unit_type,
            unit_floor: values.unit_floor,
            booking_form_signed: values.booking_form_signed,
            spa_upload: values.spa_upload,
            is_client_screened_before_payment: values.is_client_screened_before_payment,
            screening_result: values.screening_result,
            screenshot_of_green_light: values.screenshot_of_green_light,
            reason_for_late_screening: values.reason_for_late_screening,
            screening_date_and_time: values.screening_date_and_time,
            screenshot_of_final_screening: values.screenshot_of_final_screening,
            lead_id: me.frm.doc.name,
        }
                    },
                    callback: function (r) {
                        frappe.dom.unfreeze();
                        if (!r.exc) {
                             // Hide the dialog.
                            dialog.hide();
                            
                            // Immediately show the confirmation message.
                            frappe.msgprint({
                                message: __("Sales Completion Form {0} has been created. The lead will be closed upon its approval.", [`<a href="/app/sales-completion-form/${r.message.name}" target="_blank">${r.message.name}</a>`]),
                                title: __('Action Required'),
                                indicator: 'green' 
                            });
                            
                            // Refresh the form to ensure a clean state.
                            me.frm.refresh();
                        }
                        // Frappe handles errors (r.exc) automatically
                    }
                });
            }
        });
        dialog.show();
    }


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