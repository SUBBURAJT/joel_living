from frappe.share import add, get_users, remove
import frappe
from datetime import datetime, timedelta

def after_insert_lead(doc, method):
    # Always share and set custom_complete_before for new records
    if doc.lead_owner:
        handle_lead_sharing(doc)


def on_update_lead(doc, method):
    # Get the previous version of the doc
    old_doc = doc.get_doc_before_save()
    if not old_doc:
        return

    # Only update if lead_owner changed
    old_owner = old_doc.lead_owner
    new_owner = doc.lead_owner

    if old_owner != new_owner:
        handle_lead_sharing(doc)


def handle_lead_sharing(doc):
    """
    Manage lead sharing and custom_complete_before based on lead_owner
    """
    try:
        if doc.lead_owner:
            # Remove old shares
            remove_existing_shares(doc)

            # Share with lead_owner
            share_lead_with_user(doc)

            # Update custom_complete_before
            update_custom_complete_before(doc)
        else:
            # Remove all shares
            remove_existing_shares(doc)

            # Clear custom_complete_before
            doc.custom_complete_before = None

    except Exception as e:
        import traceback
        frappe.log_error(traceback.format_exc(), f"Failed handling lead sharing for {doc.name}")


def remove_existing_shares(doc):
    try:
        shares = get_users(doc.doctype, doc.name)
        for share in shares:
            remove(doc.doctype, doc.name, share.user)
    except Exception as e:
        frappe.log_error(f"Failed to remove shares for {doc.doctype} {doc.name}: {str(e)}")


def share_lead_with_user(doc):
    try:
        if doc.lead_owner:
            add(doc.doctype, doc.name, doc.lead_owner, write=1, share=1, everyone=0)
    except Exception as e:
        import traceback
        frappe.log_error(traceback.format_exc(), f"Failed to share Lead {doc.name}")


def update_custom_complete_before(doc):
    try:
        settings = frappe.get_single("Admin Settings")
        number_of_days = settings.number_of_days_lead_completed_in or 0

        # Include today as day 1
        adjusted_days = max(number_of_days - 1, 0)
        custom_date = (datetime.today() + timedelta(days=adjusted_days)).date()

        # Set directly on doc
        doc.custom_complete_before = custom_date

    except Exception as e:
        import traceback
        frappe.log_error(traceback.format_exc(), f"Failed to update custom_complete_before for {doc.name}")



################### Assign Lead to User ####################

from datetime import datetime, timedelta

@frappe.whitelist()
def assign_leads_to_user(leads, lead_owner):
    if isinstance(leads, str):
        leads = frappe.parse_json(leads)


    for lead_name in leads:
        lead = frappe.get_doc("Lead", lead_name)
        lead.lead_owner = lead_owner
        update_custom_complete_before(lead)
        lead.save(ignore_permissions=True)

    frappe.db.commit()




######### Lead Hide ##############


@frappe.whitelist()
def reject_hide(lead):
    """Admin rejects hide"""
    requester = frappe.db.get_value("Lead", lead, "custom_hide_requested_by")

    try:
        if requester:
            frappe.enqueue(
                create_notification,
                queue='long',
                timeout=600,
                user=requester,
                subject="Hide Request Rejected",
                message=f"Your request to hide Lead {lead} was rejected by Admin.",
                ref_doctype="Lead",
                ref_name=lead,
                send_email=True
            )

        # Only update after enqueue is successful
        frappe.db.set_value("Lead", lead, {
            "custom_hide_status": "Rejected",
            "custom_hide_requested_by": None
        })
        frappe.db.commit()

        return {"ok": True, "message": "Hide request rejected"}

    except Exception as e:
        frappe.log_error(f"Reject hide failed for {lead}: {str(e)}")
        return {"ok": False, "message": "Rejection failed. Notification not sent."}
    



# --- Admin approve hide ---
@frappe.whitelist()
def approve_hide(lead):
    """Admin approves hide"""
    requester = frappe.db.get_value("Lead", lead, "custom_hide_requested_by")

    try:
        if requester:
            frappe.enqueue(
                create_notification,
                queue='long',
                timeout=600,
                user=requester,
                subject="Hide Request Approved",
                message=f"Your request to hide Lead {lead} was approved and moved to Trash.",
                ref_doctype="Lead",
                ref_name=lead,
                send_email=True
            )

        # Only update after enqueue is successful
        frappe.db.set_value("Lead", lead, {
            "custom_hide_status": "Trashed",
            "custom_hide_requested_by": None
        })
        frappe.db.commit()

        return {"ok": True, "message": "Lead marked as Trash"}

    except Exception as e:
        frappe.log_error(f"Approve hide failed for {lead}: {str(e)}")
        return {"ok": False, "message": "Approval failed. Notification not sent."}


@frappe.whitelist()
def request_hide(lead):
    """Sales Agent requests hide"""
    current_user = frappe.session.user
    admins = get_admin_users()

    try:
        # Notify Admin and Administrator first
        for admin_user in admins:
            frappe.enqueue(
                create_notification,
                queue='long',
                timeout=600,
                user=admin_user,
                subject="Hide Request Submitted",
                message=f"{frappe.utils.get_fullname(current_user)} requested to hide Lead {lead}",
                ref_doctype="Lead",
                ref_name=lead,
                send_email=True
            )

        # Only after successful enqueue, update status
        frappe.db.set_value("Lead", lead, {
            "custom_hide_status": "Pending",
            "custom_hide_requested_by": current_user
        })
        frappe.db.commit()

        return {"ok": True, "message": "Hide request submitted"}

    except Exception as e:
        frappe.log_error(f"Hide request failed for {lead}: {str(e)}")
        return {"ok": False, "message": "Failed to send notification. Try again later."}



def get_admin_users():
    """Return list of Admin and Administrator users"""
   
    admins = []
    admins.append("Administrator")

    role_holders = frappe.get_all(
        "Has Role",
        filters={"role": "Admin"},
        fields=["parent"]
    )

    for r in role_holders:
        if r.parent not in admins:
            admins.append(r.parent)

    return admins





# --- Enqueued notification function ---
def create_notification(user, subject, message, ref_doctype, ref_name, send_email=True):
    """
    Create in-app notification and optionally send email in background using enqueue
    """
    # In-app notification
    notif = frappe.get_doc({
        "doctype": "Notification Log",
        "subject": subject,
        "email_content": message,
        "for_user": user,
        "document_type": ref_doctype,
        "document_name": ref_name
    })
    notif.insert(ignore_permissions=True)

    # Email (optional)
    if send_email:
        user_email = frappe.db.get_value("User", user, "email")
        send_email_safe(user_email, subject, message, ref_doctype, ref_name)

    frappe.db.commit()


def send_email_safe(user_email, subject, message, ref_doctype=None, ref_name=None):
    """
    Send email to user safely.
    Logs only on failure, ignores success.
    """
    if not user_email or "@" not in user_email:
        return

    try:
        frappe.sendmail(
            recipients=[user_email],
            subject=subject,
            message=message,
            reference_doctype=ref_doctype,
            reference_name=ref_name,
            now=True,
            delayed=False
        )
    except Exception as e:
        frappe.log_error(f"Email send failed to {user_email}: {str(e)}")
