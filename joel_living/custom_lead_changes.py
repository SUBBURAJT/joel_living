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

#             # 🚫 Backend restriction: Prevent hiding Completed / Closed leads
#             status = frappe.db.get_value("Lead", lead, "custom_lead_status")
#             if status in ["Sales Completed", "Closed"]:
#                 return {
#                     "ok": False,
#                     "message": f"Cannot hide Lead {lead}. Status is {status}, hide not allowed."
#                 }

#             req_doc = frappe.get_doc({
#                 "doctype": "Lead Hide Request",
#                 "lead": lead,
#                 "requested_by": full_name,
#                 "requested_by_user": current_user,
#                 "requested_date": frappe.utils.now_datetime(),
#                 "status": "Pending"
#             })
#             req_doc.insert(ignore_permissions=True)

#             frappe.db.set_value("Lead", lead, {
#                 "lead_owner": None,
#                 "custom_hide_status": "Pending",
#                 "custom_is_hidden": 1
#             })

#             processed_leads.append(lead)

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

#         lead_list_str = ", ".join(processed_leads)
#         frappe.msgprint(f"Hide request submitted successfully for: {lead_list_str}")

#         return {"ok": True, "message": f"Hide request submitted successfully for: {lead_list_str}"}

#     except Exception as e:
#         frappe.log_error(f"Hide request failed for {leads}: {str(e)}")
#         return {"ok": False, "message": "Failed to submit hide request. Try again later."}

# # # =========================================================
# # # SALES AGENT — REQUEST HIDE
# # # =========================================================
# # @frappe.whitelist()
# # def request_hide(leads):
# #     """
# #     Sales Agent requests to hide one or more Leads.
# #     Sends ONLY system (in-app) notifications to all Admins.
# #     """
# #     current_user = frappe.session.user
# #     full_name = frappe.utils.get_fullname(current_user)

# #     try:
# #         # Ensure leads is a list
# #         if isinstance(leads, str):
# #             try:
# #                 leads = frappe.parse_json(leads)
# #                 if isinstance(leads, str):
# #                     leads = [leads]
# #             except Exception:
# #                 leads = [leads]

# #         processed_leads = []

# #         # Get all Admin users
# #         admins = {"Administrator"}
# #         role_holders = frappe.get_all("Has Role", filters={"role": "Admin"}, fields=["parent"])
# #         admins.update({r.parent for r in role_holders})

# #         # Process each lead
# #         for lead in leads:
# #             # 🚫 Backend protection: Block hide for Completed or Closed leads
# #             status = frappe.db.get_value("Lead", lead, "custom_lead_status")
# #             if status in ["Sales Completed", "Closed"]:
# #                 return {
# #                     "ok": False,
# #                     "message": f"Cannot hide Lead {lead}. Status is {status}, hide not allowed."
# #                 }
# #             req_doc = frappe.get_doc({
# #                 "doctype": "Lead Hide Request",
# #                 "lead": lead,
# #                 "requested_by": full_name,
# #                 "requested_by_user": current_user,
# #                 "requested_date": frappe.utils.now_datetime(),
# #                 "status": "Pending"
# #             })
# #             req_doc.insert(ignore_permissions=True)

# #             # ✅ Update Lead to make it completely hidden
# #             frappe.db.set_value("Lead", lead, {
# #                 "lead_owner": None,
# #                 "custom_hide_status": "Pending",
# #                 "custom_is_hidden": 1  # Mark lead as hidden (excluded from all lists)
# #             })

# #             processed_leads.append(lead)

# #             # Send in-app notification to all Admins
# #             for admin_user in admins:
# #                 frappe.enqueue(
# #                     create_notification,
# #                     queue="long",
# #                     timeout=600,
# #                     user=admin_user,
# #                     subject=f"Lead Hide Request from {full_name}",
# #                     message=f"{full_name} has requested to hide the Lead <b>{lead}</b>.<br><br>"
# #                             f"The request is awaiting your review and approval.",
# #                     ref_doctype="Lead Hide Request",
# #                     ref_name=req_doc.name,
# #                     send_email=False
# #                 )

# #         frappe.db.commit()

# #         # ✅ Show all processed leads in a popup
# #         lead_list_str = ", ".join(processed_leads)
# #         frappe.msgprint(f"Hide request submitted successfully for: {lead_list_str}")

# #         return {"ok": True, "message": f"Hide request submitted successfully for: {lead_list_str}"}

# #     except Exception as e:
# #         frappe.log_error(f"Hide request failed for {leads}: {str(e)}")
# #         return {"ok": False, "message": "Failed to submit hide request. Try again later."}


# # =========================================================
# # ADMIN ACTION — APPROVE HIDE
# # =========================================================

# # @frappe.whitelist()
# # def approve_hide_request(docname):
# #     """Approve a hide request (Admin or Administrator only)."""
# #     try:
# #         req = frappe.get_doc("Lead Hide Request", docname)
# #         current_user = frappe.session.user
# #         approver_full_name = frappe.utils.get_fullname(current_user)

# #         if req.status != "Pending":
# #             return {"ok": False, "message": "Only Pending requests can be approved."}

# #         lead_id = req.lead
# #         requester_user = getattr(req, "requested_by_user", None)

# #         # Store the lead ID as text before deletion
# #         req.db_set("lead", lead_id, update_modified=False)

# #         # Delete the Lead safely
# #         try:
# #             frappe.delete_doc("Lead", lead_id, ignore_permissions=True, force=True)
# #         except Exception as delete_error:
# #             frappe.log_error(f"Failed to delete lead {lead_id}: {delete_error}")
# #             return {"ok": False, "message": f"Could not delete Lead {lead_id}. Check dependencies."}

# #         # Update request details (keep lead field as text)
# #         frappe.db.set_value("Lead Hide Request", req.name, {
# #             "status": "Approved",
# #             "approval_date": now(),
# #             "approved_by": approver_full_name,
# #             "approved_by_user": current_user
# #         })

# #         # Enqueue approval email
# #         if requester_user:
# #             requester_email = frappe.db.get_value("User", requester_user, "email")
# #             if requester_email:
# #                 subject = f"Lead Hide Request Approved — Lead {lead_id}"
# #                 message = f"""
# #                     <p>Dear {req.requested_by},</p>
# #                     <p>Your request to hide the lead <b>{lead_id}</b> has been <b>approved</b> by <b>{approver_full_name}</b>.</p>
# #                     <p>The lead has been permanently deleted and recorded in Deleted Documents.</p>
# #                     <br>
# #                     <p>Regards,<br><b>{approver_full_name}</b><br>Administrator</p>
# #                 """
# #                 frappe.enqueue(
# #                     send_email_safe,
# #                     queue="long",
# #                     timeout=600,
# #                     user_email=requester_email,
# #                     subject=subject,
# #                     message=message,
# #                     ref_doctype="Lead Hide Request",
# #                     ref_name=req.name
# #                 )

# #         frappe.msgprint("Lead hide request approved successfully.")
# #         return {"ok": True, "message": "Lead hide request approved successfully."}

# #     except Exception as e:
# #         frappe.log_error(f"Approve hide failed for {docname}: {frappe.get_traceback()}")
# #         return {"ok": False, "message": f"Failed to approve hide request: {str(e)}"}
# # =========================================================
# # ADMIN ACTION — APPROVE HIDE (No Delete)
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



# @frappe.whitelist()
# def restore_leads(leads):
#     """
#     Restores one or more leads from 'Trashed' or 'Hidden' to 'No Request' status.
#     """
#     import json
#     if isinstance(leads, str):
#         leads = json.loads(leads)

#     if not leads:
#         return {"ok": False, "message": "No leads provided."}

#     for lead_name in leads:
#         lead = frappe.get_doc("Lead", lead_name)
#         lead.db_set("custom_hide_status", "No Request")
#         lead.db_set("custom_is_hidden", 0)

#     return {"ok": True, "message": f"{len(leads)} Lead(s) restored successfully."}


# def get_admin_users():
#     """Return list of Admin and Administrator users"""
   
#     admins = []
#     admins.append("Administrator")

#     role_holders = frappe.get_all(
#         "Has Role",
#         filters={"role": "Admin"},
#         fields=["parent"]
#     )

