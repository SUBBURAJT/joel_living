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

# from datetime import datetime, timedelta

# @frappe.whitelist()
# def assign_leads_to_user(leads, lead_owner):
#     if isinstance(leads, str):
#         leads = frappe.parse_json(leads)


#     for lead_name in leads:
#         lead = frappe.get_doc("Lead", lead_name)
#         lead.lead_owner = lead_owner
#         update_custom_complete_before(lead)
#         lead.save(ignore_permissions=True)

#     frappe.db.commit()

#     send_assignment_email_and_notification(leads, lead_owner)


# @frappe.whitelist()
# def send_assignment_email_and_notification(leads, lead_owner):
#     """Send one consolidated email + app notification for assigned leads."""
 
#     user = frappe.get_doc("User", lead_owner)
#     user_email = user.email
#     full_name = user.full_name or get_fullname(lead_owner)
 
#     # Get lead titles for email body
#     lead_titles = [
#         frappe.db.get_value("Lead", l, "lead_name") or l for l in leads
#     ]
#     lead_list = "".join(f"<li>{lt}</li>" for lt in lead_titles)
 
#     subject = f"{len(leads)} Lead(s) Assigned to You"
#     message = f"""
#         <p>Hi {full_name},</p>
#         <p>The following leads have been assigned to you:</p>
#         <ul>{lead_list}</ul>
#         <p>Please review them at your earliest convenience.</p>
#         <p>Thanks,<br>Admin</p>
#     """
 
#     # Send one email (this is fine)
#     # send_email_safe(user_email, subject, message, ref_doctype="Lead", ref_name=leads[0])
 
#     # Create Notification Log (in-app only, no email)
#     for lead_name in leads:
#         create_notification_log(
#             user=lead_owner,
#             title=subject,
#             message=message,
#             document_type="Lead",
#             document_name=lead_name
#         )
 
 
# def create_notification_log(user, title, message, document_type=None, document_name=None):
#     """Create an in-app notification (Notification Log entry only, no email)."""
#     try:
#         frappe.get_doc({
#             "doctype": "Notification Log",
#             "subject": title,
#             "email_content": message,
#             "for_user": user,
#             "document_type": document_type,
#             "document_name": document_name,
   
#         }).insert(ignore_permissions=True)
#     except Exception as e:
#         frappe.log_error(f"Notification Log failed: {str(e)}", "Lead Assignment Notification Error")




# ######### Lead Hide ##############

# import frappe
# from frappe.utils import now
 
 
# # =========================================================
# # UTILITY FUNCTIONS
# # =========================================================
 
# def send_email_safe(user_email, subject, message, ref_doctype=None, ref_name=None):
#     """Send email safely. Logs failure without interrupting execution."""
#     if not user_email or "@" not in user_email:
#         return
 
#     try:
#         frappe.sendmail(
#             recipients=[user_email],
#             subject=subject,
#             message=message,
#             reference_doctype=ref_doctype,
#             reference_name=ref_name,
#             now=True,
#             delayed=False
#         )
#     except Exception as e:
#         frappe.log_error(f"Email send failed to {user_email}: {str(e)}")
 
 
# def create_notification(user, subject, message, ref_doctype, ref_name, send_email=True):
#     """Create an in-app notification and optionally send an email."""
#     notif = frappe.get_doc({
#         "doctype": "Notification Log",
#         "subject": subject,
#         "email_content": message,
#         "for_user": user,
#         "document_type": ref_doctype,
#         "document_name": ref_name,
#     })
#     notif.insert(ignore_permissions=True)
 
#     if send_email:
#         user_email = frappe.db.get_value("User", user, "email")
#         send_email_safe(user_email, subject, message, ref_doctype, ref_name)
 
#     frappe.db.commit()
 
 
# # =========================================================
# # SALES AGENT — REQUEST HIDE
# # =========================================================
 
# @frappe.whitelist()
# def request_hide(leads):
#     """
#     Sales Agent requests to hide one or more Leads.
#     Sends email + notification to all Admins.
#     """
#     current_user = frappe.session.user
#     full_name = frappe.utils.get_fullname(current_user)
 
#     try:
#         # Ensure leads is a list
#         if isinstance(leads, str):
#             try:
#                 leads = frappe.parse_json(leads)
#                 if isinstance(leads, str):
#                     leads = [leads]
#             except Exception:
#                 leads = [leads]
 
#         processed_leads = []
 
#         # Get all Admin users
#         admins = {"Administrator"}
#         role_holders = frappe.get_all("Has Role", filters={"role": "Admin"}, fields=["parent"])
#         admins.update({r.parent for r in role_holders})
 
#         # Process each lead
#         for lead in leads:
#             req_doc = frappe.get_doc({
#                 "doctype": "Lead Hide Request",
#                 "lead": lead,
#                 "requested_by": full_name,
#                 "requested_by_user": current_user,
#                 "requested_date": frappe.utils.now_datetime(),
#                 "status": "Pending"
#             })
#             req_doc.insert(ignore_permissions=True)
 
#             # Update Lead
#             frappe.db.set_value("Lead", lead, {
#                 "lead_owner": None,
#                 "custom_hide_status": "Pending"
#             })
 
#             processed_leads.append(lead)
 
#             # Notify Admins (both email + in-app)
#             for admin_user in admins:
#                 frappe.enqueue(
#                     create_notification,
#                     queue="long",
#                     timeout=600,
#                     user=admin_user,
#                     subject=f"Lead Hide Request from {full_name}",
#                     message=f"{full_name} has submitted a request to hide the Lead <b>{lead}</b>.<br><br>"
#                             f"The request is awaiting your review and approval. Please verify the details of the lead "
#                             f"and take the necessary action based on its validity.",
#                     ref_doctype="Lead Hide Request",
#                     ref_name=req_doc.name,
#                     send_email=True
#                 )
 
#         frappe.db.commit()
 
#         # ✅ Show all lead IDs in popup
#         lead_list_str = ", ".join(processed_leads)
#         frappe.msgprint(f"Hide request submitted successfully for: {lead_list_str}")
 
#         return {"ok": True, "message": f"Hide request submitted successfully for: {lead_list_str}"}
 
#     except Exception as e:
#         frappe.log_error(f"Hide request failed for {leads}: {str(e)}")
#         return {"ok": False, "message": "Failed to submit hide request. Try again later."}
 
 
# # =========================================================
# # ADMIN ACTION — APPROVE HIDE
# # =========================================================
 
# @frappe.whitelist()
# def approve_hide_request(docname):
#     """Approve a hide request (Admin or Administrator only)."""
#     try:
#         req = frappe.get_doc("Lead Hide Request", docname)
#         current_user = frappe.session.user
#         approver_full_name = frappe.utils.get_fullname(current_user)
 
#         if req.status != "Pending":
#             return {"ok": False, "message": "Only Pending requests can be approved."}
 
#         lead_id = req.lead
#         requester_user = getattr(req, "requested_by_user", None)
 
#         # Store the lead ID as text in the same field before deletion
#         req.db_set("lead", lead_id, update_modified=False)
 
#         # Delete the Lead safely
#         try:
#             frappe.delete_doc("Lead", lead_id, ignore_permissions=True, force=True)
#         except Exception as delete_error:
#             frappe.log_error(f"Failed to delete lead {lead_id}: {delete_error}")
#             return {"ok": False, "message": f"Could not delete Lead {lead_id}. Check dependencies."}
 
#         # Update request details (keep lead field as text)
#         frappe.db.set_value("Lead Hide Request", req.name, {
#             "status": "Approved",
#             "approval_date": now(),
#             "approved_by": approver_full_name,
#             "approved_by_user": current_user
#         })
 
#         # Enqueue email sending
#         if requester_user:
#             requester_email = frappe.db.get_value("User", requester_user, "email")
#             if requester_email:
#                 subject = f"Lead Hide Request Approved — Lead {lead_id}"
#                 message = f"""
#                     <p>Dear {req.requested_by},</p>
#                     <p>Your request to hide the lead <b>{lead_id}</b> has been <b>approved</b> by <b>{approver_full_name}</b>.</p>
#                     <p>The lead has been permanently deleted and recorded in Deleted Documents.</p>
#                     <br>
#                     <p>Regards,<br><b>{approver_full_name}</b><br>Administrator</p>
#                 """
#                 frappe.enqueue(
#                     send_email_safe,
#                     queue="long",
#                     timeout=600,
#                     user_email=requester_email,
#                     subject=subject,
#                     message=message,
#                     ref_doctype="Lead Hide Request",
#                     ref_name=req.name
#                 )
 
#         frappe.msgprint("Lead hide request approved successfully.")
#         return
 
