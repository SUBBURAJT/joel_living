# Copyright (c) 2025, Subburaj and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import pandas as pd
from io import BytesIO
from datetime import datetime
from frappe.utils import get_url, format_datetime
from joel_living.email import send_custom_email
import frappe
from frappe.utils.background_jobs import enqueue

class LeadExportRequest(Document):

    def after_insert(self):
        """Enqueue email and system notification after Lead Export Request is created."""
        enqueue(
            self.send_notifications,
            queue='short',
            job_name=f"lead_export_notify_{self.name}"
        )

    def send_notifications(self):
        """Send email and system notification for Lead Export Request"""
        admin_settings = frappe.get_single("Admin Settings")

        # Only proceed if Email Account is configured
        if not admin_settings.email_account:
            frappe.log_error("Admin Settings missing Email Account. Lead Export Notification Skipped.", 
                             "Lead Export Notification")
            return

        owner_email = self.owner
        requester = frappe.utils.get_fullname(owner_email) or owner_email

        # Prepare CC emails
        cc_emails = []
        if admin_settings.cc_mail_ids:
            cc_emails = [e.strip() for e in admin_settings.cc_mail_ids.replace("\n", ",").split(",") if e.strip()]

        # URL to view the export request
        doc_url = f"{get_url()}/app/lead-export-request/{self.name}"

        # Email content
        subject = f"New Lead Export Request from {requester}"
        message = f"""
        <div style="font-family: 'Segoe UI', Arial, sans-serif; background-color: #f7f9fc; padding: 25px;">
            <div style="max-width: 600px; margin: auto; background-color: #fff; border-radius: 8px; 
                        box-shadow: 0 2px 8px rgba(0,0,0,0.08); padding: 25px;">
                <h2 style="color: #2c3e50; text-align:center; border-bottom: 2px solid #3498db; padding-bottom: 10px;">
                    🆕 New Lead Export Request
                </h2>

                
                <p>A new <strong>Lead Export Request</strong> has been raised by 
                        <b>{requester}</b>.
                    </p>

                <div style="background-color: #f9fafc; padding: 15px; border-left: 4px solid #3498db; 
                            font-size: 14px; color: #555;">
                    <p><strong>Request ID:</strong> {self.name}</p>
                    <p><strong>Status:</strong> {self.status or "Draft"}</p>
                    <p><strong>Submitted On:</strong> {format_datetime(self.creation, 'dd-MMM-yyyy HH:mm')}</p>
                </div>

                <div style="text-align:center; margin: 25px 0;">
                    <a href="{doc_url}" style="
                        background-color: #3498db;
                        color: white;
                        text-decoration: none;
                        padding: 12px 22px;
                        border-radius: 5px;
                        font-weight: 500;
                        font-size: 15px;
                        display: inline-block;">
                        🔍 View Export Request
                    </a>
                </div>

                <p style="margin-top:25px; color:#95a5a6; font-size:13px; text-align:center;">
                    This is an automated notification from your system.
                </p>
            </div>
        </div>
        """

        # Send email
        try:
            send_custom_email(
                to=admin_settings.to_mail_id,
                cc=cc_emails,
                subject=subject,
                message=message
            )
            frappe.log_error(f"Lead Export Request notification sent to {owner_email}", "Lead Export Notification")
        except Exception as e:
            frappe.log_error(f"Failed to send Lead Export Request email: {str(e)}", "Lead Export Notification Error")

        # Send system notification
        try:
            frappe.get_doc({
                "doctype": "Notification Log",
                "subject": f"Lead Export Request Created: {self.name}",
                "type": "Alert",
                "document_type": "Lead Export Request",
                "document_name": self.name,
                "for_user": owner_email,
                "description": f"Your Lead Export Request {self.name} has been created and is currently in {self.status or 'Draft'} status."
            }).insert(ignore_permissions=True)
        except Exception as e:
            frappe.log_error(f"Failed to create system notification: {str(e)}", "Lead Export Notification")


