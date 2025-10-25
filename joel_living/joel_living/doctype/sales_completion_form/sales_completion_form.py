# Copyright (c) 2025, Subburaj and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import get_url
from joel_living.email import send_custom_email

class SalesCompletionForm(Document):
    def after_insert(self):
        """
        This method is called immediately after the document is saved for the first time.
        Instead of doing all the work here, we enqueue a background job.
        This makes the user interface feel fast and responsive.
        """
        frappe.enqueue(
            # The full path to the background function we defined below
            "joel_living.joel_living.doctype.sales_completion_form.sales_completion_form.send_sales_completion_alerts",
            # Pass the necessary data to the background job
            doc_name=self.name,
            lead_id=self.lead_id,
            type_register=self.type_register,
            now=frappe.conf.developer_mode 
        )

# ==============================================================================
# BACKGROUND JOB: Handles all the notification and email logic
# This function MUST be defined outside the SalesCompletionForm class
# ==============================================================================

def send_sales_completion_alerts(doc_name, lead_id, type_register):
    """
    This function runs in the background. It checks settings, gets recipients,
    and sends both a system notification and an email.
    """
    try:
        send_mail_enabled = frappe.db.get_single_value(
            'Admin Settings', 
            'send_mail_on_sales_completion'
        )

        if not send_mail_enabled:
            return # Exit if the setting is disabled.

        manager_roles = ["Admin", "Super Admin"]
        recipient_user_ids = frappe.db.sql_list("""
            SELECT DISTINCT hr.parent
            FROM `tabHas Role` AS hr
            INNER JOIN `tabUser` AS u ON hr.parent = u.name
            WHERE
                hr.role IN %(roles)s
                AND u.enabled = 1
        """, {"roles": manager_roles})

        if not recipient_user_ids:
            frappe.log_message(
                title="Sales Completion Alert", 
                message=f"No enabled users with roles {manager_roles} were found for document {doc_name}."
            )
            return

        # Prepare the common content for both notifications and emails
        doc = frappe.get_doc("Sales Completion Form", doc_name)
        subject = f"Action Required: New Sales Completion Form '{doc.name}'"
        notification_subject = f"New Sales Completion Form <a href='{doc.get_url()}'>{doc.name}</a> requires your action."

        for user in recipient_user_ids:
            # Create a new Notification Log entry using the precise pattern you requested.
            notification = frappe.new_doc("Notification Log")
            notification.for_user = user
            notification.from_user = doc.owner # 'owner' is more reliable than frappe.session.user
            notification.document_type = doc.doctype
            notification.document_name = doc.name
            notification.subject = ("New Sales Completion Form '{0}' needs your action").format(frappe.bold(doc.name))
            notification.set("type", "Alert") # Sets the notification type (e.g., Alert, Comment, Login)
            notification.insert(ignore_permissions=True)
        
        
        # Get email addresses for the users we found
        recipient_emails = frappe.db.get_all(
            "User",
            filters={"name": ("in", recipient_user_ids)},
            fields=["email"],
            pluck="email" # Pluck gives a clean list like ['a@b.com', 'c@d.com']
        )
        
        # Filter out any empty email strings
        recipient_emails = [email for email in recipient_emails if email]
        
        if not recipient_emails:
            return 
        from frappe.utils import get_url
        from joel_living.email import send_custom_email
        
        full_doc_url = get_url(doc.get_url())
        
        # Construct the enhanced HTML email template
        message = build_email_html(subject, lead_id, type_register, full_doc_url)
        
        send_custom_email(
            to=recipient_emails,
            subject=subject,
            message=message
        )
        
        frappe.db.commit()

    except Exception:
        # Log the full error in the "Error Log" for debugging
        frappe.log_error(frappe.get_traceback(), "Sales Completion Email & Notification Job Failed")

def build_email_html(subject, lead_id, type_register, full_doc_url):
    """
    Helper function to build and return the HTML content for the email.
    This keeps the main logic cleaner.
    """
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head><title>{subject}</title></head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; margin: 0; padding: 20px; background-color: #f4f7f6;">
        <table width="100%" border="0" cellspacing="0" cellpadding="0">
            <tr>
                <td align="center">
                    <table width="600" border="0" cellspacing="0" cellpadding="0" style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; border: 1px solid #e0e0e0;">
                        <!-- Header -->
                        <tr>
                            <td align="center" style="padding: 20px 25px; background-color: #007bff; color: #ffffff; border-top-left-radius: 8px; border-top-right-radius: 8px;">
                                <h1 style="margin: 0; font-size: 24px;">New Sales Completion Form</h1>
                            </td>
                        </tr>
                        <!-- Content -->
                        <tr>
                            <td style="padding: 30px 25px; color: #555555; line-height: 1.6;">
                                <p style="margin: 0 0 25px;">A new Sales Completion Form has been created and requires your review and action.</p>
                                <table width="100%" border="0" cellspacing="0" cellpadding="10" style="background-color: #f9f9f9; border-left: 3px solid #007bff;">
                                    <tr>
                                        <td style="padding: 15px;">
                                            <p style="margin: 0 0 8px;"><strong>Lead ID:</strong> {lead_id}</p>
                                            <p style="margin: 0;"><strong>Registration Type:</strong> {type_register}</p>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        <!-- Call-to-Action Button -->
                        <tr>
                            <td align="center" style="padding: 0 25px 30px;">
                                <a href="{full_doc_url}" target="_blank" style="display: inline-block; padding: 12px 25px; font-size: 16px; font-weight: 600; color: #ffffff; background-color: #28a745; text-decoration: none; border-radius: 5px;">
                                    View Document
                                </a>
                            </td>
                        </tr>
                        <!-- Footer -->
                        <tr>
                            <td align="center" style="padding: 20px 25px; font-size: 12px; color: #888888; border-top: 1px solid #eeeeee;">
                                <p style="margin: 0;">This is an automated notification from the system.</p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """


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