#     except Exception as e:
#         frappe.log_error(f"Approve hide failed for {docname}: {frappe.get_traceback()}")
#         return {"ok": False, "message": f"Failed to approve hide request: {str(e)}"}
 
 
# # =========================================================
# # ADMIN ACTION — REJECT HIDE
# # =========================================================
 
# @frappe.whitelist()
# def reject_hide_request(docname):
#     """Reject a hide request (Admin or Administrator only)."""
#     try:
#         req = frappe.get_doc("Lead Hide Request", docname)
#         current_user = frappe.session.user
#         approver_full_name = frappe.utils.get_fullname(current_user)
 
#         if req.status != "Pending":
#             return {"ok": False, "message": "Only Pending requests can be rejected."}
 
#         lead = req.lead
#         requester_user = getattr(req, "requested_by_user", None)
 
#         # Update Lead
#         frappe.db.set_value("Lead", lead, {
#             "lead_owner": None,
#             "custom_lead_category": "Reshuffled Lead",
#             "custom_hide_status": "Rejected"
#         })
#         frappe.db.commit()
 
#         # Update request
#         req.status = "Rejected"
#         req.approval_date = now()
#         req.approved_by = approver_full_name
#         req.approved_by_user = current_user
#         req.save(ignore_permissions=True)
 
#         # Enqueue rejection email
#         if requester_user:
#             requester_email = frappe.db.get_value("User", requester_user, "email")
#             if requester_email:
#                 subject = f"Lead Hide Request Rejected — Lead {lead}"
#                 message = f"""
#                     <p>Dear {req.requested_by},</p>
#                     <p>Your request to hide the lead <b>{lead}</b> has been <b>rejected</b> by <b>{approver_full_name}</b>.</p>
#                     <p>The lead has been moved to <b>Reshuffled Leads</b> for reassignment.</p>
#                     <br>
#                     <p>Regards,<br><b>{approver_full_name}</b></p>
#                 """
#                 frappe.enqueue(
#                     send_email_safe,
#                     queue="long",
#                     timeout=600,
#                     user_email=requester_email,
#                     subject=subject,
#                     message=message,
#                     ref_doctype="Lead Hide Request",
#                     ref_name=req.name
#                 )
 
#         frappe.msgprint("Lead hide request rejected and message sent successfully.")
#         return
 
#     except Exception as e:
#         frappe.log_error(f"Reject hide failed for {docname}: {str(e)}")
#         return {"ok": False, "message": "Failed to reject hide request."}






################## Latest ajay code ##################


from datetime import datetime, timedelta
import frappe
from frappe.utils import get_fullname
 
@frappe.whitelist()
def assign_leads_to_user(leads, lead_owner):
    """Assign multiple leads to a user and send individual email + in-app notifications."""
    if isinstance(leads, str):
        leads = frappe.parse_json(leads)
 
    for lead_name in leads:
        lead = frappe.get_doc("Lead", lead_name)
        lead.lead_owner = lead_owner
        update_custom_complete_before(lead)
        lead.save(ignore_permissions=True)
 
        # Send email + in-app notification for each lead
        send_assignment_email_and_notification(lead_name, lead_owner)
 
    frappe.db.commit()
 
 
def send_assignment_email_and_notification(lead_name, lead_owner):
    """Send one email and one in-app notification per assigned lead."""
 
    user = frappe.get_doc("User", lead_owner)
    user_email = user.email
    full_name = user.full_name or get_fullname(lead_owner)
 
    lead_doc = frappe.get_doc("Lead", lead_name)
    lead_title = lead_doc.lead_name or lead_name
 
    subject = f"New Lead Assigned: {lead_title}"
    message = f"""
        <p>Hi {full_name},</p>
        <p>A new lead has been assigned to you:</p>
        <ul>
            <li><strong>Lead Name:</strong> {lead_title}</li>
            <li><strong>Lead ID:</strong> {lead_name}</li>
        </ul>
        <p>You can review the lead by logging into the system.</p>
        <p>Thanks,<br>Admin</p>
    """
 
    # Create one in-app notification
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
 
# import frappe
# from frappe.utils import now
# # =========================================================
# # UTILITY FUNCTIONS
# # =========================================================
 
# def send_email_safe(user_email, subject, message, ref_doctype=None, ref_name=None):
#     """Send email safely. Logs failure without interrupting execution."""
#     if not user_email or "@" not in user_email:
#         return
 
#     try:
#         frappe.sendmail(
#             recipients=[user_email],
#             subject=subject,
#             message=message,
#             reference_doctype=ref_doctype,
#             reference_name=ref_name,
#             now=True,
#             delayed=False
#         )
#     except Exception as e:
#         frappe.log_error(f"Email send failed to {user_email}: {str(e)}")
 
 
# def create_notification(user, subject, message, ref_doctype, ref_name, send_email=True):
#     """Create an in-app notification and optionally send an email."""
#     notif = frappe.get_doc({
#         "doctype": "Notification Log",
#         "subject": subject,
#         "email_content": message,
#         "for_user": user,
#         "document_type": ref_doctype,
#         "document_name": ref_name,
#     })
#     notif.insert(ignore_permissions=True)
 
#     if send_email:
#         user_email = frappe.db.get_value("User", user, "email")
#         send_email_safe(user_email, subject, message, ref_doctype, ref_name)
 
#     frappe.db.commit()
 
#  # =========================================================
# # SALES AGENT — REQUEST HIDE
# # =========================================================
# @frappe.whitelist()
# def request_hide(leads):
#     """
#     Sales Agent requests to hide one or more Leads.
#     Sends ONLY system (in-app) notifications to all Admins.
#     """
#     current_user = frappe.session.user
#     full_name = frappe.utils.get_fullname(current_user)
 
#     try:
#         # Ensure leads is a list
#         if isinstance(leads, str):
#             try:
#                 leads = frappe.parse_json(leads)
#                 if isinstance(leads, str):
#                     leads = [leads]
#             except Exception:
#                 leads = [leads]
 
#         processed_leads = []
 
#         # Get all Admin users
#         admins = {"Administrator"}
#         role_holders = frappe.get_all("Has Role", filters={"role": "Admin"}, fields=["parent"])
#         admins.update({r.parent for r in role_holders})
 
#         # Process each lead
#         for lead in leads:
#             req_doc = frappe.get_doc({
#                 "doctype": "Lead Hide Request",
#                 "lead": lead,
#                 "requested_by": full_name,
#                 "requested_by_user": current_user,
#                 "requested_date": frappe.utils.now_datetime(),
#                 "status": "Pending"
#             })
#             req_doc.insert(ignore_permissions=True)
 
#             # ✅ Update Lead to make it completely hidden
#             frappe.db.set_value("Lead", lead, {
#                 "lead_owner": None,
#                 "custom_hide_status": "Pending",
#                 "custom_is_hidden": 1  # Mark lead as hidden (excluded from all lists)
#             })
 
#             processed_leads.append(lead)
 
#             # Send in-app notification to all Admins
#             for admin_user in admins:
#                 frappe.enqueue(
#                     create_notification,
#                     queue="long",
#                     timeout=600,
#                     user=admin_user,
#                     subject=f"Lead Hide Request from {full_name}",
#                     message=f"{full_name} has requested to hide the Lead <b>{lead}</b>.<br><br>"
#                             f"The request is awaiting your review and approval.",
#                     ref_doctype="Lead Hide Request",
#                     ref_name=req_doc.name,
#                     send_email=False
#                 )
 
#         frappe.db.commit()
 
#         # ✅ Show all processed leads in a popup
#         lead_list_str = ", ".join(processed_leads)
#         frappe.msgprint(f"Hide request submitted successfully for: {lead_list_str}")
 
#         return {"ok": True, "message": f"Hide request submitted successfully for: {lead_list_str}"}
 
#     except Exception as e:
#         frappe.log_error(f"Hide request failed for {leads}: {str(e)}")
#         return {"ok": False, "message": "Failed to submit hide request. Try again later."}
 
 
# # =========================================================
# # ADMIN ACTION — APPROVE HIDE
# # =========================================================
# @frappe.whitelist()
# def approve_hide_request(docname):
#     """Approve a hide request (Admin or Administrator only, without deleting the Lead)."""
#     try:
#         req = frappe.get_doc("Lead Hide Request", docname)
#         current_user = frappe.session.user
#         approver_full_name = frappe.utils.get_fullname(current_user)
 
#         if req.status != "Pending":
#             return {"ok": False, "message": "Only Pending requests can be approved."}
 
#         lead_id = req.lead
#         requester_user = getattr(req, "requested_by_user", None)
 