@frappe.whitelist()
def create_export_request(leads):
    if isinstance(leads, str):
        leads = frappe.parse_json(leads)

    doc = frappe.get_doc({
        "doctype": "Lead Export Request",
        "status": "Pending Approval",
        "requested_by": frappe.session.user,
        "requested_on": frappe.utils.now(),
        "lead_list": frappe.as_json(leads)
    })
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    return doc.name


@frappe.whitelist()
def approve_export_request(docname):
    doc = frappe.get_doc("Lead Export Request", docname)

    try:
        leads = frappe.parse_json(doc.lead_list)

        # Fetch all required fields from Lead
        lead_docs = frappe.get_all(
            "Lead",
            filters={"name": ["in", leads]},
            fields=[
                "name", "lead_name", "gender", "custom_budget_range", "custom_budget_usd",
                "custom_budget_aed", "custom_priority_", "custom_lead_status as lead_status",
                "custom_project as project", "custom_developer", "custom_developer_representative",
                "custom_lead_stages", "custom_main_lead_source as main_lead_source",
                "custom_secondary_lead_sources as secondary_lead_sources",
                "custom_lead_type", "custom_lead_category as lead_category",
                "country", "state", "city",
                "email_id as email", "mobile_no", "phone_ext", "whatsapp_no as whatsapp"
            ]
        )

        if not lead_docs:
            frappe.throw("No leads found to export")

        # Prepare rows
        rows = []
        for ld in lead_docs:
            rows.append({
                "Lead ID": ld.get("name"),
                "Lead Name": ld.get("lead_name"),
                "Gender": ld.get("custom_genders"),
                "Budget Range": ld.get("custom_budget_range"),
                "Budget Value (USD)": ld.get("custom_budget_usd"),
                "Budget converted to AED": ld.get("custom_budget_aed"),
                "Priority": ld.get("custom_priority_"),
                "Lead Status": ld.get("lead_status") or "Open",
                "Project": ld.get("project"),
                "Developer": ld.get("custom_developer"),
                "Developer Representative": ld.get("custom_developer_representative"),
                "Lead Stages": ld.get("custom_lead_stages"),
                "Main Lead Source": ld.get("main_lead_source"),
                "Secondary Lead Sources": ld.get("secondary_lead_sources"),
                "Lead Type": ld.get("custom_lead_type"),
                "Lead Category": ld.get("lead_category"),
                "Country": ld.get("country"),
                "State/Province": ld.get("state"),
                "City": ld.get("city"),
                "Email": ld.get("email"),
                "Mobile No": ld.get("mobile_no"),
                "Secondary Phone": ld.get("phone_ext"),
                "WhatsApp": ld.get("whatsapp"),
                "custom_lead_category":"Fresh Lead",
            })

        # Generate Excel in memory
        df = pd.DataFrame(rows)
        from io import BytesIO
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = BytesIO()
        df.to_excel(output, index=False)
        output.seek(0)

        file_name = f"exported_leads_{docname}_{timestamp}.xlsx"

        # Check existing file attached
        existing_file = frappe.get_all(
            "File",
            filters={
                "attached_to_doctype": "Lead Export Request",
                "attached_to_name": docname
            },
            limit=1
        )

        if existing_file:
            file_doc = frappe.get_doc("File", existing_file[0].name)
            file_doc.file_name = file_name
            file_doc.content = output.getvalue()
            file_doc.save(ignore_permissions=True)
        else:
            file_doc = frappe.get_doc({
                "doctype": "File",
                "file_name": file_name,
                "attached_to_doctype": "Lead Export Request",
                "attached_to_name": docname,
                "is_private": 1,
                "content": output.getvalue()
            })
            file_doc.insert(ignore_permissions=True)

        # Update Lead Export Request
        doc.export_file = file_doc.file_url
        doc.status = "Approved"
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        enqueue(send_export_notification, queue="short", docname=docname, status="Approved")

        return {"status": "success", "file": doc.export_file}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Lead Export Failed")
        doc.status = "Failed"
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        enqueue(send_export_notification, queue="short", docname=docname, status="Failed", error=str(e))

        return {"status": "failed", "error": str(e)}