#     for r in role_holders:
#         if r.parent not in admins:
#             admins.append(r.parent)

#     return admins

# import frappe
# from datetime import datetime, timedelta
# import pytz
# from frappe.sessions import clear_sessions

# def auto_logout_inactive_users():
#     """
#     Auto logout conditions:
#     1️⃣ User inactive for more than 2 HOURS → logout
#     2️⃣ Midnight (00:00) → force logout all users
#     Uses Activity Log timestamps (Asia/Dubai timezone).
#     """

#     try:
#         dubai_tz = pytz.timezone("Asia/Dubai")
#         current_time = datetime.now(dubai_tz)
#         logout_after = timedelta(hours=2)

#         # print(f"[Auto Logout] Running at {current_time} (Asia/Dubai)")

#         # =====================================================
#         # (1) Midnight full logout
#         # =====================================================
#         if current_time.hour == 0:
#             try:
#                 frappe.db.sql("""
#                     DELETE FROM `tabSessions`
#                     WHERE user NOT IN ('Administrator', 'Guest')
#                 """)
#                 frappe.db.commit()
#                 frappe.logger().info("[Auto Logout] Midnight detected — All users (except Admin & Guest) logged out.")
#                 # print("Midnight detected — All users (except Admin & Guest) logged out.\n")
#             except Exception as e:
#                 frappe.log_error(f"Midnight logout failed: {str(e)}", "auto_logout_inactive_users")
#                 frappe.logger().error(f"[Auto Logout] Midnight logout failed: {str(e)}")
#                 # print(f"Midnight logout failed: {e}")

#         # =====================================================
#         # (2) Inactivity > 2 HOURS logout
#         # =====================================================
#         try:
#             login_activities = frappe.db.sql("""
#                 SELECT 
#                     owner AS user,
#                     MAX(creation) AS last_login_time
#                 FROM `tabActivity Log`
#                 WHERE subject LIKE '%logged in%'
#                 GROUP BY owner
#             """, as_dict=True)

#             # print(f"Found {len(login_activities)} users with login records.")

#             for entry in login_activities:
#                 user = entry.user
#                 last_login_time = entry.last_login_time

#                 if user in ("Administrator", "Guest"):
#                     continue

#                 # Convert timestamp to Dubai timezone
#                 if last_login_time.tzinfo is None:
#                     last_login_time = dubai_tz.localize(last_login_time)
#                 else:
#                     last_login_time = last_login_time.astimezone(dubai_tz)

#                 time_diff = current_time - last_login_time
#                 # print(f"{user} logged in at {last_login_time}, active for {time_diff.total_seconds() / 3600:.2f} hours")

#                 if time_diff >= logout_after:
#                     try:
#                         clear_sessions(user=user)
#                         frappe.db.commit()
#                         frappe.logger().info(f"[Auto Logout] Logged out {user} (inactive for {time_diff.total_seconds() / 3600:.2f} hours)")
#                         # print(f"Logged out {user} (inactive for {time_diff.total_seconds() / 3600:.2f} hours)")
#                     except Exception as e:
#                         frappe.log_error(f"Failed to logout {user}: {str(e)}", "auto_logout_inactive_users")
#                         frappe.logger().error(f"[Auto Logout] Failed to logout {user}: {str(e)}")
#                         # print(f"Failed to logout {user}: {e}")

#         except Exception as e:
#             frappe.log_error(f"Inactivity check failed: {str(e)}", "auto_logout_inactive_users")
#             frappe.logger().error(f"[Auto Logout] Inactivity check failed: {str(e)}")
#             # print(f"Inactivity check failed: {e}")

#         # print("Auto logout (midnight + inactivity) check completed successfully.\n")

#     except Exception as e:
#         frappe.log_error(f"Auto logout failed: {str(e)}", "auto_logout_inactive_users")
#         frappe.logger().error(f"[Auto Logout] Fatal error: {str(e)}")
#         # print(f"Auto logout failed: {e}")



# # import frappe
# # from twilio.rest import Client
# # from frappe.utils import now_datetime
# # from hashlib import sha256
# # import hmac
# # import json

# # # =========================================================
# # #  CHECK CALL LIMIT (same as before)
# # # =========================================================
# # def check_call_limit(agent):
# #     user_doc = frappe.get_doc("User", agent)
# #     limit_count = user_doc.get("daily_call_limit_count") or 0
# #     limit_duration = user_doc.get("daily_call_limit_duration") or 0

# #     today = frappe.utils.nowdate()
# #     filters = {"agent": agent, "creation": (">=", f"{today} 00:00:00")}
# #     total_calls = frappe.db.count("Agent Call Log", filters)
# #     total_duration = frappe.db.sum("Agent Call Log", filters, "duration") or 0

# #     if limit_count and total_calls >= limit_count:
# #         frappe.throw("📞 Daily call limit (by number of calls) reached.")
# #     if limit_duration and total_duration >= limit_duration:
# #         frappe.throw("📞 Daily call limit (by total duration) reached.")


# # # =========================================================
# # #  MAKE CALL THROUGH TWILIO
# # # =========================================================
# # @frappe.whitelist()
# # def make_call(lead_id, agent_id, phone_number):
# #     """Initiate a Twilio voice call."""
# #     check_call_limit(agent_id)

# #     # Load settings
# #     settings = frappe.get_single("Admin Settings")
# #     client = Client(settings.account_sid, settings.auth_token)

# #     try:
# #         call = client.calls.create(
# #             to=phone_number,
# #             from_=settings.from_number,
# #             url=f"{frappe.utils.get_url()}/api/method/joel_living.custom_lead_changes.call_flow"
# #         )

# #         # Temporary log
# #         frappe.logger("dialer").info(f"Initiated call SID {call.sid}")

# #         return {"message": "Twilio call started", "sid": call.sid}
# #     except Exception as e:
# #         frappe.log_error(f"Twilio Error: {e}", "Twilio Call")
# #         frappe.throw("Unable to initiate call via Twilio.")


# # # =========================================================
# # #  TWIML CALLBACK — RETURN INSTRUCTIONS TO TWILIO
# # # =========================================================
# # @frappe.whitelist(allow_guest=True)
# # def call_flow():
# #     """
# #     Twilio fetches this URL to know what to do when call connects.
# #     """
# #     frappe.response['type'] = 'text/xml'
# #     frappe.response['message'] = """<?xml version="1.0" encoding="UTF-8"?>
# # <Response>
# #     <Say voice="alice">Connecting your call. Please wait.</Say>
# # </Response>"""


# # # =========================================================
# # #  TWILIO STATUS WEBHOOK (CALL LOG)
# # # =========================================================
# # @frappe.whitelist(allow_guest=True)
# # def call_log(**kwargs):
# #     """
# #     Twilio sends call status updates to this endpoint.
# #     Example POST form fields:
# #       CallSid, CallStatus, From, To, CallDuration
# #     """
# #     # Verify webhook (optional, if you set a secret)
# #     settings = frappe.get_single("Admin Settings")
# #     secret = settings.webhook_secret or ""
# #     body = frappe.request.get_data(as_text=True)
# #     signature = frappe.request.headers.get("X-Twilio-Signature", "")
# #     expected_sig = hmac.new(secret.encode(), body.encode(), sha256).hexdigest()
# #     if secret and signature != expected_sig:
# #         frappe.throw("Invalid webhook signature")

# #     data = frappe._dict(kwargs)

# #     try:
# #         call_doc = frappe.get_doc({
# #             "doctype": "Agent Call Log",
# #             "lead": data.get("lead_id"),
# #             "agent": data.get("agent"),
# #             "call_time": now_datetime(),
# #             "duration": int(data.get("CallDuration") or 0),
# #             "call_status": data.get("CallStatus", "completed").title(),
# #             "direction": "Outbound"
# #         }).insert(ignore_permissions=True)

# #         # Optional note on the lead
# #         if data.get("lead_id"):
# #             frappe.get_doc({
# #                 "doctype": "Communication",
# #                 "communication_type": "Comment",
# #                 "comment_type": "Info",
# #                 "reference_doctype": "Lead",
# #                 "reference_name": data.get("lead_id"),
# #                 "content": f"📞 Twilio Call — Status: {data.get('CallStatus')}, Duration: {data.get('CallDuration',0)}s"
# #             }).insert(ignore_permissions=True)