#         # ✅ Instead of deleting, mark the lead as hidden and clear ownership
#         frappe.db.set_value("Lead", lead_id, {
#             "lead_owner": None,
#             "custom_hide_status": "Trashed",
#             "custom_is_hidden": 0  # Hide lead from all views
#         })
#         frappe.db.commit()
 
#         # ✅ Update request details
#         frappe.db.set_value("Lead Hide Request", req.name, {
#             "status": "Approved",
#             "approval_date": now(),
#             "approved_by": approver_full_name,
#             "approved_by_user": current_user
#         })
 
#         # ✅ Send email to requester
#         if requester_user:
#             requester_email = frappe.db.get_value("User", requester_user, "email")
#             if requester_email:
#                 subject = f"Lead Hide Request Approved — Lead {lead_id}"
#                 message = f"""
#                     <p>Dear {req.requested_by},</p>
#                     <p>Your request to hide the lead <b>{lead_id}</b> has been <b>approved</b> by <b>{approver_full_name}</b>.</p>
#                     <p>The lead has been successfully hidden and removed from the active list.</p>
#                     <br>
#                     <p>Regards,<br><b>{approver_full_name}</b><br>Administrator</p>
#                 """
#                 frappe.enqueue(
#                     send_email_safe,
#                     queue="long",
#                     timeout=600,
#                     user_email=requester_email,
#                     subject=subject,
#                     message=message,
#                     ref_doctype="Lead Hide Request",
#                     ref_name=req.name
#                 )
 
#         frappe.msgprint("Lead hide request approved successfully (lead hidden).")
#         return {"ok": True, "message": "Lead hide request approved successfully."}
 
#     except Exception as e:
#         frappe.log_error(f"Approve hide failed for {docname}: {frappe.get_traceback()}")
#         return {"ok": False, "message": f"Failed to approve hide request: {str(e)}"}
 
# # =========================================================
# # ADMIN ACTION — REJECT HIDE
# # =========================================================
 
# @frappe.whitelist()
# def reject_hide_request(docname):
#     """Reject a hide request (Admin or Administrator only)."""
#     try:
#         req = frappe.get_doc("Lead Hide Request", docname)
#         current_user = frappe.session.user
#         approver_full_name = frappe.utils.get_fullname(current_user)
 
#         if req.status != "Pending":
#             return {"ok": False, "message": "Only Pending requests can be rejected."}
 
#         lead = req.lead
#         requester_user = getattr(req, "requested_by_user", None)
 
#         # ✅ Update Lead — make visible again & mark as reshuffled
#         frappe.db.set_value("Lead", lead, {
#             "lead_owner": None,
#             "custom_lead_category": "Reshuffled Lead",
#             "custom_hide_status": "Rejected",
#             "custom_is_hidden": 0  # Show again in unassigned leads
#         })
#         frappe.db.commit()
 
#         # Update request
#         req.status = "Rejected"
#         req.approval_date = now()
#         req.approved_by = approver_full_name
#         req.approved_by_user = current_user
#         req.save(ignore_permissions=True)
 
#         # Enqueue rejection email
#         if requester_user:
#             requester_email = frappe.db.get_value("User", requester_user, "email")
#             if requester_email:
#                 subject = f"Lead Hide Request Rejected — Lead {lead}"
#                 message = f"""
#                     <p>Dear {req.requested_by},</p>
#                     <p>Your request to hide the lead <b>{lead}</b> has been <b>rejected</b> by <b>{approver_full_name}</b>.</p>
#                     <p>The lead has been moved to <b>Reshuffled Leads</b> for reassignment.</p>
#                     <br>
#                     <p>Regards,<br><b>{approver_full_name}</b></p>
#                 """
#                 frappe.enqueue(
#                     send_email_safe,
#                     queue="long",
#                     timeout=600,
#                     user_email=requester_email,
#                     subject=subject,
#                     message=message,
#                     ref_doctype="Lead Hide Request",
#                     ref_name=req.name
#                 )
 
#         frappe.msgprint("Lead hide request rejected and message sent successfully.")
#         return {"ok": True, "message": "Lead hide request rejected successfully."}
 
#     except Exception as e:
#         frappe.log_error(f"Reject hide failed for {docname}: {str(e)}")
#         return {"ok": False, "message": "Failed to reject hide request."}



#############################################################################









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
    return frappe.db.exists("Sales Registration Form", {"lead": lead_name})





################# sales registration form #################

import frappe
import json # Used to handle data from the client script

@frappe.whitelist()
def create_sales_registration(lead_name, data):
    """
    Creates a new 'Sales Registration Form' document from the data
    submitted by the custom dialog in the Lead form.
    
    :param lead_name: The name of the source Lead document.
    :param data: A JSON string of the form data from the dialog.
    """
    try:
        # 1. The data from JS comes as a dictionary (or a JSON string that Frappe auto-converts)
        form_data = data if isinstance(data, dict) else frappe.parse_json(data)
        print(form_data)
        # 2. Create a new document for "Sales Registration Form"
        doc = frappe.new_doc("Sales Registration Form")
        doc.lead = lead_name

        # --- I. MAP MAIN CLIENT & UNIT FIELDS ---
        
        # Main Client Info
        doc.form_type = form_data.get('form_type')
        doc.first_name = form_data.get('first_name')
        doc.last_name = form_data.get('last_name')
        doc.email = form_data.get('email')
        doc.main_phone_number = form_data.get('main_phone_number')
        doc.uae_phone_number = form_data.get('uae_phone_number')
        doc.passport_number = form_data.get('passport_number')
        doc.passport_expiry_date = form_data.get('passport_expiry_date')
        doc.date_of_birth = form_data.get('date_of_birth')
        doc.passport_copy = form_data.get('passport_copy')
        doc.home_address = form_data.get('home_address')
        doc.uae_address = form_data.get('uae_address')
        doc.country_of_origin = form_data.get('country_of_origin')
        doc.country_of_residence = form_data.get('country_of_residence')
        doc.age_range = form_data.get('age_range')
        doc.yearly_estimated_income = form_data.get('yearly_estimated_income')
        
        # Unit & Sale Info
        doc.unit_sale_type = form_data.get('unit_sale_type')
        doc.developer = form_data.get('developer')
        doc.project = form_data.get('project')
        doc.developer_sales_rep = form_data.get('developer_sales_rep')
        doc.unit_number = form_data.get('unit_number')
        doc.unit_type = form_data.get('unit_type')
        doc.unit_price = form_data.get('unit_price')
        doc.unit_area = form_data.get('unit_area')
        doc.unit_view = form_data.get('unit_view')
        doc.unit_floor = form_data.get('unit_floor')
        doc.booking_eoi_paid_amount = form_data.get('booking_eoi_paid_amount')
        doc.booking_form_signed = form_data.get('booking_form_signed')
        doc.booking_form_upload = form_data.get('booking_form_upload')
        doc.spa_upload = form_data.get('spa_upload')
        doc.soa_upload = form_data.get('soa_upload')
        
        # Screening & KYC
        doc.screened_before_payment = form_data.get('screened_before_payment')
        
        # Conditional Field Clearing for Screening Section
        if doc.screened_before_payment == '\nYes':
            doc.screenshot_of_green_light = form_data.get('screenshot_of_green_light')
            # Clear fields for the 'No' path to avoid validation errors
            doc.screening_date_time = None
            doc.screening_result = None
            doc.reason_for_late_screening = None
            doc.final_screening_screenshot = None
        elif doc.screened_before_payment == '\nNo':
            doc.screening_date_time = form_data.get('screening_date_time')
            doc.screening_result = form_data.get('screening_result')
            doc.reason_for_late_screening = form_data.get('reason_for_late_screening')
            doc.final_screening_screenshot = form_data.get('final_screening_screenshot')
            # Clear fields for the 'Yes' path
            doc.screenshot_of_green_light = None
        else:
            # Clear all conditional fields if no selection is made
            doc.screenshot_of_green_light = None
            doc.screening_date_time = None
            doc.screening_result = None
            doc.reason_for_late_screening = None
            doc.final_screening_screenshot = None

        doc.main_client_kyc_date = form_data.get('main_client_kyc_date')
        doc.main_client_kyc_file = form_data.get('main_client_kyc_file')

        # --- II. MAP DYNAMIC CHILD TABLES ---

        # A. Handle Remarks
        # Check if a remark title or description was provided to create a child table entry.
        if form_data.get('remark_title') or form_data.get('remark_description'):
            doc.append('remarks', {
                'remark_title': form_data.get('remark_title'),
                'remark_description': form_data.get('remark_description'),
                # The 'remark_files' field from the dialog contains URLs to the uploaded files,
                # which are mapped directly to the 'attachments' field in the child table.
                'attachments': form_data.get('remark_files') 
            })
        
        # B. Handle Additional Files (Optional Section)
        # Assumes a child table with fieldname 'additional_files' and fields 'title' and 'attachment'
        if form_data.get('additional_file_upload'):
             doc.append('additional_files', {
                 'file_title': form_data.get('additional_file_title'),
                 'file_upload': form_data.get('additional_file_upload')
             })

        # C. Handle Joint Owners
        raw_num_joint_owners = form_data.get('extra_joint_owners')
        num_joint_owners = int(raw_num_joint_owners) if raw_num_joint_owners and raw_num_joint_owners.isdigit() else 0
        
        for i in range(num_joint_owners):
            prefix = f'jo{i}_'
            
            doc.append('joint_owners', {
                'first_name': form_data.get(f'{prefix}first_name'),
                'last_name': form_data.get(f'{prefix}last_name'),
                'email': form_data.get(f'{prefix}email'),
                'main_phone_number': form_data.get(f'{prefix}main_phone_number'),
                'uae_phone_number': form_data.get(f'{prefix}uae_phone_number'),
                'passport_number': form_data.get(f'{prefix}passport_number'),
                'passport_expiry_date': form_data.get(f'{prefix}passport_expiry_date'),
                'date_of_birth': form_data.get(f'{prefix}date_of_birth'),
                'passport_copy': form_data.get(f'{prefix}passport_copy'),
                'home_address': form_data.get(f'{prefix}home_address'),
                'uae_address': form_data.get(f'{prefix}uae_address'),
                'country_of_origin': form_data.get(f'{prefix}country_of_origin'),
                'country_of_residence': form_data.get(f'{prefix}country_of_residence'),
                'age_range': form_data.get(f'{prefix}age_range'),
                'yearly_estimated_income': form_data.get(f'{prefix}yearly_estimated_income'),
                'kyc_date': form_data.get(f'{prefix}kyc_date'),
                'kyc_file': form_data.get(f'{prefix}kyc_file'),
            })
        receipts_data = form_data.get('receipts', [])
        if receipts_data and isinstance(receipts_data, list):
            for receipt_row in receipts_data:
                # For each dictionary in the list, append a new row to the child table.
                # This explicitly maps only the fields defined in your child Doctype.
                doc.append('receipts', {
                    'receipt_date': receipt_row.get('receipt_date'),
                    'amount': receipt_row.get('receipt_amount'),
                    'receipt_file': receipt_row.get('receipt_proof')
                })
        # --- III. SAVE THE DOCUMENT ---
        
        # Insert the document into the database
        doc.insert(ignore_permissions=True)

        # Return the name of the newly created document
        return doc.name

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Sales Registration Creation Failed")
        # Re-throw the exception to show a detailed error to the user
        frappe.throw(f"An error occurred while creating the document: {str(e)}")







