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

    send_assignment_email_and_notification(leads, lead_owner)


@frappe.whitelist()
def send_assignment_email_and_notification(leads, lead_owner):
    """Send one consolidated email + app notification for assigned leads."""
 
    user = frappe.get_doc("User", lead_owner)
    user_email = user.email
    full_name = user.full_name or get_fullname(lead_owner)
 
    # Get lead titles for email body
    lead_titles = [
        frappe.db.get_value("Lead", l, "lead_name") or l for l in leads
    ]
    lead_list = "".join(f"<li>{lt}</li>" for lt in lead_titles)
 
    subject = f"{len(leads)} Lead(s) Assigned to You"
    message = f"""
        <p>Hi {full_name},</p>
        <p>The following leads have been assigned to you:</p>
        <ul>{lead_list}</ul>
        <p>Please review them at your earliest convenience.</p>
        <p>Thanks,<br>Admin</p>
    """
 
    # Send one email (this is fine)
    # send_email_safe(user_email, subject, message, ref_doctype="Lead", ref_name=leads[0])
 
    # Create Notification Log (in-app only, no email)
    for lead_name in leads:
        create_notification_log(
            user=lead_owner,
            title=subject,
            message=message,
            document_type="Lead",
            document_name=lead_name
        )
 
 
def create_notification_log(user, title, message, document_type=None, document_name=None):
    """Create an in-app notification (Notification Log entry only, no email)."""
    try:
        frappe.get_doc({
            "doctype": "Notification Log",
            "subject": title,
            "email_content": message,
            "for_user": user,
            "document_type": document_type,
            "document_name": document_name,
   
        }).insert(ignore_permissions=True)
    except Exception as e:
        frappe.log_error(f"Notification Log failed: {str(e)}", "Lead Assignment Notification Error")




######### Lead Hide ##############

import frappe
from frappe.utils import now
 
 
# =========================================================
# UTILITY FUNCTIONS
# =========================================================
 
def send_email_safe(user_email, subject, message, ref_doctype=None, ref_name=None):
    """Send email safely. Logs failure without interrupting execution."""
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
 
 
def create_notification(user, subject, message, ref_doctype, ref_name, send_email=True):
    """Create an in-app notification and optionally send an email."""
    notif = frappe.get_doc({
        "doctype": "Notification Log",
        "subject": subject,
        "email_content": message,
        "for_user": user,
        "document_type": ref_doctype,
        "document_name": ref_name,
    })
    notif.insert(ignore_permissions=True)
 
    if send_email:
        user_email = frappe.db.get_value("User", user, "email")
        send_email_safe(user_email, subject, message, ref_doctype, ref_name)
 
    frappe.db.commit()
 
 
# =========================================================
# SALES AGENT — REQUEST HIDE
# =========================================================
 
@frappe.whitelist()
def request_hide(leads):
    """
    Sales Agent requests to hide one or more Leads.
    Sends email + notification to all Admins.
    """
    current_user = frappe.session.user
    full_name = frappe.utils.get_fullname(current_user)
 
    try:
        # Ensure leads is a list
        if isinstance(leads, str):
            try:
                leads = frappe.parse_json(leads)
                if isinstance(leads, str):
                    leads = [leads]
            except Exception:
                leads = [leads]
 
        processed_leads = []
 
        # Get all Admin users
        admins = {"Administrator"}
        role_holders = frappe.get_all("Has Role", filters={"role": "Admin"}, fields=["parent"])
        admins.update({r.parent for r in role_holders})
 
        # Process each lead
        for lead in leads:
            req_doc = frappe.get_doc({
                "doctype": "Lead Hide Request",
                "lead": lead,
                "requested_by": full_name,
                "requested_by_user": current_user,
                "requested_date": frappe.utils.now_datetime(),
                "status": "Pending"
            })
            req_doc.insert(ignore_permissions=True)
 
            # Update Lead
            frappe.db.set_value("Lead", lead, {
                "lead_owner": None,
                "custom_hide_status": "Pending"
            })
 
            processed_leads.append(lead)
 
            # Notify Admins (both email + in-app)
            for admin_user in admins:
                frappe.enqueue(
                    create_notification,
                    queue="long",
                    timeout=600,
                    user=admin_user,
                    subject=f"Lead Hide Request from {full_name}",
                    message=f"{full_name} has submitted a request to hide the Lead <b>{lead}</b>.<br><br>"
                            f"The request is awaiting your review and approval. Please verify the details of the lead "
                            f"and take the necessary action based on its validity.",
                    ref_doctype="Lead Hide Request",
                    ref_name=req_doc.name,
                    send_email=True
                )
 
        frappe.db.commit()
 
        # ✅ Show all lead IDs in popup
        lead_list_str = ", ".join(processed_leads)
        frappe.msgprint(f"Hide request submitted successfully for: {lead_list_str}")
 
        return {"ok": True, "message": f"Hide request submitted successfully for: {lead_list_str}"}
 
    except Exception as e:
        frappe.log_error(f"Hide request failed for {leads}: {str(e)}")
        return {"ok": False, "message": "Failed to submit hide request. Try again later."}
 
 
