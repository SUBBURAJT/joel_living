# Copyright (c) 2025, Subburaj and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class SalesCompletionForm(Document):
	pass



@frappe.whitelist()
def approve_and_close_lead(form_name, lead_name):
    """
    Approves the Sales Completion Form and updates the linked Lead's status.
    - Submits the form to mark it as 'Approved'.
    - Fetches the Lead document.
    - If the lead status is 'Sales Completed', it changes it to 'Close'.
    """
    try:
        # Get the Sales Completion Form and submit it (sets docstatus to 1)
        sales_form = frappe.get_doc("Sales Completion Form", form_name)
        sales_form.submit()

        # Get the linked Lead document
        lead_doc = frappe.get_doc("Lead", lead_name)

        # Check if the custom_lead_status is 'Sales Completed' before updating
        if lead_doc.custom_lead_status == "Sales Completed":
            lead_doc.custom_lead_status = "Closed" # Update the status
            lead_doc.save(ignore_permissions=True) # Save the lead
            frappe.db.commit() # Commit changes to the database
            return f"Lead {lead_name} status updated to Closed."
        else:
            return f"Lead {lead_name} status was not 'Sales Completed'. No changes were made."

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Approval Error")
        frappe.throw(f"An error occurred during the approval process: {e}")