# import frappe
# import json # Used to handle data from the client script

# @frappe.whitelist()
# def create_sales_registration(lead_name, data):
#     """
#     Creates a new 'Sales Registration Form' document from the data
#     submitted by the custom dialog in the Lead form.
    
#     :param lead_name: The name of the source Lead document.
#     :param data: A JSON string of the form data from the dialog.
#     """
#     try:
#         # 1. The data from JS comes as a dictionary (or a JSON string that Frappe auto-converts)
#         form_data = data if isinstance(data, dict) else frappe.parse_json(data)
#         print(form_data)
#         # 2. Create a new document for "Sales Registration Form"
#         doc = frappe.new_doc("Sales Registration Form")
#         doc.lead = lead_name

#         # --- I. MAP MAIN CLIENT & UNIT FIELDS (DIRECT MAPPING & CONDITIONAL FILTERING) ---
        
#         # General Fields (Mandatory, no specific conditional logic needed other than basic setting)
#         # Using .get() or " or None" is critical here for missing data points from JS where Frappe validation might be confused
        
#         doc.form_type = form_data.get('form_type') or None
#         doc.first_name = form_data.get('first_name') or None
#         doc.last_name = form_data.get('last_name') or None
#         doc.email = form_data.get('email') or None
#         doc.main_phone_number = form_data.get('main_phone_number') or None
#         doc.uae_phone_number = form_data.get('uae_phone_number') or None
#         doc.passport_number = form_data.get('passport_number') or None
#         doc.passport_expiry_date = form_data.get('passport_expiry_date') or None
#         doc.date_of_birth = form_data.get('date_of_birth') or None
#         doc.passport_copy = form_data.get('passport_copy') or None
#         doc.home_address = form_data.get('home_address') or None
#         doc.uae_address = form_data.get('uae_address') or None
#         doc.country_of_origin = form_data.get('country_of_origin') or None
#         doc.country_of_residence = form_data.get('country_of_residence') or None
#         doc.age_range = form_data.get('age_range') or None
#         doc.yearly_estimated_income = form_data.get('yearly_estimated_income') or None
        
#         # Unit & Sale Info Tab
#         doc.unit_sale_type = form_data.get('unit_sale_type') or None
#         doc.developer = form_data.get('developer') or None
#         doc.project = form_data.get('project') or None
#         doc.developer_sales_rep = form_data.get('developer_sales_rep') or None
#         doc.unit_number = form_data.get('unit_number') or None
#         doc.unit_type = form_data.get('unit_type') or None
#         doc.unit_price = form_data.get('unit_price') or None
#         doc.unit_area = form_data.get('unit_area') or None
#         doc.unit_view = form_data.get('unit_view') or None
#         doc.unit_floor = form_data.get('unit_floor') or None
#         doc.booking_eoi_paid_amount = form_data.get('booking_eoi_paid_amount') or None
#         doc.booking_form_upload = form_data.get('booking_form_upload') or None
#         doc.spa_upload = form_data.get('spa_upload') or None
#         doc.soa_upload = form_data.get('soa_upload') or None

#         # Screening & KYC Tab
#         doc.screened_before_payment = form_data.get('screened_before_payment') or None
        
#         # Aggressive Conditional Field Clearing: Prevent Server-Side Mandatory Check Errors
#         if doc.screened_before_payment == '\nYes':
#             # ONLY map the required 'Yes' field(s). Clear 'No' fields.
#             doc.screenshot_of_green_light = form_data.get('screenshot_of_green_light') or None
#             doc.screening_date_time = None
#             doc.screening_result = None
#             doc.reason_for_late_screening = None
#             doc.final_screening_screenshot = None
#         elif doc.screened_before_payment == '\nNo':
#             # ONLY map the required 'No' fields. Clear 'Yes' fields.
#             doc.screenshot_of_green_light = None
#             doc.screening_date_time = form_data.get('screening_date_time') or None
#             doc.screening_result = form_data.get('screening_result') or None
#             doc.reason_for_late_screening = form_data.get('reason_for_late_screening') or None
#             doc.final_screening_screenshot = form_data.get('final_screening_screenshot') or None
#         else:
#             # If nothing selected, clear all conditional fields to avoid validation errors for both paths.
#             doc.screenshot_of_green_light = None
#             doc.screening_date_time = None
#             doc.screening_result = None
#             doc.reason_for_late_screening = None
#             doc.final_screening_screenshot = None

#         doc.main_client_kyc_date = form_data.get('main_client_kyc_date') or None
#         doc.main_client_kyc_file = form_data.get('main_client_kyc_file') or None
        
#         # --- II. MAP DYNAMIC/CHILD TABLE FIELDS (JOINT OWNERS) ---
        
#         # Fix TypeError: extra_joint_owners from JS will be null if untouched.
#         raw_num_joint_owners = form_data.get('extra_joint_owners')
#         num_joint_owners = int(raw_num_joint_owners) if raw_num_joint_owners not in [None, ''] else 0
        
#         # Prepare Joint Owners
#         joint_owners_list = []
#         for i in range(num_joint_owners):
#             prefix = f'jo{i}_'
            
#             # The JS code ensures all these mandatory fields are filled if the owner count > 0
#             joint_owners_list.append({
#                 'first_name': form_data.get(f'{prefix}first_name') or None,
#                 'last_name': form_data.get(f'{prefix}last_name') or None,
#                 'email': form_data.get(f'{prefix}email') or None,
#                 'main_phone_number': form_data.get(f'{prefix}main_phone_number') or None,
#                 'uae_phone_number': form_data.get(f'{prefix}uae_phone_number') or None, # Added missing field
#                 'passport_number': form_data.get(f'{prefix}passport_number') or None,
#                 'passport_expiry_date': form_data.get(f'{prefix}passport_expiry_date') or None,
#                 'date_of_birth': form_data.get(f'{prefix}date_of_birth') or None,
#                 'passport_copy': form_data.get(f'{prefix}passport_copy') or None,
#                 'home_address': form_data.get(f'{prefix}home_address') or None,
#                 'uae_address': form_data.get(f'{prefix}uae_address') or None, # Added missing field
#                 'country_of_origin': form_data.get(f'{prefix}country_of_origin') or None, # Added missing field
#                 'country_of_residence': form_data.get(f'{prefix}country_of_residence') or None, # Added missing field
#                 'age_range': form_data.get(f'{prefix}age_range') or None, # Added missing field
#                 'yearly_estimated_income': form_data.get(f'{prefix}yearly_estimated_income') or None, # Added missing field
#                 'kyc_date': form_data.get(f'{prefix}kyc_date') or None,
#                 'kyc_file': form_data.get(f'{prefix}kyc_file') or None,
#             })
            
