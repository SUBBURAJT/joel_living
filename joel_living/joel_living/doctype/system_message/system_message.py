# Copyright (c) 2025, Subburaj and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class SystemMessage(Document):
	def after_insert(self):
		
		"""Send system message to all / selected / multiple users + email"""

		subject = self.subject or "System Message"
		message = self.message
		sender = frappe.session.user

		recipients = []
		if self.send_to_all_users:
			recipients = frappe.get_all(
				"User",
				filters={"enabled": 1, "user_type": "System User"},
				pluck="name"
			)
			recipients = [u for u in recipients if u not in [sender, "Guest"]]

		elif self.recipients:
			recipients = [
				row.user for row in self.recipients
				if row.user not in [sender, "Guest"]
			]
	
	
		if not recipients:
			frappe.msgprint("No valid recipients found.")
			return

		valid_emails = []
		for user in recipients:
			# In-app notification
			frappe.get_doc({
				"doctype": "Notification Log",
				"subject": subject,
				"email_content": message,
				"for_user": user,
				"type": "Alert"
			}).insert(ignore_permissions=True)

			# Collect valid emails for sending
			if is_valid_email(user):
				valid_emails.append(user)

		# Send emails
		if valid_emails:
			frappe.sendmail(
				recipients=valid_emails,
				subject=subject,
				message=message,
				now=True
			)

		# Add to custom inbox
		add_to_inbox(subject, message, recipients)

		frappe.msgprint(
			f" Message sent to {len(valid_emails)} email(s) "
			f"and {len(recipients)} in-app user(s)."
		)


import re
# Message to all the users
def is_valid_email(email):
    """Basic RFC 5321 check"""
    return bool(re.match(r"[^@]+@[^@]+\.[^@]+", str(email)))


def add_to_inbox(subject, message, recipients):
    """Insert records into Message Inbox"""
    for user in recipients:
        doc = frappe.get_doc({
            "doctype": "Message Inbox",
            "title": subject,
            "content": message,
            "recipient": user,
            "sent_on": frappe.utils.now_datetime()
        })
        # Generate custom name like MSG-2025-00001
        doc.name = frappe.model.naming.make_autoname("MSG-.YYYY.-.#####")
        doc.insert(ignore_permissions=True)


def system_inbox_permission(user):
    """Restrict Message Inbox so users only see their own messages.
       Admin/Administrator see all.
    """
    if user in ["Administrator", "admin"]:
        return None  # no restriction
    return f"`tabMessage Inbox`.recipient = '{user}'"