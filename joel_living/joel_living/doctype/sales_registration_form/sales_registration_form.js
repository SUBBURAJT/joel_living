// Copyright (c) 2025, Subburaj and contributors
// For license information, please see license.txt

frappe.ui.form.on("Sales Registration Form", {
    refresh(frm) {
        // Run the logic when the form first loads.
        update_floor_options(frm);
    },

    project(frm) {
        // Run the logic whenever the 'project' field changes.
        update_floor_options(frm);
    }
});

// Helper function to keep the code clean and avoid repetition (DRY principle).
function update_floor_options(frm) {
    const project_name = frm.doc.project;
    const floor_field = frm.fields_dict['unit_floor'];

    // If the project field is cleared, reset the floor field and stop.
    if (!project_name) {
        frm.set_value('unit_floor', ''); // Clear the selected value
        frm.set_df_property('unit_floor', 'options', []); // Clear the dropdown options
        return;
    }

    // Show a loading indicator for better user experience.
    frm.fields_dict.unit_floor.df.options = ["Loading..."];
    frm.fields_dict.unit_floor.refresh();

    // Call the same backend Python function we used for the dialog.
    frappe.call({
        method: "joel_living.custom_lead.get_project_floor_details", // IMPORTANT: Ensure this path is correct for your app.
        args: {
            project_name: project_name
        },
        callback: function(r) {
            // Check if the server returned valid data.
            if (r.message) {
                const details = r.message;
                const number_of_floors = cint(details.no_of_floors) || 0;
                const has_mezzanine = cint(details.include_mezzanine_floor); // cint converts to integer (0 or 1)

                let floor_options = [];

                // --- This is the same logic from the dialog ---
                floor_options.push('G'); // Ground floor is always first

                if (has_mezzanine) {
                    floor_options.push('M');
                    // If mezzanine exists, count up to (total floors - 1)
                    for (let i = 1; i < number_of_floors; i++) {
                        floor_options.push(String(i));
                    }
                } else {
                    // If no mezzanine, count up to the total number of floors
                    for (let i = 1; i <= number_of_floors; i++) {
                        floor_options.push(String(i));
                    }
                }

                // Update the 'unit_floor' field's properties with the new options.
                floor_field.df.options = floor_options;
                
                // Refresh the field on the UI to display the new dropdown.
                floor_field.refresh();
                
                // IMPORTANT: If the previously saved floor value is no longer valid
                // (e.g., project changed from one with a Mezzanine to one without),
                // clear the value to prevent saving invalid data.
                if (frm.doc.unit_floor && !floor_options.includes(frm.doc.unit_floor)) {
                    frm.set_value('unit_floor', '');
                }

            } else {
                // If the project doesn't exist or has no floor data, reset the field.
                frm.set_value('unit_floor', '');
                floor_field.df.options = [];
                floor_field.refresh();
            }
        }
    });
}