#         doc.set('joint_owners', joint_owners_list) # Use doc.set for a clear list setting

#         # Insert the document into the database
#         doc.insert(ignore_permissions=True)

#         # Return the name of the newly created document
#         return doc.name

#     except frappe.MandatoryError as e:
#         # CRITICAL FIX: The Python error contains the entire list, so re-raise it
#         # so the browser handles the error object correctly and finds the list of fields.
#         frappe.throw(f"Mandatory fields are missing or not correctly mapped in server API: {str(e)}", title="Submission Failed")
        
#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "Sales Registration Creation Failed")
#         frappe.throw(str(e)) # Generic error re-raise


import frappe
from frappe.model.document import Document
@frappe.whitelist()
def update_sales_registration_details(doc_name: str, data: str):
    print(doc_name)
    print(data)
    """
    Updates a Sales Registration Form document with new values, including child tables.
    :param doc_name: The name of the Sales Registration Form to update.
    :param data: A JSON string containing the fields to update.
    """
    try:
        # Decode the incoming data from JSON string to a Python dictionary
        update_data = frappe.parse_json(data)

        # Load the existing document
        doc = frappe.get_doc("Sales Registration Form", doc_name)
        
        # Check permissions and document status (only drafts can be heavily modified)
        if not doc.has_permission("write"):
            frappe.throw("You do not have permission to write to this document.", frappe.PermissionError)

        if doc.docstatus != 0:
            # For submitted docs, you might only allow certain fields to be changed
            # For this example, we only allow changes if it's a draft.
            frappe.throw("Only draft documents can be edited in this manner.")
            
        # Update main document fields (excluding child tables)
        main_fields = {k: v for k, v in update_data.items() if k not in ['joint_owners', 'remarks', 'receipts', 'additional_files']}
        doc.update(main_fields)

        # Handle joint_owners child table
        if "joint_owners" in update_data:
            doc.set("joint_owners", [])  # Clear existing child table entries
            for owner_entry in update_data["joint_owners"]:
                doc.append("joint_owners", owner_entry)

        # Handle remarks child table
        if "remarks" in update_data:
            doc.set("remarks", [])  # Clear existing child table entries
            for remark_entry in update_data["remarks"]:
                doc.append("remarks", {
                    "remark_title": remark_entry.get("remark_title"),
                    "remark_description": remark_entry.get("remark_description"),
                    "attachments": remark_entry.get("attachments"),
                })

        # Handle receipts child table
        if "receipts" in update_data:
            doc.set("receipts", [])  # Clear existing child table entries
            for receipt_entry in update_data["receipts"]:
                doc.append("receipts", {
                    "receipt_date": receipt_entry.get("receipt_date"),
                    "amount": receipt_entry.get("amount"),
                    "receipt_file": receipt_entry.get("receipt_file"),
                })

        # If 'additional_files' child table data is present, update it
        if "additional_files" in update_data:
            doc.set("additional_files", []) # Clear existing child table entries
            for file_entry in update_data["additional_files"]:
                doc.append("additional_files", {
                    "file_title": file_entry.get("file_title"),
                    "file_upload": file_entry.get("file_upload"),
                })
        
        # Save the document to the database
        doc.save(ignore_permissions=True) # Permissions already checked

        return doc.as_dict()

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Sales Registration Update Error")
        frappe.throw(f"An error occurred while saving: {e}")


# Add this to the same file as your other whitelisted methods
import frappe
import json
from frappe.model.document import Document
from frappe import _

# This function is being updated to clear rejection data upon re-submission.
@frappe.whitelist()
def submit_for_approval(doc_name: str):
    try:
        doc = frappe.get_doc("Sales Registration Form", doc_name)

        # if not doc.has_permission("submit"):
        #     frappe.throw(_("You do not have permission to submit this document."), frappe.PermissionError)

        # if doc.docstatus != 0:
        #     frappe.throw(_("This document cannot be sent for approval again."))
        
        # --- NEW LOGIC FOR RE-SUBMISSION ---
        # If the document was previously rejected, clear the old rejection data.
        if doc.status == "Rejected":
            doc.set("rejection_details", [])  # Clear the child table
            doc.rejected_fields_json = None         # Clear the JSON field
        # --- END NEW LOGIC ---

        doc.status = "Awaiting Review"
        doc.save(ignore_permissions=True)

        return {"status": "success", "message": "Document successfully sent for approval."}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Approval Submission Error")
        frappe.throw(f"An error occurred: {e}")

# @frappe.whitelist()
# def approve_registration(doc_name: str, commission_percentage: float):
#     if not (frappe.user.has_role("Admin") or frappe.user.has_role("Super Admin")):
#         frappe.throw(_("You do not have permissions to approve this."), frappe.PermissionError)

#     doc = frappe.get_doc("Sales Registration Form", doc_name)
#     if doc.status != "Awaiting Review":
#         frappe.throw(f"Cannot approve a document with status '{doc.status}'.")

#     doc.status = "Approved"
#     doc.commission_percentage = commission_percentage
#     doc.save(ignore_permissions=True)
#     return {"status": "success", "message": "Registration has been approved."}


# This function is completely new to handle the detailed rejection.
@frappe.whitelist()
def reject_registration_with_details(doc_name: str, rejection_data: str):
    """
    Rejects a registration and logs specific field errors in a child table.
    'rejection_data' is a JSON string of a list of objects.
    e.g., '[{"field_name": "passport_number", "field_label": "Passport Number", "description": "Scan is blurry", ...}]'
    """
    if not (frappe.user.has_role("Admin") or frappe.user.has_role("Super Admin")):
        frappe.throw(_("You do not have permissions to reject this."), frappe.PermissionError)

    doc = frappe.get_doc("Sales Registration Form", doc_name)
    if doc.status != "Awaiting Review":
        frappe.throw(f"Cannot reject a document with status '{doc.status}'.")

    details = json.loads(rejection_data)
    
    if not details:
        frappe.throw(_("You must select at least one field and provide a reason for rejection."))

    # Get a simple list of fieldnames to highlight on the front-end
    rejected_field_names = [d.get("field_name") for d in details]

    # Update the document
    doc.status = "Rejected"
    doc.rejected_fields_json = json.dumps(rejected_field_names)
    
    # Clear old entries and add new ones
    doc.set("rejection_details", [])
    for detail in details:
        doc.append("rejection_details", {
            "field_name": detail.get("field_name"),
            "field_label": detail.get("field_label"),
            "description": detail.get("description"),
            "fine_amount": detail.get("fine_amount"),
            "due_date": detail.get("due_date"),
        })

    doc.save(ignore_permissions=True)
    return {"status": "success", "message": "Registration has been rejected with details."}
@frappe.whitelist()
def get_sales_reg_name_and_status_field(lead_name):
    """
    Checks for Sales Registration existence and safely fetches its current 
    name and the value of its custom 'status' field (bypassing client DocType security for specific fields).
    """
    sales_reg_name = frappe.db.get_value("Sales Registration Form", {"lead": lead_name}, "name")
    
    if sales_reg_name:
        # **Using the user-defined 'status' field name here**
        status = frappe.db.get_value("Sales Registration Form", sales_reg_name, "status") 
        return {"name": sales_reg_name, "status": status}
    
    return {"name": None, "status": None}

# @frappe.whitelist()
# def submit_for_approval(doc_name):
#     """Sets the document status to 'Awaiting Review'."""
#     try:
#         doc = frappe.get_doc("Sales Registration Form", doc_name)
#         doc.rejection_reason = None
#         doc.rejected_fields = None
#         doc.status = "Awaiting Review"
#         doc.save(ignore_permissions=True)
#         doc.add_comment("Submitted for review.")
#         return doc.status
#     except Exception as e:
#         frappe.throw(f"Could not submit for approval: {str(e)}")


# copyright and imports if any