# #         frappe.db.commit()
# #         return "OK"
# #     except Exception as e:
# #         frappe.log_error(f"Twilio Webhook Error: {e}", "Twilio Webhook")
# #         frappe.throw("Error recording Twilio call.")



# # import frappe
# # from twilio.rest import Client
# # from frappe.utils import now_datetime
# # from hashlib import sha256
# # import hmac, json, twilio

# # # =========================================================
# # #  CHECK CALL LIMIT
# # # =========================================================
# # def check_call_limit(agent):
# #     try:
# #         user_doc = frappe.get_doc("User", agent)
# #         limit_count = user_doc.get("daily_call_limit_count") or 0
# #         limit_duration = user_doc.get("daily_call_limit_duration") or 0

# #         today = frappe.utils.nowdate()
# #         filters = {
# #             "agent": agent,
# #             "creation": (">=", f"{today} 00:00:00")
# #         }

# #         # --- Count total calls ---
# #         total_calls = frappe.db.count("Agent Call Log", filters)

# #         # --- Sum duration manually ---
# #         total_duration = 0  # Skip until you add the duration field


# #         frappe.logger("dialer").info(
# #             f"[CHECK LIMIT] Agent: {agent}, Calls: {total_calls}, Duration: {total_duration}"
# #         )

# #         if limit_count and total_calls >= limit_count:
# #             frappe.throw("📞 Daily call limit (by number of calls) reached.")
# #         if limit_duration and total_duration >= limit_duration:
# #             frappe.throw("📞 Daily call limit (by total duration) reached.")
# #     except Exception:
# #         frappe.log_error(frappe.get_traceback(), "Twilio Call Debug")
# #         raise



# # # =========================================================
# # #  MAKE CALL THROUGH TWILIO
# # # =========================================================
# # @frappe.whitelist()
# # def make_call(lead_id, agent_id, phone_number):
# #     try:
# #         frappe.logger("dialer").info(f"[MAKE CALL] Lead={lead_id}, Agent={agent_id}, Phone={phone_number}")
# #         check_call_limit(agent_id)

# #         settings = frappe.get_single("Admin Settings")
# #         print(settings,"-----------settings--------------")
# #         client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
# #         print(client,"------------client-----------")
# #         call = client.calls.create(
# #             to=phone_number,
# #             from_=settings.twilio_from_number,
# #             url=f"{frappe.utils.get_url()}/api/method/joel_living.custom_lead_changes.call_flow"
# #         )
# #         print(call.url,"---------url-----------------")
# #         print(call,"---------------call-----------------")
# #         frappe.logger("dialer").info(f"[MAKE CALL] Twilio Call SID={call.sid}")
# #         return {"message": "Twilio call started", "sid": call.sid}

# #     except Exception as e:
# #         frappe.log_error(
# #             message=f"Twilio Error: {str(e)}\n\nTraceback:\n{frappe.get_traceback()}",
# #             title="Twilio Call Debug - make_call()"
# #         )
# #         frappe.throw("Unable to initiate call via Twilio. Please check Admin Settings credentials.")

# #     except Exception:
# #         frappe.log_error(frappe.get_traceback(), "Twilio Error: make_call()")
# #         frappe.throw("Unable to initiate call via Twilio.")


# # # =========================================================
# # #  TWIML CALLBACK
# # # =========================================================
# # @frappe.whitelist(allow_guest=True)
# # def call_flow():
# #     try:
# #         frappe.response['type'] = 'text/xml'
# #         frappe.response['message'] = """<?xml version="1.0" encoding="UTF-8"?>
# # <Response>
# #     <Say voice="alice">Connecting your call. Please wait.</Say>
# # </Response>"""
# #     except Exception:
# #         frappe.log_error(frappe.get_traceback(), "Twilio Error: call_flow()")
# #         raise


# # # =========================================================
# # #  TWILIO WEBHOOK (CALL LOG)
# # # =========================================================
# # @frappe.whitelist(allow_guest=True)
# # def call_log(**kwargs):
# #     try:
# #         frappe.logger("dialer").info(f"[CALL LOG] Webhook: {json.dumps(kwargs)}")
# #         settings = frappe.get_single("Admin Settings")

# #         secret = settings.webhook_secret or ""
# #         body = frappe.request.get_data(as_text=True)
# #         signature = frappe.request.headers.get("X-Twilio-Signature", "")
# #         expected_sig = hmac.new(secret.encode(), body.encode(), sha256).hexdigest()

# #         if secret and signature != expected_sig:
# #             frappe.log_error("Invalid webhook signature", "Twilio Webhook Signature Mismatch")
# #             frappe.throw("Invalid webhook signature")

# #         data = frappe._dict(kwargs)

# #         call_doc = frappe.get_doc({
# #             "doctype": "Agent Call Log",
# #             "lead": data.get("lead_id"),
# #             "agent": data.get("agent"),
# #             "call_time": now_datetime(),
# #             "duration": int(data.get("CallDuration") or 0),
# #             "call_status": data.get("CallStatus", "completed").title(),
# #             "direction": "Outbound"
# #         }).insert(ignore_permissions=True)

# #         # Add comment on Lead
# #         if data.get("lead_id"):
# #             frappe.get_doc({
# #                 "doctype": "Communication",
# #                 "communication_type": "Comment",
# #                 "comment_type": "Info",
# #                 "reference_doctype": "Lead",
# #                 "reference_name": data.get("lead_id"),
# #                 "content": f"📞 Twilio Call — {data.get('CallStatus')} ({data.get('CallDuration', 0)}s)"
# #             }).insert(ignore_permissions=True)

# #         frappe.db.commit()
# #         return "OK"

# #     except Exception:
# #         frappe.log_error(frappe.get_traceback(), "Twilio Error: call_log()")
# #         frappe.throw("Error recording Twilio call.")


# import requests
# import frappe
# from frappe.utils import now_datetime

# # @frappe.whitelist()
# # def make_call(lead_id, from_number, to_number):
# #     """Initiate Exotel call and log details in Exotel Call Log"""
# #     try:
# #         sid = frappe.db.get_single_value("Admin Settings", "twilio_account_sid")
# #         token = frappe.db.get_single_value("Admin Settings", "twilio_auth_token")
# #         virtual_number = frappe.db.get_single_value("Admin Settings", "twilio_auth_token")

# #         url = f"https://{sid}:{token}@api.exotel.com/v1/Accounts/{sid}/Calls/connect"

# #         payload = {
# #             "From": from_number,
# #             "To": to_number,
# #             "CallerId": virtual_number,
# #             "CallType": "trans"
# #         }

# #         response = requests.post(url, data=payload)
# #         result = response.json()

# #         # Extract Exotel call details
# #         call_sid = result.get("Call", {}).get("Twilio Account SID")
# #         call_status = result.get("Call", {}).get("Status", "Initiated")

# #         # Create Call Log entry
# #         call_log = frappe.get_doc({
# #             "doctype": "Exotel Call Log",
# #             "lead": lead_id,
# #             "agent": frappe.session.user,
# #             "call_time": now_datetime(),
# #             "call_status": call_status,
# #             "direction": "Outbound"
# #         })
# #         call_log.insert(ignore_permissions=True)
# #         frappe.db.commit()

# #         return {"success": True, "message": "Call initiated successfully", "call_sid": call_sid}

# #     except Exception as e:
# #         frappe.log_error(f"Exotel Call Error: {e}", "Exotel Integration")
# #         return {"success": False, "message": str(e)}

# import requests
# import frappe
# from frappe.utils import now_datetime

# @frappe.whitelist()
# def make_call(lead_id, from_number, to_number):
#     """Initiate Exotel call and log details in Exotel Call Log"""
#     try:
#         # ✅ Fetch Exotel credentials
#         account_sid = frappe.db.get_single_value("Admin Settings", "exotel_sid")
#         api_key = frappe.db.get_single_value("Admin Settings", "exotel_api_key")
#         api_token = frappe.db.get_single_value("Admin Settings", "exotel_token")
#         virtual_number = frappe.db.get_single_value("Admin Settings", "exotel_virtual_number")