# =========================================================
# ADMIN ACTION — APPROVE HIDE
# =========================================================
 
@frappe.whitelist()
def approve_hide_request(docname):
    """Approve a hide request (Admin or Administrator only)."""
    try:
        req = frappe.get_doc("Lead Hide Request", docname)
        current_user = frappe.session.user
        approver_full_name = frappe.utils.get_fullname(current_user)
 
        if req.status != "Pending":
            return {"ok": False, "message": "Only Pending requests can be approved."}
 
        lead_id = req.lead
        requester_user = getattr(req, "requested_by_user", None)
 
        # Store the lead ID as text in the same field before deletion
        req.db_set("lead", lead_id, update_modified=False)
 
        # Delete the Lead safely
        try:
            frappe.delete_doc("Lead", lead_id, ignore_permissions=True, force=True)
        except Exception as delete_error:
            frappe.log_error(f"Failed to delete lead {lead_id}: {delete_error}")
            return {"ok": False, "message": f"Could not delete Lead {lead_id}. Check dependencies."}
 
        # Update request details (keep lead field as text)
        frappe.db.set_value("Lead Hide Request", req.name, {
            "status": "Approved",
            "approval_date": now(),
            "approved_by": approver_full_name,
            "approved_by_user": current_user
        })
 
        # Enqueue email sending
        if requester_user:
            requester_email = frappe.db.get_value("User", requester_user, "email")
            if requester_email:
                subject = f"Lead Hide Request Approved — Lead {lead_id}"
                message = f"""
                    <p>Dear {req.requested_by},</p>
                    <p>Your request to hide the lead <b>{lead_id}</b> has been <b>approved</b> by <b>{approver_full_name}</b>.</p>
                    <p>The lead has been permanently deleted and recorded in Deleted Documents.</p>
                    <br>
                    <p>Regards,<br><b>{approver_full_name}</b><br>Administrator</p>
                """
                frappe.enqueue(
                    send_email_safe,
                    queue="long",
                    timeout=600,
                    user_email=requester_email,
                    subject=subject,
                    message=message,
                    ref_doctype="Lead Hide Request",
                    ref_name=req.name
                )
 
        frappe.msgprint("Lead hide request approved successfully.")
        return
 
    except Exception as e:
        frappe.log_error(f"Approve hide failed for {docname}: {frappe.get_traceback()}")
        return {"ok": False, "message": f"Failed to approve hide request: {str(e)}"}
 
 
# =========================================================
# ADMIN ACTION — REJECT HIDE
# =========================================================
 
@frappe.whitelist()
def reject_hide_request(docname):
    """Reject a hide request (Admin or Administrator only)."""
    try:
        req = frappe.get_doc("Lead Hide Request", docname)
        current_user = frappe.session.user
        approver_full_name = frappe.utils.get_fullname(current_user)
 
        if req.status != "Pending":
            return {"ok": False, "message": "Only Pending requests can be rejected."}
 
        lead = req.lead
        requester_user = getattr(req, "requested_by_user", None)
 
        # Update Lead
        frappe.db.set_value("Lead", lead, {
            "lead_owner": None,
            "custom_lead_category": "Reshuffled Lead",
            "custom_hide_status": "Rejected"
        })
        frappe.db.commit()
 
        # Update request
        req.status = "Rejected"
        req.approval_date = now()
        req.approved_by = approver_full_name
        req.approved_by_user = current_user
        req.save(ignore_permissions=True)
 
        # Enqueue rejection email
        if requester_user:
            requester_email = frappe.db.get_value("User", requester_user, "email")
            if requester_email:
                subject = f"Lead Hide Request Rejected — Lead {lead}"
                message = f"""
                    <p>Dear {req.requested_by},</p>
                    <p>Your request to hide the lead <b>{lead}</b> has been <b>rejected</b> by <b>{approver_full_name}</b>.</p>
                    <p>The lead has been moved to <b>Reshuffled Leads</b> for reassignment.</p>
                    <br>
                    <p>Regards,<br><b>{approver_full_name}</b></p>
                """
                frappe.enqueue(
                    send_email_safe,
                    queue="long",
                    timeout=600,
                    user_email=requester_email,
                    subject=subject,
                    message=message,
                    ref_doctype="Lead Hide Request",
                    ref_name=req.name
                )
 
        frappe.msgprint("Lead hide request rejected and message sent successfully.")
        return
 
    except Exception as e:
        frappe.log_error(f"Reject hide failed for {docname}: {str(e)}")
        return {"ok": False, "message": "Failed to reject hide request."}

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





import frappe

@frappe.whitelist()
def check_for_existing_sales_form(lead_name):
    """
    Checks if a 'Sales Completion Form' for a given Lead already exists.
    Returns the name of the form if it exists, otherwise returns None.
    """
    return frappe.db.exists("Sales Completion Form", {"lead_id": lead_name})