@frappe.whitelist()
def approve_registration(doc_name, developer_commission_percentage, agent_commission_percentage, commission_status):
    """
    Approves the Sales Registration Form, sets status to 'Approved',
    records the developer and agent commission percentages and initial commission status,
    clears rejection-related fields,
    logs the approval action in remarks,
    and updates the associated Lead's custom_lead_status to 'Closed'.
    Also updates the Lead with commission details and calculated amounts.
    
    :param doc_name: The name of the Sales Registration Form document (str).
    :param developer_commission_percentage: The developer commission percentage (float).
    :param agent_commission_percentage: The agent commission percentage of developer commission (float).
    :param commission_status: The initial commission status (str).
    :returns: Success message.
    """
    
    # --- 1. Permissions Check ---
    allowed_roles = ["System Manager", "Administrator", "Admin"]
    user_roles = frappe.get_roles(frappe.session.user) 
    is_authorized = any(role in user_roles for role in allowed_roles)

    if not is_authorized:
        frappe.throw(frappe._("You are not permitted to approve Sales Registration Forms."))
    
    # --- 2. Fetch the document ---
    try:
        doc = frappe.get_doc("Sales Registration Form", doc_name)
    except frappe.DoesNotExistError:
        frappe.throw(frappe._("Sales Registration Form {0} not found.").format(doc_name))
        
    # --- 3. Validate Status ---
    if doc.status != "Awaiting Review":
        frappe.throw(frappe._("Only 'Awaiting Review' documents can be approved."))

    # --- 4. Validate Commission Percentages ---
    try:
        developer_commission_percentage = float(developer_commission_percentage)
        agent_commission_percentage = float(agent_commission_percentage)
    except (ValueError, TypeError):
        frappe.throw(frappe._("Invalid commission percentage values. They must be valid numbers."))
    
    if developer_commission_percentage <= 0 or developer_commission_percentage > 100:
        frappe.throw(frappe._("Developer commission percentage must be between 0 and 100 (exclusive)."))
    
    if agent_commission_percentage <= 0 or agent_commission_percentage > 100:
        frappe.throw(frappe._("Agent commission percentage must be between 0 and 100 (exclusive)."))
    
    # --- 5. Validate Commission Status ---
    allowed_status = [
        'Invoice Awaiting Payment',
        'Commission Partially Received From Developer',
        'Commission Fully Received From Developer',
        'Commission Paid Partially to Agent',
        'Commission Paid Fully to Agent'
    ]
    if commission_status not in allowed_status:
        frappe.throw(frappe._("Invalid commission status. Must be one of: {0}").format(', '.join(allowed_status)))
    
    # --- 6. Update Approval Details ---
    doc.status = "Approved"
    doc.developer_commission_percentage = developer_commission_percentage
    doc.agent_commission_percentage = agent_commission_percentage
    doc.commission_status = commission_status
    doc.approved_on = frappe.utils.now()
    doc.approved_by = frappe.session.user
    
    # Clear rejection-related fields
    doc.rejected_fields_json = ""
    doc.last_rejected_fields_json = ""
    doc.rejection_reason = ""
    # rejection_count remains as historical data
    
    # --- 7. Log Approval in Remarks ---
    current_datetime = frappe.utils.now()
    ip_address = frappe.local.request_ip
    user = frappe.session.user
    log_description = (
        f"Admin {user} approved the registration on {current_datetime} from IP {ip_address} "
        f"with Developer Commission {developer_commission_percentage}%, "
        f"Agent Commission {agent_commission_percentage}% (of Developer Commission), "
        f"Initial Status: {commission_status}."
    )
    remark = doc.append("remarks", {})
    remark.remark_title = "System Log: Approval"
    remark.remark_description = log_description
    
    # --- 8. Save Sales Registration ---
    doc.save(ignore_permissions=True)
    
    # --- 9. Update Associated Lead ---
    if doc.lead:
        try:
            lead = frappe.get_doc("Lead", doc.lead)
            lead.custom_lead_status = "Closed"
            lead.custom_developer_commission_percentage = developer_commission_percentage
            lead.custom_agent_commission_percentage = agent_commission_percentage
            lead.custom_commission_status = commission_status
            total_commission = doc.unit_price * (developer_commission_percentage / 100)
            lead.custom_total_commission = total_commission
            total_fines = lead.custom_total_fine_amount or 0
            lead.custom_agent_commission = total_commission * (agent_commission_percentage / 100) - total_fines
            lead.save(ignore_permissions=True)
        except frappe.DoesNotExistError:
            frappe.log_error(title="Lead Update Error", message=f"Lead {doc.lead} not found for Sales Registration {doc_name}")
    
    # --- 10. Commit ---
    frappe.db.commit()

    # --- 11. Return Success Message ---
    return {
        "status": "success",
        "message": frappe._("Sales Registration Form {0} has been approved with Developer Commission {1}%, Agent Commission {2}%, Status: {3}, and associated Lead updated to Closed.").format(
            doc_name, developer_commission_percentage, agent_commission_percentage, commission_status
        )
    }

# @frappe.whitelist()
# def reject_registration(doc_name: str, rejection_reason: str):
#     """
#     Rejects a Sales Registration Form. Restricted to Admin and Super Admin roles.
#     """
#     # 1. CORRECTED Security Check: Ensure the user is Admin OR Super Admin
#     user_roles = frappe.get_roles()
#     if "Admin" not in user_roles and "Super Admin" not in user_roles:
#         frappe.throw(
#             _("You do not have the required permissions to reject this document."),
#             frappe.PermissionError
#         )

#     try:
#         doc = frappe.get_doc("Sales Registration Form", doc_name)

#         if doc.status != "Awaiting Review":
#             frappe.throw(f"This document is in '{doc.status}' status and cannot be rejected.")

#         doc.status = "Rejected"
#         # Note: Ensure you have the 'rejection_reason' field in your DocType
#         doc.rejection_reason = rejection_reason 
        
#         doc.save(ignore_permissions=True)

#         return {"status": "success", "message": "Registration has been rejected."}

#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "Reject Registration Error")
#         frappe.throw(f"An error occurred: {e}")



@frappe.whitelist()
def get_sales_registration_fines(lead_name):
    """Fetches fine details and total fine amount from the linked Sales Registration."""
    try:
        # 1. Find the linked Sales Registration document.
        # Assuming Sales Registration is linked to Lead by a 'lead' field.
        sales_reg_name = frappe.db.get_value(
            "Sales Registration Form",
            {"lead": lead_name} # Ensure only Submitted docs are considered
        )
        
        if not sales_reg_name:
            return {'fines': [], 'total_fine_amount': 0}

        # 2. Fetch fines from the Sales Registration Fine child table.
        fines = frappe.db.get_all(
            "Sales Registration Form Fine",
            filters={"parent": sales_reg_name},
            fields=["fine_date", "fine_description", "fine_amount", "name"],
            order_by="fine_date desc"
        )
        print('ssssssssssssssssssssssssssssssssssssssssss',fines)
        # 3. Calculate total fine amount.
        total_fine_amount = sum(frappe.utils.flt(f.get('fine_amount')) for f in fines)

        return {
            'fines': fines,
            'total_fine_amount': total_fine_amount
        }

    except Exception:
        frappe.log_error(frappe.utils.get_traceback(), "Get Sales Registration Fines Error")
        return {'fines': [], 'total_fine_amount': 0}



# In joel_living.custom_lead.py

import frappe

@frappe.whitelist()
def get_sales_registration_docname_for_lead(lead_name):
    """
    Finds the submitted Sales Registration linked to a Lead.
    Assumes Sales Registration has a link field 'lead' to the Lead doctype.
    """
    if not lead_name:
        return None
        
    sales_reg_name = frappe.db.get_value(
        "Sales Registration Form",  # Use your correct Sales Registration DocType Name
        filters={
            "lead": lead_name        # NOTE: This MUST match the name of the link field in your Sales Registration
                      # Only submitted documents (Optional: based on requirement)
        },
        fieldname="name",
        order_by="creation desc"
    )
    return sales_reg_name


# --- CONSTANTS ---
SALES_REG_DOCTYPE = "Sales Registration Form"
# -----------------
import frappe
import json
from frappe.utils import cstr, get_fullname, format_datetime
from collections import defaultdict

