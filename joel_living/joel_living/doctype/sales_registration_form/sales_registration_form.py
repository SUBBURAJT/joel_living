import frappe
from frappe.model.document import Document
import json

class SalesRegistrationForm(Document):
    def before_save(self):
        """
        This hook runs before the document is saved. It checks for changes in the
        `rejected_fields_json` field, consolidates all rejected fields into a
        single message, and appends ONE new row to the `rejection_reason_table`.
        """
        # This logic should only run on existing documents, not on creation
        if self.is_new():
            return

        # Get the state of the document as it was just before this save operation
        doc_before_save = self.get_doc_before_save()
        if not doc_before_save:
            return

        # Get the new and old JSON strings
        new_rejection_json = self.rejected_fields_json
        old_rejection_json = doc_before_save.rejected_fields_json

        # --- CORE LOGIC ---
        # Proceed only if `rejected_fields_json` has changed AND contains new data.
        if new_rejection_json and (new_rejection_json != old_rejection_json):
            try:
                # Parse the JSON string: {"main": ["field1", "field2"], ...}
                rejection_data = json.loads(new_rejection_json)

                if not isinstance(rejection_data, dict):
                    return  # Exit if not a dictionary

                all_rejected_fieldnames = []
                all_rejected_labels = []

                # Step 1: Collect all rejected fieldnames from all lists in the JSON
                for key, value in rejection_data.items():
                    if isinstance(value, list):
                        all_rejected_fieldnames.extend(value)
                
                # If after checking all lists, we have no fieldnames, stop.
                if not all_rejected_fieldnames:
                    return

                # Step 2: Get the human-readable labels for each fieldname
                meta = frappe.get_meta(self.doctype)
                for fieldname in all_rejected_fieldnames:
                    field_def = meta.get_field(fieldname)
                    if field_def and field_def.label:
                        all_rejected_labels.append(field_def.label)
                    else:
                        all_rejected_labels.append(fieldname) # Fallback to fieldname

                # Step 3: Construct the final, consolidated strings
                # For the `rejection_field` (a comma-separated list of technical names)
                consolidated_fields = ", ".join(all_rejected_fieldnames)
                consolidated_fields_names = ", ".join(all_rejected_labels)
                # For the `rejection_reason` (a single, user-friendly message)
                # consolidated_reason = "Please review and correct the following fields: " + ", ".join(all_rejected_labels) + "."

                # Step 4: Append the single, consolidated row to the child table
                self.append('rejection_reason_table', {
                    'rejection_field': consolidated_fields_names,
                    'rejection_reason': self.rejection_reason
                })

            except (json.JSONDecodeError, TypeError):
                frappe.log_error(
                    f"Could not parse rejected_fields_json for {self.name}",
                    "Sales Registration Hook Error"
                )
                return