@frappe.whitelist()
def reject_export_request(docname, rejected_notes):
    doc = frappe.get_doc("Lead Export Request", docname)
    doc.status = "Rejected"
    doc.rejected_notes = rejected_notes
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    enqueue(send_export_notification, queue="short", docname=docname, status="Rejected")
    return {"status": "rejected"}



def send_export_notification(docname, status, error=None):
    """Send email and system notification for Lead Export Request"""
    try:
        doc = frappe.get_doc("Lead Export Request", docname)
        admin_settings = frappe.get_single("Admin Settings")

        if not admin_settings.email_account:
            frappe.log_error("Admin Settings missing Email Account. Lead Export Notification Skipped.", "Lead Export Notification")
            return

        owner_email = doc.owner
        requester = frappe.utils.get_fullname(owner_email) or owner_email

        # Prepare CC emails
        cc_emails = []
        if admin_settings.cc_mail_ids:
            cc_emails = [e.strip() for e in admin_settings.cc_mail_ids.replace("\n", ",").split(",") if e.strip()]

        doc_url = f"{get_url()}/app/lead-export-request/{doc.name}"
        subject = f"Lead Export Request {status}: {doc.name}"

        # Email message
        message = f"""
        <div style="font-family: 'Segoe UI', Arial, sans-serif; background-color: #f7f9fc; padding: 25px;">
            <div style="max-width: 600px; margin: auto; background-color: #fff; border-radius: 8px; 
                        box-shadow: 0 2px 8px rgba(0,0,0,0.08); padding: 25px;">
                <h2 style="color: #2c3e50; text-align:center; border-bottom: 2px solid #3498db; padding-bottom: 10px;">
                    🆕 Lead Export Request {status}
                </h2>
                <p style="font-size: 15px; color: #34495e;">
                    Hello <b style="color:#2c3e50;">{requester}</b>, your Lead Export Request <b>{doc.name}</b> has been <b>{status}</b>.
                </p>
        """

        # Include rejected notes for Rejected status
        if status == "Rejected" and getattr(doc, "rejected_notes", None):
            message += f"""
            <div style="background-color: #f9fafc; padding: 15px; border-left: 4px solid #e74c3c; font-size: 14px; color: #555;">
                <p><strong>Notes:</strong> {doc.rejected_notes}</p>
            </div>
            """

        # Include error if Failed
        if status == "Failed" and error:
            message += f'<p style="color:#e74c3c;"><strong>Error:</strong> {error}</p>'

        message += f"""
                <div style="text-align:center; margin: 25px 0;">
                    <a href="{doc_url}" style="
                        background-color: #3498db;
                        color: white;
                        text-decoration: none;
                        padding: 12px 22px;
                        border-radius: 5px;
                        font-weight: 500;
                        font-size: 15px;
                        display: inline-block;">
                        🔍 View Request
                    </a>
                </div>
                <p style="margin-top:25px; color:#95a5a6; font-size:13px; text-align:center;">
                    This is an automated notification from your system.
                </p>
            </div>
        </div>
        """

        # Send email
        send_custom_email(to=owner_email, cc=cc_emails, subject=subject, message=message)

        # Send system notification
        try:
            desc = f"Your Lead Export Request {doc.name} has been {status}."
            if status == "Rejected" and getattr(doc, "rejected_notes", None):
                desc += f"\nNotes: {doc.rejected_notes}"
            if status == "Failed" and error:
                desc += f"\nError: {error}"

            frappe.get_doc({
                "doctype": "Notification Log",
                "subject": f"Lead Export Request {status}: {doc.name}",
                "type": "Alert",
                "document_type": "Lead Export Request",
                "document_name": doc.name,
                "for_user": owner_email,
                "description": desc
            }).insert(ignore_permissions=True)
        except Exception as e:
            frappe.log_error(f"Failed to create system notification: {str(e)}", "Lead Export Notification")

    except Exception as e:
        frappe.log_error(f"Failed to send export notification: {str(e)}", "Lead Export Notification")