@frappe.whitelist()
def get_sales_registration_activity_history(sales_reg_docname):
    """
    Fetches full activity from Version DocType, parsing data for root/child changes.
    Handles grouping for multiple row removals/additions per table.
    """
    try:
        if not sales_reg_docname: return []
        history = frappe.get_all(
            "Version",
            filters={"ref_doctype": SALES_REG_DOCTYPE, "docname": sales_reg_docname},
            fields=["name", "creation", "owner", "data", "custom_ip_address"],
            order_by="creation desc",
            as_list=False
        )
        if not history: return []
       
        meta = frappe.get_meta(SALES_REG_DOCTYPE)
        field_label_map = {df.fieldname: df.label for df in meta.fields}
       
        processed_history = []
        for version in history:
            changes = []
            try: 
                data = json.loads(version.data)
            except Exception: 
                data = {}
           
            # Parse 'changed' array (root field updates)
            if data.get('changed'):
                for change in data.get('changed'):
                    if isinstance(change, list) and len(change) >= 3:
                        field_name = change[0]
                        old_value = cstr(change[1])
                        new_value = cstr(change[2])
                    else:
                        field_name = change.get('fieldname', '') if isinstance(change, dict) else ''
                        old_value = cstr(change.get('old', ''))
                        new_value = cstr(change.get('new', ''))
                   
                    if not field_name: continue
                   
                    field_obj = meta.get_field(field_name)
                   
                    # Root field update
                    if field_obj and field_obj.fieldtype not in ('Table', 'Table MultiSelect'):
                        changes.append({
                            'type': 'Field Update',
                            'field_label': field_label_map.get(field_name, field_name.replace('_', ' ').title()),
                            'old_value': old_value,
                            'new_value': new_value
                        })
           
            # Parse 'row_changed' for child table cell updates
            if data.get('row_changed'):
                for row_change_entry in data.get('row_changed'):
                    if isinstance(row_change_entry, list) and len(row_change_entry) >= 4:
                        table_field = row_change_entry[0]
                        row_idx = row_change_entry[1]
                        row_name = row_change_entry[2]
                        sub_changes = row_change_entry[3]
                        
                        table_obj = meta.get_field(table_field)
                        if table_obj and table_obj.fieldtype in ('Table', 'Table MultiSelect'):
                            child_doctype = table_obj.options
                            table_label = field_label_map.get(table_field, table_field.replace('_', ' ').title())
                            
                            try:
                                child_meta = frappe.get_meta(child_doctype)
                                child_field_map = {d.fieldname: d.label for d in child_meta.fields if not d.hidden}
                            except:
                                child_field_map = {}
                            
                            if isinstance(sub_changes, list):
                                for sub_change in sub_changes:
                                    if isinstance(sub_change, list) and len(sub_change) >= 3:
                                        sub_field = sub_change[0]
                                        old_value = cstr(sub_change[1])
                                        new_value = cstr(sub_change[2])
                                        
                                        sub_label = child_field_map.get(sub_field, sub_field.replace('_', ' ').title())
                                        full_label = f"{table_label} > Row #{row_idx} > {sub_label}"
                                        changes.append({
                                            'type': 'Field Update',
                                            'field_label': full_label,
                                            'old_value': old_value,
                                            'new_value': new_value
                                        })
           
            # Grouped parsing for 'added' and 'removed' (multiple rows per table)
            added_groups = defaultdict(list)
            removed_groups = defaultdict(list)
           
            if data.get('added'):
                for add_entry in data.get('added'):
                    if isinstance(add_entry, dict) and 'doctype' in add_entry and 'row' in add_entry:
                        child_doctype = add_entry['doctype']
                        row = add_entry['row']
                        parentfield = None
                        for df in meta.fields:
                            if df.fieldtype == 'Table' and df.options == child_doctype:
                                parentfield = df.fieldname
                                break
                        if parentfield:
                            added_groups[parentfield].append(row)
           
            if data.get('removed'):
                for rem_entry in data.get('removed'):
                    if isinstance(rem_entry, dict) and 'doctype' in rem_entry and 'row' in rem_entry:
                        child_doctype = rem_entry['doctype']
                        row = rem_entry['row']
                        parentfield = None
                        for df in meta.fields:
                            if df.fieldtype == 'Table' and df.options == child_doctype:
                                parentfield = df.fieldname
                                break
                        if parentfield:
                            removed_groups[parentfield].append(row)
           
            # Add grouped entries
            for parentfield, rows in added_groups.items():
                table_label = field_label_map.get(parentfield, parentfield.replace('_', ' ').title())
                row_count = len(rows)
                detail = f"{row_count} row{'s' if row_count > 1 else ''}"
                if row_count == 1:
                    row = rows[0]
                    row_idx = row.get('idx', row.get('name', 'N/A'))
                    detail = f"Row #{row_idx}"
                    try:
                        child_meta = frappe.get_meta(meta.get_field(parentfield).options)
                        child_field_map = {d.fieldname: d.label for d in child_meta.fields if not d.hidden}
                        for k, v in row.items():
                            if k in child_field_map and v and k not in ('name', 'idx', 'doctype', 'parent', 'parentfield', 'parenttype'):
                                detail += f" - {child_field_map[k]}: {v}"
                                break
                    except:
                        pass
                changes.append({
                    'type': 'Row Added',
                    'details': f"Added {detail} to **{table_label}**"
                })
           
            for parentfield, rows in removed_groups.items():
                table_label = field_label_map.get(parentfield, parentfield.replace('_', ' ').title())
                row_count = len(rows)
                detail = f"{row_count} row{'s' if row_count > 1 else ''}"
                if row_count == 1:
                    row = rows[0]
                    row_idx = row.get('idx', row.get('name', 'N/A'))
                    detail = f"Row #{row_idx}"
                    try:
                        child_meta = frappe.get_meta(meta.get_field(parentfield).options)
                        child_field_map = {d.fieldname: d.label for d in child_meta.fields if not d.hidden}
                        for k, v in row.items():
                            if k in child_field_map and v and k not in ('name', 'idx', 'doctype', 'parent', 'parentfield', 'parenttype'):
                                detail += f" - {child_field_map[k]}: {v}"
                                break
                    except:
                        pass
                changes.append({
                    'type': 'Row Removed',
                    'details': f"Removed {detail} from **{table_label}**"
                })
           
            # System comments (e.g., "You last edited this")
            if data.get('comment'):
                changes.append({
                    'type': 'System/Comment',
                    'field_label': 'Activity',
                    'old_value': '',
                    'new_value': data['comment']
                })
           
            # --- Compile final entry ---
            owner_name = version.owner
            processed_history.append({
                'owner_fullname': get_fullname(owner_name),
                'creation_formatted': format_datetime(version.creation, "dd-MMM-yyyy HH:mm:ss"),
                'changes': changes,
                'ip_address': version.get('custom_ip_address') or 'N/A'
            })
           
            # Simplified Debug
            if not changes and data:
                frappe.log_error(f"No changes parsed for version {version.name[:20] if version.name else 'None'}", "History Debug - Child Table")
           
        return processed_history
    except Exception:
        frappe.log_error(frappe.utils.get_traceback(), f"Error fetching {SALES_REG_DOCTYPE} history")
        return []

@frappe.whitelist()
def set_version_ip_address(doc, method=None):
    """
    Sets the client's IP address on the custom field 'custom_ip_address' of the Version document.
    """
    if doc.doctype != "Version":
        return

    ip_address = None
    # Use frappe.request.remote_addr which is more commonly available
    if hasattr(frappe.request, 'remote_addr'):
        ip_address = frappe.request.remote_addr
    
    # Fallback to a clear marker if the request object or IP is missing (e.g., if called via scheduler or CLI)
    doc.custom_ip_address = ip_address or 'Server-Side/CLI/Unknown' 