#         if not all([account_sid, api_key, api_token, virtual_number]):
#             frappe.throw("Exotel settings are incomplete. Please check Admin Settings.")

#         # ✅ Correct API endpoint
#         url = f"https://{api_key}:{api_token}@api.exotel.com/v1/Accounts/{account_sid}/Calls/connect"

#         payload = {
#             "From": from_number,        # Agent's number
#             "To": to_number,            # Customer's number
#             "CallerId": virtual_number, # Exotel virtual number
#             "CallType": "trans"         # Transactional call
#         }

#         # Make the API call
#         response = requests.post(url, data=payload)

#         # Debug Log
#         frappe.log_error(f"Exotel Raw Response ({response.status_code}): {response.text}", "Exotel Debug")

#         # ✅ Handle success
#         if response.status_code == 200:
#             call_log = frappe.get_doc({
#                 "doctype": "Agent Call Log",
#                 "lead": lead_id,
#                 "agent": frappe.session.user,
#                 "call_time": now_datetime(),
#                 "call_status": "Completed",
#                 "direction": "Outbound"
#             })
#             call_log.insert(ignore_permissions=True)
#             frappe.db.commit()

#             return {"success": True, "message": "Call initiated successfully"}

#         else:
#             return {"success": False, "message": f"Exotel Error: {response.text}"}

#     except Exception as e:
#         frappe.log_error(f"Exotel Call Error: {e}", "Exotel Integration")
#         return {"success": False, "message": str(e)}


# # import frappe
# # from frappe.utils import now_datetime

# # @frappe.whitelist(allow_guest=True)
# # def call_status_update(**kwargs):
# #     """
# #     Webhook endpoint for Exotel call status updates
# #     """
# #     try:
# #         call_sid = kwargs.get("CallSid")
# #         status = kwargs.get("Status")
# #         duration = kwargs.get("DialCallDuration")

# #         # Determine readable status
# #         status_map = {
# #             "completed": "Completed",
# #             "busy": "Rejected",
# #             "failed": "Missed",
# #             "no-answer": "Missed"
# #         }
# #         call_status = status_map.get(status.lower(), "Completed") if status else "Completed"

# #         # Find latest outbound call log (no unique sid field in your doctype)
# #         call_log = frappe.db.get_all(
# #             "Agent Call Log",
# #             filters={"direction": "Outbound"},
# #             fields=["name"],
# #             order_by="creation desc",
# #             limit=1
# #         )

# #         if call_log:
# #             name = call_log[0].name
# #             frappe.db.set_value("Agent Call Log", name, {
# #                 "call_status": call_status,
# #                 "duration": duration or 0
# #             })
# #             frappe.db.commit()

# #         return "OK"

# #     except Exception as e:
# #         frappe.log_error(f"Exotel Webhook Error: {e}", "Exotel Webhook")
# #         return "Error"



# # import frappe
# # from frappe.utils import now_datetime

# # @frappe.whitelist()
# # def create_call_log(lead, phone):
# #     """Create a new Call Log when agent clicks 'Call'"""
# #     doc = frappe.get_doc({
# #         "doctype": "Agent Call Log",
# #         "lead": lead,
# #         "phone_number": phone,
# #         "call_status": "Dialing",
# #         "call_start_time": now_datetime(),
# #         "agent": frappe.session.user
# #     })
# #     doc.insert(ignore_permissions=True)
# #     frappe.db.commit()
# #     return {"call_id": doc.name, "phone": phone}


# # @frappe.whitelist()
# # def update_call_log_status(call_id, status):
# #     """Update status when agent returns"""
# #     doc = frappe.get_doc("Agent Call Log", call_id)
# #     doc.call_status = status
# #     doc.call_end_time = now_datetime()
# #     doc.save(ignore_permissions=True)
# #     frappe.db.commit()
# #     return "ok"


# # @frappe.whitelist()
# # def increment_lead_call_count(lead):
# #     """Increase call count in Lead when call completes"""
# #     lead_doc = frappe.get_doc("Lead", lead)
# #     current = lead_doc.get("call_count") or 0
# #     lead_doc.call_count = current + 1
# #     lead_doc.save(ignore_permissions=True)
# #     frappe.db.commit()
# #     return lead_doc.call_count

# # import frappe
# # from frappe.utils import now_datetime

# # @frappe.whitelist()
# # def create_call_log(lead, phone):
# #     doc = frappe.get_doc({
# #         "doctype": "Agent Call Log",
# #         "lead": lead,
# #         "phone_number": phone,
# #         "call_status": "Initiated",
# #         "call_start_time": now_datetime(),
# #         "agent": frappe.session.user
# #     })
# #     doc.insert(ignore_permissions=True)
# #     frappe.db.commit()
# #     return {"call_id": doc.name, "phone": phone}


# # @frappe.whitelist()
# # def update_call_log_status(call_id, status, duration=None):
# #     doc = frappe.get_doc("Agent Call Log", call_id)
    
# #     # ✅ Use correct field name 'call_status'
# #     doc.call_status = status
# #     doc.call_end_time = now_datetime()

# #     # ✅ Save call duration if available
# #     if duration is not None:
# #         doc.duration_sec = duration

# #     doc.save(ignore_permissions=True)
# #     frappe.db.commit()
# #     return "ok"


# # @frappe.whitelist()
# # def increment_lead_call_count(lead):
# #     lead_doc = frappe.get_doc("Lead", lead)
# #     current = lead_doc.get("call_count") or 0
# #     lead_doc.call_count = current + 1
# #     lead_doc.save(ignore_permissions=True)
# #     frappe.db.commit()
# #     return lead_doc.call_count

# import frappe
# from frappe.utils import now_datetime

# @frappe.whitelist()
# def create_call_log(lead, phone):
#     """Create a call log entry and store lead and agent names."""
#     try:
#         lead_doc = frappe.get_doc("Lead", lead)
#         lead_name = lead_doc.lead_name or lead_doc.name

#         # ✅ Get agent (user) details
#         agent_email = frappe.session.user
#         agent_full_name = frappe.db.get_value("User", agent_email, "full_name")

#         doc = frappe.get_doc({
#             "doctype": "Agent Call Log",
#             "lead": lead,
#             "lead_name": lead_name,  # human-readable lead name
#             "phone_number": phone,
#             "call_status": "Initiated",
#             "call_start_time": now_datetime(),
#             "agent": agent_email,          # still store email for reference
#             "called_by": agent_full_name  # ✅ store full name for display
#         })
#         doc.insert(ignore_permissions=True)
#         frappe.db.commit()

#         return {
#             "call_id": doc.name,
#             "phone": phone,
#             "lead_name": lead_name,
#             "called_by": agent_full_name
#         }

#     except Exception as e:
#         frappe.log_error(f"Error in create_call_log: {e}", "Call Log Creation Error")
#         return {"error": str(e)}


# @frappe.whitelist()
# def update_call_log_status(call_id, status, duration=None):
#     """Update call log with status and duration."""
#     try:
#         doc = frappe.get_doc("Agent Call Log", call_id)
#         doc.call_status = status
#         doc.call_end_time = now_datetime()

#         if duration is not None:
#             try:
#                 doc.duration_sec = int(duration)
#             except Exception:
#                 frappe.log_error(f"Invalid duration value: {duration}", "Duration Conversion Error")

#         doc.save(ignore_permissions=True)
#         frappe.db.commit()
#         return {"message": f"Call updated with status {status}"}

#     except Exception as e:
#         frappe.log_error(f"Error in update_call_log_status: {e}", "Call Log Update Error")
#         return {"error": str(e)}


# @frappe.whitelist()
# def increment_lead_call_count(lead):
#     """Increment lead's call count when call is completed."""
#     try:
#         lead_doc = frappe.get_doc("Lead", lead)
#         lead_doc.custom_call_count = (lead_doc.custom_call_count or 0) + 1
#         lead_doc.save(ignore_permissions=True)
#         frappe.db.commit()
#         return {"message": f"Lead {lead_doc.lead_name} call count updated"}

