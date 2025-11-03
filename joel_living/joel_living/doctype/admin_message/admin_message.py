# Copyright (c) 2025, Subburaj and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime
import re

class AdminMessage(Document):
    def before_save(self):
        """Auto-populate recipients_display with names or emails"""
        if self.send_to_all_users:
            # Get all enabled users except sender & Guest
            recipients = frappe.get_all(
                "User",
                filters={"enabled": 1, "user_type": "System User"},
                pluck="full_name"
            )
            recipients = [r for r in recipients if r not in [frappe.session.user, "Guest"]]
        else:
            recipients = []
            for r in self.get("recipients"):
                # Try to use full name if available, else email
                full_name = frappe.db.get_value("User", r.user, "full_name") or r.user
                recipients.append(full_name)

        # Set the display field
        self.recipient_name = ", ".join(recipients[:5])  # show only first 5 if too long
        if len(recipients) > 5:
            self.recipient_name += f" (+{len(recipients) - 5} more)"
    def after_insert(self):
        """Triggered when the Admin Message is saved and confirmed"""
        print(self.__dict__)  # This will print the document's data

        subject = self.subject or "Admin Message"
        message_body = self.message or "No message content provided."
        sender = frappe.session.user
        
        recipients = []
        if self.send_to_all_users:
            recipients = frappe.get_all(
                "User",
                filters={"enabled": 1, "user_type": "System User"},
                pluck="name"
            )
            recipients = [u for u in recipients if u not in [sender, "Guest"]]
        else:
            # Assuming the child table fieldname is 'recipients' and the field for the user is 'user'
            for recipient in self.get("recipients"):
                recipients.append(recipient.user)

        if not recipients:
            frappe.msgprint("No recipients found.")
            return

        # Update to "Sending" before enqueue
        self.status = "Sending"
        self.sent_date = now_datetime()
        self.save(ignore_permissions=True)

        # Enqueue background job
        frappe.enqueue(
            send_system_message_job,
            queue='long',
            timeout=600,
            is_async=True,
            subject=subject,
            message_body=message_body,
            sender=sender,
            recipients=recipients, # Pass the dynamically generated recipients list
            message_docname=self.name
        )

        frappe.msgprint("Message sending has been enqueued successfully")


# -----------------------------------------------
# Helper Functions
# -----------------------------------------------
def is_valid_email(email):
    """Basic RFC 5321 check"""
    return bool(re.match(r"[^@]+@[^@]+\.[^@]+", str(email)))


def get_system_message_template(subject, message_body, sender_name=None):
    sender_name = sender_name or "System Administrator"
    return f"""
    <div style="font-family: Arial, sans-serif; background-color: #f8f9fa; padding: 30px;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; 
                    box-shadow: 0 2px 6px rgba(0,0,0,0.1); overflow: hidden;">
            
            <div style="background-color: #0052cc; color: white; padding: 16px 24px; font-size: 20px; font-weight: bold;">
                {subject}
            </div>

            <div style="padding: 24px; color: #333333; font-size: 15px; line-height: 1.6;">
                <p style="margin: 0 0 16px;">Dear Team,</p>

                <div style="background-color: #f1f5f9; border-left: 4px solid #0052cc; padding: 16px; border-radius: 4px;">
                    {message_body}
                </div>

                <p style="margin-top: 24px;">Best regards,</p>
                <p style="font-weight: bold; color: #0052cc;">{sender_name}</p>
            </div>

            <div style="background-color: #f1f3f5; color: #555; font-size: 12px; text-align: center; padding: 12px;">
                This is an automated Admin message from <b>Joel Living</b>. Please do not reply directly to this email.
            </div>
        </div>
    </div>
    """


def add_to_inbox(subject, message, recipients, sent_date=None):
    """Insert records into Admin Message Inbox and return mapping {user: docname}"""
    inbox_map = {}
    for user in recipients:
        doc = frappe.get_doc({
            "doctype": "Admin Message Inbox",
            "title": subject,
            "content": message,
            "recipient": user,
            "send_date": sent_date or frappe.utils.now_datetime(),
        })
        doc.name = frappe.model.naming.make_autoname("MSG-.YYYY.-.#####")
        doc.insert(ignore_permissions=True)
        inbox_map[user] = doc.name
    return inbox_map


# -----------------------------------------------
# Main Job Function (Async)
# -----------------------------------------------
def send_system_message_job(subject, message_body, sender, recipients, message_docname):
    """Runs in background — sends emails and updates status accordingly"""
    try:
        # Update to "Sending"
        frappe.db.set_value("Admin Message", message_docname, "status", "Sending")
        frappe.db.commit()

        sender_full_name = frappe.utils.get_fullname(sender)
        email_message = get_system_message_template(subject, message_body, sender_full_name)
        sent_date = now_datetime()

        if not recipients:
            frappe.db.set_value("Admin Message", message_docname, "status", "Send Failed")
            frappe.db.commit()
            frappe.log_error("No valid recipients found", "Admin Message Sending Error")
            return

        inbox_map = add_to_inbox(subject, message_body, recipients, sent_date)
        valid_emails = []

        for user in recipients:
            inbox_docname = inbox_map.get(user)
            frappe.get_doc({
                "doctype": "Notification Log",
                "subject": subject,
                "email_content": message_body,
                "for_user": user,
                "type": "Alert",
                "document_type": "Admin Message Inbox",
                "document_name": inbox_docname,
            }).insert(ignore_permissions=True)

            if is_valid_email(user):
                valid_emails.append(user)

        # Send emails
        if valid_emails:
            frappe.sendmail(
                recipients=valid_emails,
                subject=subject,
                message=email_message,
                now=True
            )

        # ✅ Update status to "Sent"
        frappe.db.set_value("Admin Message", message_docname, {
            "status": "Sent",
            "sent_date": sent_date
        })
        frappe.db.commit()

        frappe.msgprint("Message sent successfully.")

    except Exception as e:
        frappe.db.set_value("Admin Message", message_docname, "status", "Send Failed")
        frappe.db.commit()
        frappe.log_error(frappe.get_traceback(), "Admin Message Send Failed")

def system_inbox_permission(user):
    """Restrict Admin Message Inbox so users only see their own messages.
       Admin/Administrator see all.
    """
    if user in ["Administrator", "admin"]:
        return None  # no restriction
    return f"`tabAdmin Message Inbox`.recipient = '{user}'"