@frappe.whitelist()
def reject_sales_registration(doc_name, rejected_fields_json, rejection_reason, fine_amount, fine_description, fine_date):
    """
    Rejects the Sales Registration Form, sets status to 'Rejected',
    records the rejection details and fine,
    logs the rejection action in remarks,
    and immediately updates the associated Lead's custom_total_fine_amount with the new total.
    
    :param doc_name: The name of the Sales Registration Form document (str).
    :param rejected_fields_json: JSON string of rejected fields (str).
    :param rejection_reason: The reason for rejection (str).
    :param fine_amount: The fine amount (float).
    :param fine_description: The fine description (str).
    :param fine_date: The fine date (str, optional).
    :returns: Success message or error.
    """
    
    # --- 1. Permissions Check ---
    allowed_roles = ["System Manager", "Administrator", "Admin"]
    user_roles = frappe.get_roles(frappe.session.user) 
    is_authorized = any(role in user_roles for role in allowed_roles)

    if not is_authorized:
        frappe.throw(frappe._("You are not permitted to reject Sales Registration Forms."))
    
    # --- 2. Fetch the document ---
    try:
        doc = frappe.get_doc("Sales Registration Form", doc_name)
    except frappe.DoesNotExistError:
        frappe.throw(frappe._("Sales Registration Form {0} not found.").format(doc_name))
        
    # --- 3. Validate Status ---
    if doc.status != "Awaiting Review":
        frappe.throw(frappe._("Only 'Awaiting Review' documents can be rejected."))

    # --- 4. Validate Inputs ---
    if not rejection_reason:
        frappe.throw(frappe._("Rejection reason is required."))
    
    try:
        fine_amount = float(fine_amount)
    except (ValueError, TypeError):
        frappe.throw(frappe._("Invalid fine amount. It must be a valid number."))
    
    if fine_amount <= 0:
        frappe.throw(frappe._("Fine amount must be greater than 0."))
    
    if not fine_description:
        frappe.throw(frappe._("Fine description is required."))
    
    if not fine_date:
        fine_date = frappe.utils.nowdate()
    
    try:
        rejected_fields = frappe.utils.json.loads(rejected_fields_json)
    except ValueError:
        frappe.throw(frappe._("Invalid rejected fields JSON."))
    
    if not rejected_fields or (len(rejected_fields.get('main', [])) == 0 and len(rejected_fields.get('additional_files', {})) == 0 and len(rejected_fields.get('remarks_rows', [])) == 0 and len(rejected_fields.get('receipts_rows', [])) == 0):
        frappe.throw(frappe._("At least one field must be selected for rejection."))
    
    # --- 5. Update Rejection Details ---
    doc.status = "Rejected"
    doc.rejected_fields_json = rejected_fields_json
    doc.last_rejected_fields_json = rejected_fields_json  # For audit
    doc.rejection_reason = rejection_reason
    doc.rejection_count = (doc.rejection_count or 0) + 1
    doc.rejected_on = frappe.utils.now()
    doc.rejected_by = frappe.session.user
    
    # --- 6. Add Fine to Child Table ---
    fine = doc.append("sales_registration_fines", {})
    fine.fine_date = fine_date
    fine.fine_description = fine_description
    fine.fine_amount = fine_amount
    
    # --- 7. Log Rejection in Remarks ---
    current_datetime = frappe.utils.now()
    ip_address = frappe.local.request_ip
    user = frappe.session.user
    log_description = (
        f"Admin {user} rejected the registration on {current_datetime} from IP {ip_address}. "
        f"Reason: {rejection_reason}. "
        f"Fine: AED {fine_amount:.2f}, Description: {fine_description}, Date: {fine_date}."
    )
    remark = doc.append("remarks", {})
    remark.remark_title = "System Log: Rejection"
    remark.remark_description = log_description
    
    # --- 8. Save Sales Registration ---
    doc.save(ignore_permissions=True)
    
    # --- 9. Calculate Total Fines and Update Lead ---
    if doc.lead:
        try:
            lead = frappe.get_doc("Lead", doc.lead)
            total_fines = sum(f.fine_amount for f in doc.sales_registration_fines)
            lead.custom_total_fine_amount = total_fines
            # Optionally update custom_fine_details HTML here if needed
            html = '<table class="table table-sm"><thead><tr><th>Date</th><th>Description</th><th>Amount (AED)</th></tr></thead><tbody>'
            for fine in doc.sales_registration_fines:
                html += f'<tr><td>{fine.fine_date or ""}</td><td>{fine.fine_description or ""}</td><td>{fine.fine_amount or 0}</td></tr>'
            html += '</tbody></table><p><strong>Total Fine: AED ' + f'{total_fines:.2f}' + '</strong></p>'
            lead.custom_fine_details = html
            lead.save(ignore_permissions=True)
        except frappe.DoesNotExistError:
            frappe.log_error(title="Lead Update Error", message=f"Lead {doc.lead} not found for Sales Registration {doc_name}")
    
    # --- 10. Commit ---
    frappe.db.commit()

    # --- 11. Return Success Message ---
    return {
        "status": "success",
        "message": frappe._("Sales Registration Form {0} has been rejected. Fine added and Lead updated with total fine AED {1:.2f}.").format(doc_name, fine_amount)
    }
# @frappe.whitelist()
# def reject_registration(doc_name, reason, rejected_fields):
#     """Sets status to 'Rejected', increments count, and logs reasons."""
#     if not reason: frappe.throw("A reason for rejection is required.")
#     if not rejected_fields: frappe.throw("You must select at least one field that needs correction.")
#     try:
#         doc = frappe.get_doc("Sales Registration Form", doc_name)
#         doc.status = "Rejected"
#         doc.rejection_reason = reason
#         doc.rejected_fields = json.dumps(rejected_fields if isinstance(rejected_fields, list) else [])
#         doc.rejection_count = cint(doc.rejection_count) + 1
#         doc.save(ignore_permissions=True)
#         doc.add_comment(f"Rejected. Reason: {reason}")
#         return doc.status
#     except Exception as e:
#         frappe.throw(f"Could not reject document: {str(e)}")

# This function is used by the refresh trigger on the Lead form
import frappe

@frappe.whitelist()
def get_sales_registration_for_lead(lead_name):
    try:
        # Your existing logic, e.g.:
        sr = frappe.get_all("Sales Registration Form", filters={"lead": lead_name}, fields=["name", "status"])
        if sr:
            return frappe.get_doc("Sales Registration Form", sr[0].name).as_dict()
        return None
    except Exception as e:
        frappe.log_error(f"Sales Reg Error for {lead_name}: {str(e)}", "Sales Registration Lookup")
        return {"exc": str(e)}

@frappe.whitelist()
def update_and_log_registration(docname, changes, user):
    """Update editable file fields and create a log entry."""
    import json

    doc = frappe.get_doc("Sales Registration Form", docname)
    changes = frappe._dict(json.loads(changes)) if isinstance(changes, str) else frappe._dict(changes)
    updated_fields = []

    for field, value in changes.items():
        if doc.get(field) != value:
            doc.set(field, value)
            updated_fields.append(field)

    if updated_fields:
        doc.save(ignore_permissions=True)

        # Log update in a custom Log doctype or Comment
        frappe.get_doc({
            "doctype": "Comment",
            "comment_type": "Info",
            "reference_doctype": "Sales Registration Form",
            "reference_name": docname,
            "content": f"Updated by {user}: {', '.join(updated_fields)}"
        }).insert(ignore_permissions=True)

    return {"success": True, "updated_fields": updated_fields}




# ==============================================================================
# 3. FUNCTIONS FOR THE ADMIN REVIEW DIALOG (Approve/Reject actions)
#    (These are from your more complex script and included for completeness)
# ==============================================================================
@frappe.whitelist()
def admin_review_action(doc_name, action, finance_data):
    """
    Handles admin actions like 'Approve' and saves financial/commission data.
    """
    doc = frappe.get_doc("Sales Registration Form", doc_name)
    
    # Update all the finance and commission fields from the dialog
    doc.update(finance_data)
    
    # Set the new status
    doc.status = action # e.g., 'Approved'
    
    # Add a comment to the document's timeline for auditing
    doc.add_comment('Comment', text=f"Document status set to '{action}' by Admin.")
    
    doc.save(ignore_permissions=True)
    return {"status": "success", "message": f"Document {doc.name} has been {action}."}


@frappe.whitelist()
def update_and_set_fields_to_reject(doc_name, reject_reason, correction_fields_newline, set_status='Rejected'):
    """
    Updates the document status to Rejected and logs the reason.
    """
    doc = frappe.get_doc("Sales Registration Form", doc_name)
    doc.status = set_status
    doc.reject_reason = reject_reason
    doc.correction_fields = correction_fields_newline # The list of fields for the agent to correct
    
    # Add a detailed comment for the agent and for auditing purposes
    doc.add_comment('Comment', text=f"Document Rejected by Admin. Reason: {reject_reason}")
    
    doc.save(ignore_permissions=True)
    return {"status": "success", "message": "Document has been rejected and agent notified."}

@frappe.whitelist()
def get_project_floor_details(project_name):
    """
    Given the name of a 'Project List' document, fetches the number of floors
    and whether it includes a mezzanine floor and a ground floor.

    :param project_name: The name of the project to look up.
    :return: A dictionary with 'no_of_floors', 'include_mezzanine_floor', and 'include_ground_floor'.
    """
    if not project_name or not frappe.db.exists("Project List", project_name):
        # Return a dictionary with 0s/False defaults if project is not found or project_name is None
        return {
            "no_of_floors": 0,
            "include_mezzanine_floor": 0,
            "include_ground_floor": 0
        }

    details = frappe.get_value(
        "Project List",
        project_name,
        ["no_of_floors", "include_mezzanine_floor", "include_ground_floor"],
        as_dict=1
    )
    if details is None:
        return {
            "no_of_floors": 0,
            "include_mezzanine_floor": 0,
            "include_ground_floor": 0
        }

    return details