#     except Exception as e:
#         frappe.log_error(f"Error in increment_lead_call_count: {e}", "Lead Call Count Error")
#         return {"error": str(e)}



# @frappe.whitelist()
# def get_lead_call_logs(lead):
#     """Return call logs for a specific lead."""
#     try:
#         logs = frappe.db.get_all(
#             "Agent Call Log",
#             filters={"lead": lead},
#             fields=["name", "phone_number", "call_status", "duration_sec", "called_by", "call_start_time"],
#             order_by="creation desc"
#         )
#         return logs
#     except Exception as e:
#         frappe.log_error(f"Error fetching call logs for lead {lead}: {e}", "Call Log Fetch Error")
#         return []










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

#             # 🚫 Backend restriction: Prevent hiding Completed / Closed leads
#             status = frappe.db.get_value("Lead", lead, "custom_lead_status")
#             if status in ["Sales Completed", "Closed"]:
#                 return {
#                     "ok": False,
#                     "message": f"Cannot hide Lead {lead}. Status is {status}, hide not allowed."
#                 }

#             req_doc = frappe.get_doc({
#                 "doctype": "Lead Hide Request",
#                 "lead": lead,
#                 "requested_by": full_name,
#                 "requested_by_user": current_user,
#                 "requested_date": frappe.utils.now_datetime(),
#                 "status": "Pending"
#             })
#             req_doc.insert(ignore_permissions=True)

#             frappe.db.set_value("Lead", lead, {
#                 "lead_owner": None,
#                 "custom_hide_status": "Pending",
#                 "custom_is_hidden": 1
#             })

#             processed_leads.append(lead)

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

#         lead_list_str = ", ".join(processed_leads)
#         frappe.msgprint(f"Hide request submitted successfully for: {lead_list_str}")

#         return {"ok": True, "message": f"Hide request submitted successfully for: {lead_list_str}"}

#     except Exception as e:
#         frappe.log_error(f"Hide request failed for {leads}: {str(e)}")
#         return {"ok": False, "message": "Failed to submit hide request. Try again later."}
@frappe.whitelist()
def request_hide(leads):
    """
    Sales Agent requests to hide one or more Leads.
    Sends ONLY system (in-app) notifications to all Admins.
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
        failed_leads = []
        
        # Get all Admin users
        admins = {"Administrator"}
        role_holders = frappe.get_all("Has Role", filters={"role": "Admin"}, fields=["parent"])
        admins.update({r.parent for r in role_holders})

        # Process each lead individually
        for lead in leads:
            try:
                # 🚫 Backend restriction: Prevent hiding Completed / Closed leads
                status = frappe.db.get_value("Lead", lead, "custom_lead_status")
                if status in ["Sales Completed", "Closed"]:
                    failed_leads.append(f"{lead} (Status: {status})")
                    continue

                req_doc = frappe.get_doc({
                    "doctype": "Lead Hide Request",
                    "lead": lead,
                    "requested_by": full_name,
                    "requested_by_user": current_user,
                    "requested_date": frappe.utils.now_datetime(),
                    "status": "Pending"
                })
                req_doc.insert(ignore_permissions=True)

                frappe.db.set_value("Lead", lead, {
                    "lead_owner": None,
                    "custom_hide_status": "Pending",
                    "custom_is_hidden": 1
                })

                processed_leads.append(lead)

                # Send notifications to admins
                for admin_user in admins:
                    frappe.enqueue(
                        create_notification,
                        queue="long",
                        timeout=600,
                        user=admin_user,
                        subject=f"Lead Hide Request from {full_name}",
                        message=f"{full_name} has requested to hide the Lead <b>{lead}</b>.<br><br>"
                                f"The request is awaiting your review and approval.",
                        ref_doctype="Lead Hide Request",
                        ref_name=req_doc.name,
                        send_email=False
                    )

            except Exception as e:
                failed_leads.append(f"{lead} (Error: {str(e)})")
                continue

        frappe.db.commit()

       # Prepare count-only response
        processed_count = len(processed_leads)
        failed_count = len(failed_leads)

        if processed_count and failed_count:
            return {
                "ok": True,
                "message": f"Hide request submitted for {processed_count} lead(s). {failed_count} could not be processed.",
                "processed_count": processed_count,
                "failed_count": failed_count
            }

        elif processed_count:
            return {
                "ok": True,
                "message": f"Hide request submitted successfully for {processed_count} lead(s).",
                "processed_count": processed_count,
                "failed_count": 0
            }

        else:
            return {
                "ok": False,
                "message": f"All selected leads failed validation ({failed_count} lead(s) blocked).",
                "processed_count": 0,
                "failed_count": failed_count
            }


    except Exception as e:
        frappe.log_error(f"Hide request failed for {leads}: {str(e)}")
        return {"ok": False, "message": "Failed to submit hide request. Try again later."}
# # =========================================================
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
#             # 🚫 Backend protection: Block hide for Completed or Closed leads
#             status = frappe.db.get_value("Lead", lead, "custom_lead_status")
#             if status in ["Sales Completed", "Closed"]:
#                 return {
#                     "ok": False,
#                     "message": f"Cannot hide Lead {lead}. Status is {status}, hide not allowed."
#                 }
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


# =========================================================
# ADMIN ACTION — APPROVE HIDE
# =========================================================

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

#         # Store the lead ID as text before deletion
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

#         # Enqueue approval email
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
#         return {"ok": True, "message": "Lead hide request approved successfully."}

#     except Exception as e:
#         frappe.log_error(f"Approve hide failed for {docname}: {frappe.get_traceback()}")
#         return {"ok": False, "message": f"Failed to approve hide request: {str(e)}"}
# =========================================================
# ADMIN ACTION — APPROVE HIDE (No Delete)
# =========================================================
@frappe.whitelist()
def approve_hide_request(docname):
    """Approve a hide request (Admin or Administrator only, without deleting the Lead)."""
    try:
        req = frappe.get_doc("Lead Hide Request", docname)
        current_user = frappe.session.user
        approver_full_name = frappe.utils.get_fullname(current_user)

        if req.status != "Pending":
            return {"ok": False, "message": "Only Pending requests can be approved."}

        lead_id = req.lead
        requester_user = getattr(req, "requested_by_user", None)

        # ✅ Instead of deleting, mark the lead as hidden and clear ownership
        frappe.db.set_value("Lead", lead_id, {
            "lead_owner": None,
            "custom_hide_status": "Trashed",
            "custom_is_hidden": 0  # Hide lead from all views
        })
        frappe.db.commit()

        # ✅ Update request details
        frappe.db.set_value("Lead Hide Request", req.name, {
            "status": "Approved",
            "approval_date": now(),
            "approved_by": approver_full_name,
            "approved_by_user": current_user
        })

        # ✅ Send email to requester
        if requester_user:
            requester_email = frappe.db.get_value("User", requester_user, "email")
            if requester_email:
                subject = f"Lead Hide Request Approved — Lead {lead_id}"
                message = f"""
                    <p>Dear {req.requested_by},</p>
                    <p>Your request to hide the lead <b>{lead_id}</b> has been <b>approved</b> by <b>{approver_full_name}</b>.</p>
                    <p>The lead has been successfully hidden and removed from the active list.</p>
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

        frappe.msgprint("Lead hide request approved successfully (lead hidden).")
        return {"ok": True, "message": "Lead hide request approved successfully."}

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

        # ✅ Update Lead — make visible again & mark as reshuffled
        frappe.db.set_value("Lead", lead, {
            "lead_owner": None,
            "custom_lead_category": "Reshuffled Lead",
            "custom_hide_status": "No Request",
            "custom_is_hidden": 0  # Show again in unassigned leads
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
        return {"ok": True, "message": "Lead hide request rejected successfully."}

    except Exception as e:
        frappe.log_error(f"Reject hide failed for {docname}: {str(e)}")
        return {"ok": False, "message": "Failed to reject hide request."}



@frappe.whitelist()
def restore_leads(leads):
    """
    Restores one or more leads from 'Trashed' or 'Hidden' to 'No Request' status.
    """
    import json
    if isinstance(leads, str):
        leads = json.loads(leads)

    if not leads:
        return {"ok": False, "message": "No leads provided."}

    for lead_name in leads:
        lead = frappe.get_doc("Lead", lead_name)
        lead.db_set("custom_hide_status", "No Request")
        lead.db_set("custom_is_hidden", 0)

    return {"ok": True, "message": f"{len(leads)} Lead(s) restored successfully."}


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

import frappe
from datetime import datetime, timedelta
import pytz
from frappe.sessions import clear_sessions

def auto_logout_inactive_users():
    """
    Auto logout conditions:
    1️⃣ User inactive for more than 2 HOURS → logout
    2️⃣ Midnight (00:00) → force logout all users
    Uses Activity Log timestamps (Asia/Dubai timezone).
    """

    try:
        dubai_tz = pytz.timezone("Asia/Dubai")
        current_time = datetime.now(dubai_tz)
        logout_after = timedelta(hours=2)

        print(f"[Auto Logout] Running at {current_time} (Asia/Dubai)")

        # =====================================================
        # (1) Midnight full logout
        # =====================================================
        if current_time.hour == 0:
            try:
                frappe.db.sql("""
                    DELETE FROM `tabSessions`
                    WHERE user NOT IN ('Administrator', 'Guest')
                """)
                frappe.db.commit()
                frappe.logger().info("[Auto Logout] Midnight detected — All users (except Admin & Guest) logged out.")
                print("Midnight detected — All users (except Admin & Guest) logged out.\n")
            except Exception as e:
                frappe.log_error(f"Midnight logout failed: {str(e)}", "auto_logout_inactive_users")
                frappe.logger().error(f"[Auto Logout] Midnight logout failed: {str(e)}")
                print(f"Midnight logout failed: {e}")

        # =====================================================
        # (2) Inactivity > 2 HOURS logout
        # =====================================================
        try:
            login_activities = frappe.db.sql("""
                SELECT 
                    owner AS user,
                    MAX(creation) AS last_login_time
                FROM `tabActivity Log`
                WHERE subject LIKE '%logged in%'
                GROUP BY owner
            """, as_dict=True)

            print(f"Found {len(login_activities)} users with login records.")

            for entry in login_activities:
                user = entry.user
                last_login_time = entry.last_login_time

                if user in ("Administrator", "Guest"):
                    continue

                # Convert timestamp to Dubai timezone
                if last_login_time.tzinfo is None:
                    last_login_time = dubai_tz.localize(last_login_time)
                else:
                    last_login_time = last_login_time.astimezone(dubai_tz)

                time_diff = current_time - last_login_time
                print(f"{user} logged in at {last_login_time}, active for {time_diff.total_seconds() / 3600:.2f} hours")

                if time_diff >= logout_after:
                    try:
                        clear_sessions(user=user)
                        frappe.db.commit()
                        frappe.logger().info(f"[Auto Logout] Logged out {user} (inactive for {time_diff.total_seconds() / 3600:.2f} hours)")
                        print(f"Logged out {user} (inactive for {time_diff.total_seconds() / 3600:.2f} hours)")
                    except Exception as e:
                        frappe.log_error(f"Failed to logout {user}: {str(e)}", "auto_logout_inactive_users")
                        frappe.logger().error(f"[Auto Logout] Failed to logout {user}: {str(e)}")
                        print(f"Failed to logout {user}: {e}")

        except Exception as e:
            frappe.log_error(f"Inactivity check failed: {str(e)}", "auto_logout_inactive_users")
            frappe.logger().error(f"[Auto Logout] Inactivity check failed: {str(e)}")
            print(f"Inactivity check failed: {e}")

        print("Auto logout (midnight + inactivity) check completed successfully.\n")

    except Exception as e:
        frappe.log_error(f"Auto logout failed: {str(e)}", "auto_logout_inactive_users")
        frappe.logger().error(f"[Auto Logout] Fatal error: {str(e)}")
        print(f"Auto logout failed: {e}")



# import frappe
# from twilio.rest import Client
# from frappe.utils import now_datetime
# from hashlib import sha256
# import hmac
# import json

# # =========================================================
# #  CHECK CALL LIMIT (same as before)
# # =========================================================
# def check_call_limit(agent):
#     user_doc = frappe.get_doc("User", agent)
#     limit_count = user_doc.get("daily_call_limit_count") or 0
#     limit_duration = user_doc.get("daily_call_limit_duration") or 0

#     today = frappe.utils.nowdate()
#     filters = {"agent": agent, "creation": (">=", f"{today} 00:00:00")}
#     total_calls = frappe.db.count("Agent Call Log", filters)
#     total_duration = frappe.db.sum("Agent Call Log", filters, "duration") or 0

#     if limit_count and total_calls >= limit_count:
#         frappe.throw("📞 Daily call limit (by number of calls) reached.")
#     if limit_duration and total_duration >= limit_duration:
#         frappe.throw("📞 Daily call limit (by total duration) reached.")


# # =========================================================
# #  MAKE CALL THROUGH TWILIO
# # =========================================================
# @frappe.whitelist()
# def make_call(lead_id, agent_id, phone_number):
#     """Initiate a Twilio voice call."""
#     check_call_limit(agent_id)

#     # Load settings
#     settings = frappe.get_single("Admin Settings")
#     client = Client(settings.account_sid, settings.auth_token)

#     try:
#         call = client.calls.create(
#             to=phone_number,
#             from_=settings.from_number,
#             url=f"{frappe.utils.get_url()}/api/method/joel_living.custom_lead_changes.call_flow"
#         )

#         # Temporary log
#         frappe.logger("dialer").info(f"Initiated call SID {call.sid}")

#         return {"message": "Twilio call started", "sid": call.sid}
#     except Exception as e:
#         frappe.log_error(f"Twilio Error: {e}", "Twilio Call")
#         frappe.throw("Unable to initiate call via Twilio.")


# # =========================================================
# #  TWIML CALLBACK — RETURN INSTRUCTIONS TO TWILIO
# # =========================================================
# @frappe.whitelist(allow_guest=True)
# def call_flow():
#     """
#     Twilio fetches this URL to know what to do when call connects.
#     """
#     frappe.response['type'] = 'text/xml'
#     frappe.response['message'] = """<?xml version="1.0" encoding="UTF-8"?>
# <Response>
#     <Say voice="alice">Connecting your call. Please wait.</Say>
# </Response>"""


# # =========================================================
# #  TWILIO STATUS WEBHOOK (CALL LOG)
# # =========================================================
# @frappe.whitelist(allow_guest=True)
# def call_log(**kwargs):
#     """
#     Twilio sends call status updates to this endpoint.
#     Example POST form fields:
#       CallSid, CallStatus, From, To, CallDuration
#     """
#     # Verify webhook (optional, if you set a secret)
#     settings = frappe.get_single("Admin Settings")
#     secret = settings.webhook_secret or ""
#     body = frappe.request.get_data(as_text=True)
#     signature = frappe.request.headers.get("X-Twilio-Signature", "")
#     expected_sig = hmac.new(secret.encode(), body.encode(), sha256).hexdigest()
#     if secret and signature != expected_sig:
#         frappe.throw("Invalid webhook signature")

#     data = frappe._dict(kwargs)

#     try:
#         call_doc = frappe.get_doc({
#             "doctype": "Agent Call Log",
#             "lead": data.get("lead_id"),
#             "agent": data.get("agent"),
#             "call_time": now_datetime(),
#             "duration": int(data.get("CallDuration") or 0),
#             "call_status": data.get("CallStatus", "completed").title(),
#             "direction": "Outbound"
#         }).insert(ignore_permissions=True)

#         # Optional note on the lead
#         if data.get("lead_id"):
#             frappe.get_doc({
#                 "doctype": "Communication",
#                 "communication_type": "Comment",
#                 "comment_type": "Info",
#                 "reference_doctype": "Lead",
#                 "reference_name": data.get("lead_id"),
#                 "content": f"📞 Twilio Call — Status: {data.get('CallStatus')}, Duration: {data.get('CallDuration',0)}s"
#             }).insert(ignore_permissions=True)

#         frappe.db.commit()
#         return "OK"
#     except Exception as e:
#         frappe.log_error(f"Twilio Webhook Error: {e}", "Twilio Webhook")
#         frappe.throw("Error recording Twilio call.")



# import frappe
# from twilio.rest import Client
# from frappe.utils import now_datetime
# from hashlib import sha256
# import hmac, json, twilio

# # =========================================================
# #  CHECK CALL LIMIT
# # =========================================================
# def check_call_limit(agent):
#     try:
#         user_doc = frappe.get_doc("User", agent)
#         limit_count = user_doc.get("daily_call_limit_count") or 0
#         limit_duration = user_doc.get("daily_call_limit_duration") or 0

#         today = frappe.utils.nowdate()
#         filters = {
#             "agent": agent,
#             "creation": (">=", f"{today} 00:00:00")
#         }

#         # --- Count total calls ---
#         total_calls = frappe.db.count("Agent Call Log", filters)

#         # --- Sum duration manually ---
#         total_duration = 0  # Skip until you add the duration field


#         frappe.logger("dialer").info(
#             f"[CHECK LIMIT] Agent: {agent}, Calls: {total_calls}, Duration: {total_duration}"
#         )

#         if limit_count and total_calls >= limit_count:
#             frappe.throw("📞 Daily call limit (by number of calls) reached.")
#         if limit_duration and total_duration >= limit_duration:
#             frappe.throw("📞 Daily call limit (by total duration) reached.")
#     except Exception:
#         frappe.log_error(frappe.get_traceback(), "Twilio Call Debug")
#         raise



# # =========================================================
# #  MAKE CALL THROUGH TWILIO
# # =========================================================
# @frappe.whitelist()
# def make_call(lead_id, agent_id, phone_number):
#     try:
#         frappe.logger("dialer").info(f"[MAKE CALL] Lead={lead_id}, Agent={agent_id}, Phone={phone_number}")
#         check_call_limit(agent_id)

#         settings = frappe.get_single("Admin Settings")
#         print(settings,"-----------settings--------------")
#         client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
#         print(client,"------------client-----------")
#         call = client.calls.create(
#             to=phone_number,
#             from_=settings.twilio_from_number,
#             url=f"{frappe.utils.get_url()}/api/method/joel_living.custom_lead_changes.call_flow"
#         )
#         print(call.url,"---------url-----------------")
#         print(call,"---------------call-----------------")
#         frappe.logger("dialer").info(f"[MAKE CALL] Twilio Call SID={call.sid}")
#         return {"message": "Twilio call started", "sid": call.sid}

#     except Exception as e:
#         frappe.log_error(
#             message=f"Twilio Error: {str(e)}\n\nTraceback:\n{frappe.get_traceback()}",
#             title="Twilio Call Debug - make_call()"
#         )
#         frappe.throw("Unable to initiate call via Twilio. Please check Admin Settings credentials.")

#     except Exception:
#         frappe.log_error(frappe.get_traceback(), "Twilio Error: make_call()")
#         frappe.throw("Unable to initiate call via Twilio.")


# # =========================================================
# #  TWIML CALLBACK
# # =========================================================
# @frappe.whitelist(allow_guest=True)
# def call_flow():
#     try:
#         frappe.response['type'] = 'text/xml'
#         frappe.response['message'] = """<?xml version="1.0" encoding="UTF-8"?>
# <Response>
#     <Say voice="alice">Connecting your call. Please wait.</Say>
# </Response>"""
#     except Exception:
#         frappe.log_error(frappe.get_traceback(), "Twilio Error: call_flow()")
#         raise


# # =========================================================
# #  TWILIO WEBHOOK (CALL LOG)
# # =========================================================
# @frappe.whitelist(allow_guest=True)
# def call_log(**kwargs):
#     try:
#         frappe.logger("dialer").info(f"[CALL LOG] Webhook: {json.dumps(kwargs)}")
#         settings = frappe.get_single("Admin Settings")

#         secret = settings.webhook_secret or ""
#         body = frappe.request.get_data(as_text=True)
#         signature = frappe.request.headers.get("X-Twilio-Signature", "")
#         expected_sig = hmac.new(secret.encode(), body.encode(), sha256).hexdigest()

#         if secret and signature != expected_sig:
#             frappe.log_error("Invalid webhook signature", "Twilio Webhook Signature Mismatch")
#             frappe.throw("Invalid webhook signature")

#         data = frappe._dict(kwargs)

#         call_doc = frappe.get_doc({
#             "doctype": "Agent Call Log",
#             "lead": data.get("lead_id"),
#             "agent": data.get("agent"),
#             "call_time": now_datetime(),
#             "duration": int(data.get("CallDuration") or 0),
#             "call_status": data.get("CallStatus", "completed").title(),
#             "direction": "Outbound"
#         }).insert(ignore_permissions=True)

#         # Add comment on Lead
#         if data.get("lead_id"):
#             frappe.get_doc({
#                 "doctype": "Communication",
#                 "communication_type": "Comment",
#                 "comment_type": "Info",
#                 "reference_doctype": "Lead",
#                 "reference_name": data.get("lead_id"),
#                 "content": f"📞 Twilio Call — {data.get('CallStatus')} ({data.get('CallDuration', 0)}s)"
#             }).insert(ignore_permissions=True)

#         frappe.db.commit()
#         return "OK"

#     except Exception:
#         frappe.log_error(frappe.get_traceback(), "Twilio Error: call_log()")
#         frappe.throw("Error recording Twilio call.")


import requests
import frappe
from frappe.utils import now_datetime

# @frappe.whitelist()
# def make_call(lead_id, from_number, to_number):
#     """Initiate Exotel call and log details in Exotel Call Log"""
#     try:
#         sid = frappe.db.get_single_value("Admin Settings", "twilio_account_sid")
#         token = frappe.db.get_single_value("Admin Settings", "twilio_auth_token")
#         virtual_number = frappe.db.get_single_value("Admin Settings", "twilio_auth_token")

#         url = f"https://{sid}:{token}@api.exotel.com/v1/Accounts/{sid}/Calls/connect"

#         payload = {
#             "From": from_number,
#             "To": to_number,
#             "CallerId": virtual_number,
#             "CallType": "trans"
#         }

#         response = requests.post(url, data=payload)
#         result = response.json()

#         # Extract Exotel call details
#         call_sid = result.get("Call", {}).get("Twilio Account SID")
#         call_status = result.get("Call", {}).get("Status", "Initiated")

#         # Create Call Log entry
#         call_log = frappe.get_doc({
#             "doctype": "Exotel Call Log",
#             "lead": lead_id,
#             "agent": frappe.session.user,
#             "call_time": now_datetime(),
#             "call_status": call_status,
#             "direction": "Outbound"
#         })
#         call_log.insert(ignore_permissions=True)
#         frappe.db.commit()

#         return {"success": True, "message": "Call initiated successfully", "call_sid": call_sid}

#     except Exception as e:
#         frappe.log_error(f"Exotel Call Error: {e}", "Exotel Integration")
#         return {"success": False, "message": str(e)}

import requests
import frappe
from frappe.utils import now_datetime

@frappe.whitelist()
def make_call(lead_id, from_number, to_number):
    """Initiate Exotel call and log details in Exotel Call Log"""
    try:
        # ✅ Fetch Exotel credentials
        account_sid = frappe.db.get_single_value("Admin Settings", "exotel_sid")
        api_key = frappe.db.get_single_value("Admin Settings", "exotel_api_key")
        api_token = frappe.db.get_single_value("Admin Settings", "exotel_token")
        virtual_number = frappe.db.get_single_value("Admin Settings", "exotel_virtual_number")

        if not all([account_sid, api_key, api_token, virtual_number]):
            frappe.throw("Exotel settings are incomplete. Please check Admin Settings.")

        # ✅ Correct API endpoint
        url = f"https://{api_key}:{api_token}@api.exotel.com/v1/Accounts/{account_sid}/Calls/connect"

        payload = {
            "From": from_number,        # Agent's number
            "To": to_number,            # Customer's number
            "CallerId": virtual_number, # Exotel virtual number
            "CallType": "trans"         # Transactional call
        }

        # Make the API call
        response = requests.post(url, data=payload)

        # Debug Log
        frappe.log_error(f"Exotel Raw Response ({response.status_code}): {response.text}", "Exotel Debug")

        # ✅ Handle success
        if response.status_code == 200:
            call_log = frappe.get_doc({
                "doctype": "Agent Call Log",
                "lead": lead_id,
                "agent": frappe.session.user,
                "call_time": now_datetime(),
                "call_status": "Completed",
                "direction": "Outbound"
            })
            call_log.insert(ignore_permissions=True)
            frappe.db.commit()

            return {"success": True, "message": "Call initiated successfully"}

        else:
            return {"success": False, "message": f"Exotel Error: {response.text}"}

    except Exception as e:
        frappe.log_error(f"Exotel Call Error: {e}", "Exotel Integration")
        return {"success": False, "message": str(e)}


# import frappe
# from frappe.utils import now_datetime

# @frappe.whitelist(allow_guest=True)
# def call_status_update(**kwargs):
#     """
#     Webhook endpoint for Exotel call status updates
#     """
#     try:
#         call_sid = kwargs.get("CallSid")
#         status = kwargs.get("Status")
#         duration = kwargs.get("DialCallDuration")

#         # Determine readable status
#         status_map = {
#             "completed": "Completed",
#             "busy": "Rejected",
#             "failed": "Missed",
#             "no-answer": "Missed"
#         }
#         call_status = status_map.get(status.lower(), "Completed") if status else "Completed"

#         # Find latest outbound call log (no unique sid field in your doctype)
#         call_log = frappe.db.get_all(
#             "Agent Call Log",
#             filters={"direction": "Outbound"},
#             fields=["name"],
#             order_by="creation desc",
#             limit=1
#         )

#         if call_log:
#             name = call_log[0].name
#             frappe.db.set_value("Agent Call Log", name, {
#                 "call_status": call_status,
#                 "duration": duration or 0
#             })
#             frappe.db.commit()

#         return "OK"

#     except Exception as e:
#         frappe.log_error(f"Exotel Webhook Error: {e}", "Exotel Webhook")
#         return "Error"



# import frappe
# from frappe.utils import now_datetime

# @frappe.whitelist()
# def create_call_log(lead, phone):
#     """Create a new Call Log when agent clicks 'Call'"""
#     doc = frappe.get_doc({
#         "doctype": "Agent Call Log",
#         "lead": lead,
#         "phone_number": phone,
#         "call_status": "Dialing",
#         "call_start_time": now_datetime(),
#         "agent": frappe.session.user
#     })
#     doc.insert(ignore_permissions=True)
#     frappe.db.commit()
#     return {"call_id": doc.name, "phone": phone}


# @frappe.whitelist()
# def update_call_log_status(call_id, status):
#     """Update status when agent returns"""
#     doc = frappe.get_doc("Agent Call Log", call_id)
#     doc.call_status = status
#     doc.call_end_time = now_datetime()
#     doc.save(ignore_permissions=True)
#     frappe.db.commit()
#     return "ok"


# @frappe.whitelist()
# def increment_lead_call_count(lead):
#     """Increase call count in Lead when call completes"""
#     lead_doc = frappe.get_doc("Lead", lead)
#     current = lead_doc.get("call_count") or 0
#     lead_doc.call_count = current + 1
#     lead_doc.save(ignore_permissions=True)
#     frappe.db.commit()
#     return lead_doc.call_count

# import frappe
# from frappe.utils import now_datetime

# @frappe.whitelist()
# def create_call_log(lead, phone):
#     doc = frappe.get_doc({
#         "doctype": "Agent Call Log",
#         "lead": lead,
#         "phone_number": phone,
#         "call_status": "Initiated",
#         "call_start_time": now_datetime(),
#         "agent": frappe.session.user
#     })
#     doc.insert(ignore_permissions=True)
#     frappe.db.commit()
#     return {"call_id": doc.name, "phone": phone}


# @frappe.whitelist()
# def update_call_log_status(call_id, status, duration=None):
#     doc = frappe.get_doc("Agent Call Log", call_id)
    
#     # ✅ Use correct field name 'call_status'
#     doc.call_status = status
#     doc.call_end_time = now_datetime()

#     # ✅ Save call duration if available
#     if duration is not None:
#         doc.duration_sec = duration

#     doc.save(ignore_permissions=True)
#     frappe.db.commit()
#     return "ok"


# @frappe.whitelist()
# def increment_lead_call_count(lead):
#     lead_doc = frappe.get_doc("Lead", lead)
#     current = lead_doc.get("call_count") or 0
#     lead_doc.call_count = current + 1
#     lead_doc.save(ignore_permissions=True)
#     frappe.db.commit()
#     return lead_doc.call_count

import frappe
from frappe.utils import now_datetime

@frappe.whitelist()
def create_call_log(lead, phone):
    """Create a call log entry and store lead and agent names."""
    try:
        lead_doc = frappe.get_doc("Lead", lead)
        lead_name = lead_doc.lead_name or lead_doc.name

        # ✅ Get agent (user) details
        agent_email = frappe.session.user
        agent_full_name = frappe.db.get_value("User", agent_email, "full_name")

        doc = frappe.get_doc({
            "doctype": "Agent Call Log",
            "lead": lead,
            "lead_name": lead_name,  # human-readable lead name
            "phone_number": phone,
            "call_status": "Initiated",
            "call_start_time": now_datetime(),
            "agent": agent_email,          # still store email for reference
            "called_by": agent_full_name  # ✅ store full name for display
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()

        return {
            "call_id": doc.name,
            "phone": phone,
            "lead_name": lead_name,
            "called_by": agent_full_name
        }

    except Exception as e:
        frappe.log_error(f"Error in create_call_log: {e}", "Call Log Creation Error")
        return {"error": str(e)}


@frappe.whitelist()
def update_call_log_status(call_id, status, duration=None):
    """Update call log with status and duration."""
    try:
        doc = frappe.get_doc("Agent Call Log", call_id)
        doc.call_status = status
        doc.call_end_time = now_datetime()

        if duration is not None:
            try:
                doc.duration_sec = int(duration)
            except Exception:
                frappe.log_error(f"Invalid duration value: {duration}", "Duration Conversion Error")

        doc.save(ignore_permissions=True)
        frappe.db.commit()
        return {"message": f"Call updated with status {status}"}

    except Exception as e:
        frappe.log_error(f"Error in update_call_log_status: {e}", "Call Log Update Error")
        return {"error": str(e)}


@frappe.whitelist()
def increment_lead_call_count(lead):
    """Increment lead's call count when call is completed."""
    try:
        lead_doc = frappe.get_doc("Lead", lead)
        lead_doc.custom_call_count = (lead_doc.custom_call_count or 0) + 1
        lead_doc.save(ignore_permissions=True)
        frappe.db.commit()
        return {"message": f"Lead {lead_doc.lead_name} call count updated"}

    except Exception as e:
        frappe.log_error(f"Error in increment_lead_call_count: {e}", "Lead Call Count Error")
        return {"error": str(e)}



@frappe.whitelist()
def get_lead_call_logs(lead):
    """Return call logs for a specific lead."""
    try:
        logs = frappe.db.get_all(
            "Agent Call Log",
            filters={"lead": lead},
            fields=["name", "phone_number", "call_status", "duration_sec", "called_by", "call_start_time"],
            order_by="creation desc"
        )
        return logs
    except Exception as e:
        frappe.log_error(f"Error fetching call logs for lead {lead}: {e}", "Call Log Fetch Error")
        return []

# lead_validation.py
import re
import frappe

def validate_names(doc, method):
    fields = ['first_name', 'middle_name', 'last_name']
    pattern = re.compile(r"^[A-Za-z'-]+$")

    for field in fields:
        value = getattr(doc, field, None)
        if not value:
            continue

        value = value.strip()

        if not pattern.match(value):
            frappe.throw(f"{field.replace('_', ' ').title()} contains invalid characters")

        if len(value) > 50:
            frappe.throw(f"{field.replace('_', ' ').title()} cannot exceed 50 characters")

        value = value.capitalize()
        setattr(doc, field, value)
