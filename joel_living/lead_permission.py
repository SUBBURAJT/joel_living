import frappe
from frappe.utils import now_datetime
from frappe.utils.background_jobs import enqueue
from frappe import _
from frappe.utils import now_datetime, add_to_date, format_datetime
# --------------------------- #
# List View / Query Conditions
# --------------------------- #
def get_sales_agent_lead_conditions(user):
    """Generates SQL conditions for the Lead list view based on user role."""
    roles = frappe.get_roles(user)

    if any(r in roles for r in ["Admin", "Super Admin"]):
        return ""

    if "Sales Agent" not in roles:
        return ""

    conditions = [f"tabLead.lead_owner = {frappe.db.escape(user)}"]

    try:
        admin_settings = frappe.get_doc("Admin Settings")
    except frappe.DoesNotExistError:
        return "(" + " OR ".join(conditions) + ")"

    restrictions = getattr(admin_settings, "user_lead_restrictions", []) or []
    user_rows = [r for r in restrictions if r.user == user]

    if not user_rows:
        conditions.append("tabLead.lead_owner IS NULL OR tabLead.lead_owner = ''")
    else:
        for r in user_rows:
            try:
                cats = frappe.parse_json(r.lead_category or "[]")
                sources = frappe.parse_json(r.main_lead_source or "[]")
            except Exception:
                continue

            sub_conditions = []
            cats.append("Meta Leads")
            if cats:
                cats_sql = ",".join([frappe.db.escape(c) for c in cats])
                sub_conditions.append(f"tabLead.custom_lead_category IN ({cats_sql})")

            if sources:
                sources_sql = ",".join([frappe.db.escape(s) for s in sources])
                sub_conditions.append(f"tabLead.custom_main_lead_source IN ({sources_sql})")
            
            sub_conditions.append("(tabLead.lead_owner IS NULL OR tabLead.lead_owner = '')")
            
            if sub_conditions:
                conditions.append("(" + " AND ".join(sub_conditions) + ")")

    final_condition = "(" + " OR ".join(conditions) + ")"
    return final_condition

# --------------------------- #
# Document Access Permissions
# --------------------------- #
@frappe.whitelist()
def has_sales_agent_lead_permission(doc, user):
    """Determine if a user has write access to a Lead document."""
    roles = frappe.get_roles(user)
    
    if any(r in roles for r in ["Admin", "Super Admin"]):
        return True

    if "Sales Agent" not in roles:
        return True

    if getattr(doc, "lead_owner", None) == user:
        return True

    if not getattr(doc, "lead_owner", None):
        try:
            admin_settings = frappe.get_doc("Admin Settings")
        except frappe.DoesNotExistError:
            return False
        
        restrictions = getattr(admin_settings, "user_lead_restrictions", []) or []
        user_rows = [r for r in restrictions if r.user == user]
        
        if not user_rows:
            return True

        for r in user_rows:
            try:
                cats = frappe.parse_json(r.lead_category or "[]")
                cats.append("Meta Leads")
                sources = frappe.parse_json(r.main_lead_source or "[]")
            except Exception:
                continue
            
            if (not cats or getattr(doc, "custom_lead_category", None) in cats) and \
               (not sources or getattr(doc, "custom_main_lead_source", None) in sources):
                return True

    return False



def allow_write_for_lead_owner(doc, method):
    """Restrict editing only to lead owner or unassigned leads."""
    user = frappe.session.user
    roles = frappe.get_roles(user)

    if any(r in roles for r in ["Administrator", "Sales Manager"]):
        return

    if "Sales Agent" in roles:
        if not doc.lead_owner or doc.lead_owner == user:
            return
        frappe.throw("You are not allowed to edit this Lead.")


# --------------------------- #
# Assignment & Logging Logic
# --------------------------- #
def _create_assignment_history(lead, action, new_owner=None, action_by=None):
    """
    This is the ONLY function that creates history logs.
    It is the single source of truth for auditing.
    """
    if not action_by:
        action_by = frappe.session.user

    frappe.get_doc({
        "doctype": "Lead Assignment History", 
        "lead": lead,
        "action": action,
        "assigned_to": new_owner,
        "action_by": action_by,
        "timestamp": now_datetime()
    }).insert(ignore_permissions=True, ignore_mandatory=True)


@frappe.whitelist()
def assign_lead_to_me(lead_name):
    """
    Allows a Sales Agent to assign a FRESH, UNASSIGNED lead to themselves.
    A "fresh" lead is one that has NEVER been assigned to anyone before.
    """
    user = frappe.session.user
    roles = frappe.get_roles(user)

    # --- UPDATED VALIDATION BLOCK ---
    # This entire block only runs for users who are NOT Admins.
    if "Admin" not in roles and "Super Admin" not in roles:
        
        # --- NEW MASTER CHECK ---
        # Check if this lead has ANY assignment history at all.
        # If a record exists, it means the lead was previously owned and is not "fresh".
        # Therefore, it cannot be self-claimed and must be assigned by a manager.
        if frappe.db.exists("Lead Assignment History", {"lead": lead_name}):
            frappe.throw(_("This lead has been previously worked on and cannot be self-claimed. Please ask a manager to assign it to you."))

      
    # If the checks pass, it's a truly fresh lead. Proceed with assignment.
    doc = frappe.get_doc("Lead", lead_name)
    if doc.lead_owner:
        # This is a final safety check in case of a race condition.
        frappe.throw(_("This lead is already assigned to another user."))
    
    doc.lead_owner = user
    doc.custom_lead_status = "Open"
    # The 'on_lead_assignment_change' hook will correctly set the timestamp and create the history.
    doc.save(ignore_permissions=True)
    
    # --- Calculate and Format Expiry Time for the Message ---
    try:
        timeout_minutes = frappe.db.get_single_value("Admin Settings", "assignment_timeout_minutes") or 60
        expiry_time = add_to_date(now_datetime(), minutes=int(timeout_minutes))
        # This formatting requires from frappe.utils import format_datetime, add_to_date, now_datetime
        formatted_expiry_time = format_datetime(expiry_time, "short") 
        success_message = _("Lead {0} has been assigned to you. You must action it before {1}.").format(
            frappe.bold(lead_name), frappe.bold(formatted_expiry_time)
        )
    except Exception:
        success_message = _(f"Lead {lead_name} has been assigned to you.")

    frappe.db.commit()
    return {"status": "success", "message": success_message}
def on_lead_assignment_change(doc, method):
    """
    Runs before every Lead save — handles assignment changes.
    """
    if doc.flags.get("ignore_assignment_hook"):
        return

    try:
        # Skip for new docs; handled in after_insert
        if doc.is_new():
            return

        doc_before_save = doc.get_doc_before_save()
        if not doc_before_save or doc_before_save.lead_owner == doc.lead_owner:
            return  # No change

        old_owner = doc_before_save.lead_owner
        new_owner = doc.lead_owner
        action_by = frappe.session.user
        action = ""

        if new_owner and not old_owner:  # Assigned
            doc.custom_assigned_at = now_datetime()
            action = "Self-assigned" if new_owner == action_by else "Assigned"
        elif new_owner and old_owner:  # Reassigned
            doc.custom_assigned_at = now_datetime()
            action = "Reassigned"
        elif not new_owner and old_owner:  # Unassigned
            doc.custom_assigned_at = None
            action = "Unassigned"

        if action:
            _create_assignment_history(doc.name, action, new_owner, action_by)

    except Exception:
        frappe.log_error(title=f"Lead Assignment Hook Failed for: {doc.name}", message=frappe.get_traceback())


def after_insert_lead_assignment(doc, method):
    """Handle initial assignment tracking for new leads."""
    try:
        if doc.lead_owner:
            doc.custom_assigned_at = now_datetime()
            _create_assignment_history(doc.name, "Assigned", doc.lead_owner)
    except Exception:
        frappe.log_error(title=f"Lead After Insert Hook Failed for: {doc.name}", message=frappe.get_traceback())


# -------------------------------------------------------- #
# --- WORKER & DISPATCHER JOBS ---
# -------------------------------------------------------- #

# In process_lead_timeout_unassignment
def process_lead_timeout_unassignment(lead_name, owner):
    """WORKER JOB: Unassigns a single timed-out SELF-ASSIGNED lead."""
    try:
        doc = frappe.get_doc("Lead", lead_name)
        # Final check to ensure the state hasn't changed since dispatch
        if doc.lead_owner == owner and doc.custom_lead_status == "Open":
            doc.lead_owner = None
            doc.custom_assigned_at = None
            
            # Set a flag to prevent the 'on_lead_assignment_change' hook from running
            doc.flags.ignore_assignment_hook = True
            
            doc.save(ignore_permissions=True)
            # Create the specific history record
            _create_assignment_history(lead_name, "Unassigned (Timeout)", None, "Administrator")
            frappe.db.commit()
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(title=f"Failed to process timeout for lead: {lead_name}", message=str(e))



def process_overdue_unassignment(lead_name, owner, status):
    """
    WORKER JOB: Unassigns an overdue lead.
    If the lead was in a critical status, it flags it for a potential re-assignment.
    """
    try:
        doc = frappe.get_doc("Lead", lead_name)
        if doc.lead_owner != owner: return # Stop if the owner has already changed

        is_critical = status in ['Meeting Scheduled', 'Sales Completed']

        # === THIS IS THE SPECIAL LOGIC FOR CRITICAL LEADS ===
        if is_critical:
            doc.custom_requires_reapproval = 1
            doc.custom_last_owner = owner
            doc.add_comment("Comment", f"Lead unassigned from {owner} (Status: '{status}'). Re-assignment request created for admin review.")
        
        # === THIS PART RUNS FOR ALL OVERDUE LEADS ===
        # The lead is now unassigned, making it available for admin action.
        doc.lead_owner = None
        doc.custom_assigned_at = None
        doc.custom_lead_category = "Reshuffled Lead"
        doc.flags.ignore_assignment_hook = True
        doc.save(ignore_permissions=True)
        
        _create_assignment_history(lead_name, "Unassigned (Overdue)", None, "Administrator")

        # After saving, if it was critical, enqueue the job to notify the admins.
        if is_critical:
            enqueue("joel_living.lead_permission.create_extension_request_for_lead", lead_name=lead_name, owner=owner)

        frappe.db.commit()
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(title=f"Failed to process overdue unassignment for lead: {lead_name}", message=str(e))


@frappe.whitelist()
def approve_lead_reassignment(request_name):
    """
    Allows a System Manager, Admin, or Super Admin to approve a re-assignment request.

    This function finds a lead that was previously unassigned, re-assigns it to its
    last owner, and starts a new deadline based on the value in Admin Settings.
    """
    # Ensure the user performing this action has the required role.
    user = frappe.session.user
    user_roles = frappe.get_roles(user)
    if not any(role in user_roles for role in ["System Manager", "Admin", "Super Admin"]):
        frappe.throw(_("You do not have the required permissions to approve lead re-assignments."))

    try:
        req_doc = frappe.get_doc("Lead Extension Request", request_name)
        if req_doc.status != "Open":
            frappe.throw(_("This request has already been actioned and cannot be changed."))

        lead_doc = frappe.get_doc("Lead", req_doc.lead)
        if not lead_doc.custom_requires_reapproval or not lead_doc.custom_last_owner:
            frappe.throw(_("This lead is not eligible for re-assignment. The state may have changed."))

        last_owner = lead_doc.custom_last_owner

        # Re-assign the lead
        lead_doc.lead_owner = last_owner
        lead_doc.custom_assigned_at = now_datetime()
        lead_doc.custom_requires_reapproval = 0
        lead_doc.custom_last_owner = ""
        lead_doc.save(ignore_permissions=True)

        # Update the request document
        req_doc.status = "Approved"
        req_doc.approved_by = user
        req_doc.approved_on = now_datetime()
        req_doc.save(ignore_permissions=True)

        _create_assignment_history(lead_doc.name, "Re-approved Assignment", last_owner, user)
        
        frappe.db.commit()

        # Fetch the deadline from Admin Settings, with a default fallback of 3.
        deadline_days = frappe.db.get_single_value("Admin Settings", "re_approval_deadline_days") or 3
        deadline_days = int(deadline_days)
        # --- END OF CHANGE ---

        # Show a success message to the admin with the correct number of days.
        frappe.msgprint(
            _("Lead {0} has been re-assigned to {1} for a final {2}-day period.").format(
                frappe.bold(lead_doc.name),
                frappe.bold(last_owner),
                frappe.bold(deadline_days)
            )
        )

    except Exception as e:
        frappe.db.rollback()
        frappe.throw(f"An error occurred during re-assignment: {str(e)}")


@frappe.whitelist()
def unassign_overdue_leads():
    """DISPATCHER JOB (Daily): Finds ALL overdue leads and enqueues them for processing."""
    try:
        days = frappe.db.get_single_value("Admin Settings", "number_of_days_lead_completed_in")
        if not days or int(days) <= 0: return

        overdue_date = add_to_date(now_datetime(), days=-int(days))
        
        # This query correctly finds ALL assigned leads past the overdue date.
        sql_query = """
            SELECT L.name, L.lead_owner, L.custom_lead_status 
            FROM `tabLead` AS L
            WHERE L.lead_owner IS NOT NULL
              AND L.custom_assigned_at <= %(overdue_date)s
        """
        overdue_leads = frappe.db.sql(sql_query, {"overdue_date": overdue_date}, as_dict=True)
        
        if overdue_leads:
            for lead in overdue_leads:
                enqueue(
                    # This worker function is the "brain" that decides what to do next.
                    "joel_living.lead_permission.process_overdue_unassignment",
                    lead_name=lead.name,
                    owner=lead.lead_owner,
                    status=lead.custom_lead_status
                )
            frappe.logger().info(f"[Lead Overdue Dispatcher] Enqueued {len(overdue_leads)} overdue leads for processing.")
    except Exception:
        frappe.log_error("Lead Overdue Dispatcher job failed", frappe.get_traceback())


def process_final_unassignment(lead_name, owner):
    """
    WORKER JOB: Unassigns a lead because its 3-day re-approval period expired
    without the lead being moved to 'Closed' status.
    """
    try:
        doc = frappe.get_doc("Lead", lead_name)
        
        # Final check to ensure the state hasn't changed since dispatch
        if doc.lead_owner == owner and doc.status != "Closed":
            # Unassign the lead permanently
            doc.lead_owner = None
            doc.custom_assigned_at = None
            
            # This flag prevents the generic 'on_lead_assignment_change' hook from running
            doc.flags.ignore_assignment_hook = True
            doc.save(ignore_permissions=True)

            # Create a very specific history log for a clear audit trail
            _create_assignment_history(lead_name, "Unassigned (Re-approval Expired)", None, "Administrator")
            
            # Add a comment to the lead for clarity
            doc.add_comment("Comment", f"Lead unassigned from {owner} because the 3-day re-approval period expired and the status was not 'Closed'.")
            
            frappe.db.commit()
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(title=f"Failed final unassignment for lead: {lead_name}", message=str(e))

          
@frappe.whitelist()
def dispatch_expired_reapproved_leads():
    """
    DISPATCHER JOB (Daily): Finds re-approved leads that have passed their deadline
    and have not been 'Closed', then enqueues them for final unassignment.
    """
    try:
        # --- CHANGE IS HERE ---
        # Fetch the deadline from Admin Settings, with a default fallback of 3.
        deadline_days = frappe.db.get_single_value("Admin Settings", "re_approval_deadline_days") or 3
        deadline_days = int(deadline_days) # Ensure it's an integer

        # As a safeguard, if the setting is invalid (e.g., 0 or negative), log it and use the default.
        if deadline_days <= 0:
            frappe.logger().warning("Re-approval Deadline in Admin Settings is invalid. Using default of 3 days.")
            deadline_days = 3
        # --- END OF CHANGE ---

        cutoff_date = add_to_date(now_datetime(), days=-deadline_days)

        sql_query = """
            SELECT
                L.name, L.lead_owner
            FROM `tabLead` AS L
            INNER JOIN (
                SELECT
                    lead,
                    action,
                    ROW_NUMBER() OVER(PARTITION BY lead ORDER BY timestamp DESC) as rn
                FROM `tabLead Assignment History`
            ) AS H ON L.name = H.lead
            WHERE
                L.lead_owner IS NOT NULL
                AND L.status != 'Closed'
                AND L.custom_assigned_at <= %(cutoff_date)s
                AND H.rn = 1
                AND H.action = 'Re-approved Assignment'
        """

        expired_leads = frappe.db.sql(sql_query, {"cutoff_date": cutoff_date}, as_dict=True)

        if expired_leads:
            for lead in expired_leads:
                enqueue(
                    "joel_living.lead_permission.process_final_unassignment",
                    queue="long",
                    lead_name=lead.name,
                    owner=lead.lead_owner
                )
            frappe.logger().info(f"[Lead Re-approval Dispatcher] Enqueued {len(expired_leads)} expired leads for final unassignment.")

    except Exception as e:
        frappe.log_error("Expired Re-approved Leads Dispatcher job failed", message=frappe.get_traceback())

def unassign_expired_open_leads():
    """
    DISPATCHER JOB (Cron): Finds expired 'Open' leads that were SELF-ASSIGNED 
    and enqueues a job for each.
    """
    try:
        timeout_minutes = frappe.db.get_single_value("Admin Settings", "assignment_timeout_minutes")
        if not timeout_minutes or int(timeout_minutes) <= 0:
            return
            
        cutoff_time = add_to_date(now_datetime(), minutes=-int(timeout_minutes))
        
      
        sql_query = """
            SELECT
                L.name, L.lead_owner
            FROM `tabLead` AS L
            INNER JOIN (
                SELECT lead, action, ROW_NUMBER() OVER(PARTITION BY lead ORDER BY timestamp DESC) as rn
                FROM `tabLead Assignment History`
                WHERE action IN ('Self-assigned', 'Assigned', 'Reassigned')
            ) AS H ON L.name = H.lead
            WHERE
                L.custom_lead_status = 'Open'
                AND L.lead_owner IS NOT NULL
                AND L.custom_assigned_at <= %(cutoff_time)s
                AND H.rn = 1
                AND H.action = 'Self-assigned'
        """
        
        expired_leads = frappe.db.sql(sql_query, {"cutoff_time": cutoff_time}, as_dict=True)

        if expired_leads:
            for lead in expired_leads:
                enqueue(
                    "joel_living.lead_permission.process_lead_timeout_unassignment",
                    queue="long",
                    lead_name=lead.name,
                    owner=lead.lead_owner
                )
            frappe.logger().info(f"[Lead Timeout Dispatcher] Enqueued {len(expired_leads)} self-assigned leads for timeout unassignment.")
    except Exception:
        frappe.log_error("Lead Timeout Dispatcher job failed", frappe.get_traceback())



from joel_living.email import send_custom_email

def create_extension_request_for_lead(lead_name, owner):
    """
    WORKER JOB: Creates a notification and a 'Lead Extension Request' doc
    for an overdue lead that is in a critical stage.
    """
    try:
        # Prevent creating duplicate requests if the job runs again before approval
        if frappe.db.exists("Lead Extension Request", {"lead": lead_name, "status": "Open"}):
            frappe.logger().info(f"Extension request for lead {lead_name} already exists. Skipping.")
            return

        request_doc = frappe.get_doc({
            "doctype": "Lead Extension Request",
            "lead": lead_name,
            "lead_owner": owner,
            "status": "Open",
            "requested_on": now_datetime()
        })
        request_doc.insert(ignore_permissions=True)

        manager_roles = ["Admin", "Super Admin"]
        recipients_list = frappe.db.sql("""
            SELECT DISTINCT hr.parent
            FROM `tabHas Role` AS hr
            INNER JOIN `tabUser` AS u ON hr.parent = u.name
            WHERE
                hr.role IN %(roles)s
                AND u.enabled = 1
        """, {"roles": manager_roles}, as_list=1)
        recipients = [row[0] for row in recipients_list]

        if not recipients:
            frappe.log_error(title="Lead Extension Failed", message=f"No enabled users with roles {manager_roles} found to notify for Lead {lead_name}.")
            frappe.db.rollback()
            return

        lead_doc = frappe.get_doc("Lead", lead_name)
        notification_subject = f"Action Required: Overdue Lead '{lead_doc.name}'"
        request_link = frappe.utils.get_url_to_form("Lead Extension Request", request_doc.name)

        email_message = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif; background-color: #f4f4f5; padding: 40px; text-align: center;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border: 1px solid #e4e4e7; border-radius: 8px; overflow: hidden;">
                
                <div style="background-color: #dc2626; color: #ffffff; padding: 24px;">
                    <h1 style="margin: 0; font-size: 24px; font-weight: 600;">Lead Extension Request</h1>
                </div>

                <div style="padding: 24px; text-align: left; color: #3f3f46;">
                    <p style="margin-bottom: 20px; font-size: 16px;">
                        A lead assigned to <b>{owner}</b> is overdue and requires your approval for extension.
                    </p>

                    <div style="border-top: 1px solid #e4e4e7; border-bottom: 1px solid #e4e4e7; padding: 16px 0;">
                        <table style="width: 100%; border-collapse: collapse;">
                            <tbody>
                                <tr>
                                    <td style="padding: 8px; font-weight: 600;">Lead Name:</td>
                                    <td style="padding: 8px;">{lead_doc.lead_name}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px; font-weight: 600;">Lead ID:</td>
                                    <td style="padding: 8px;">{lead_doc.name}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px; font-weight: 600;">Current Status:</td>
                                    <td style="padding: 8px;">
                                        <span style="background-color: #fef08a; color: #854d0e; padding: 4px 8px; border-radius: 4px; font-weight: 500;">
                                            {lead_doc.custom_lead_status}
                                        </span>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>

                    <p style="margin-top: 24px; font-size: 16px;">
                        Please review the lead's progress and approve the extension if appropriate.
                    </p>
                    
                    <a href="{request_link}" style="display: inline-block; background-color: #2563eb; color: #ffffff; text-decoration: none; padding: 14px 28px; border-radius: 6px; font-size: 16px; font-weight: 500; margin-top: 20px;">
                        Review and Approve Extension
                    </a>
                </div>

                <div style="background-color: #f4f4f5; color: #71717a; padding: 16px; font-size: 12px; text-align: center;">
                    <p style="margin: 0;">This is an automated notification from your CRM system.</p>
                </div>
            </div>
        </div>
        """


        for user in recipients:
            try:
                frappe.get_doc({
                    "doctype": "Notification Log",
                    "type": "Alert",
                    "document_type": "Lead Extension Request",
                    "document_name": request_doc.name,
                    "subject": f"Lead Extension Required: {lead_doc.name}",
                    "for_user": user,
                    # Optional: you can include the full html content in the system notification as well
                    # "email_content": email_message
                }).insert(ignore_permissions=True)
            except Exception as e:
                frappe.log_error(
                    title="Failed to create system notification",
                    message=f"Could not create notification for user {user} for Lead {lead_name}.\nError: {str(e)}"
                )

        # Assuming `send_custom_email` can handle a list of recipients in the 'to' field.
        should_send_email = frappe.db.get_single_value("Admin Settings", "send_email_on_extension_request")
        if should_send_email:
            try:
                send_custom_email(
                    to=recipients,
                    subject=notification_subject,
                    message=email_message,
                )
            except Exception as e:
                frappe.log_error(
                    title="Failed to send extension request email",
                    message=f"Could not send email for Lead {lead_name}.\nError: {str(e)}"
                )

        frappe.db.commit()

    except Exception:
        frappe.db.rollback()
        frappe.log_error(
            title=f"Failed to create extension request for lead: {lead_name}",
            message=frappe.get_traceback()
        )


# --- NEW DISPATCHER for EXTENSION REQUEST Leads ---
def dispatch_overdue_extension_requests():
    """
    DISPATCHER JOB (Daily): Finds overdue leads IN CRITICAL STAGES ('Meeting Scheduled', etc.) 
    and enqueues a job to create an extension request.
    """
    try:
        days = frappe.db.get_single_value("Admin Settings", "number_of_days_lead_completed_in")
        if not days or int(days) <= 0: return

        overdue_date = add_to_date(now_datetime(), days=-int(days))
        
        # It also joins to check that an open request doesn't already exist.
        sql_query = """
            SELECT L.name, L.lead_owner FROM `tabLead` AS L
            LEFT JOIN `tabLead Extension Request` AS R 
                ON L.name = R.lead AND R.status = 'Open'
            WHERE L.lead_owner IS NOT NULL
            AND L.custom_assigned_at <= %(overdue_date)s
            AND L.custom_lead_status IN ('Meeting Scheduled', 'Sales Completed')
            AND R.name IS NULL
        """
        leads_needing_review = frappe.db.sql(sql_query, {"overdue_date": overdue_date}, as_dict=True)

        if leads_needing_review:
            for lead in leads_needing_review:
                enqueue("joel_living.lead_permission.create_extension_request_for_lead", lead_name=lead.name, owner=lead.lead_owner)
            frappe.logger().info(f"[Lead Extension Dispatcher] Enqueued {len(leads_needing_review)} leads for extension review.")
    except Exception:
        frappe.log_error("Lead Extension Dispatcher job failed", frappe.get_traceback())




@frappe.whitelist()
def reject_lead_extension(request_name, reason=""):
    """
    Allows an Admin or Super Admin to formally reject a re-assignment request.

    This closes the request, clears the recovery flags on the lead, and sends
    a professionally formatted notification email to the original agent.
    """
    # Restrict this action to Admins and Super Admins.
    user = frappe.session.user
    user_roles = frappe.get_roles(user)
    if not any(role in user_roles for role in ["Admin", "Super Admin"]):
        frappe.throw(_("You do not have the required permissions (Admin or Super Admin) to reject lead requests."))

    try:
        req_doc = frappe.get_doc("Lead Extension Request", request_name)
        if req_doc.status != "Open":
            frappe.throw(_("This request has already been actioned."))

        lead_doc = frappe.get_doc("Lead", req_doc.lead)

        # Officially end the recovery process for this lead.
        lead_doc.custom_requires_reapproval = 0
        lead_doc.custom_last_owner = ""
        lead_doc.save(ignore_permissions=True)

        # Mark the request itself as 'Rejected' for the audit trail.
        req_doc.status = "Rejected"
        req_doc.approved_by = user  # 'actioned_by'
        req_doc.approved_on = now_datetime() # 'actioned_on'
        if reason and hasattr(req_doc, "rejected_reason"):
             req_doc.rejected_reason = reason
        req_doc.save(ignore_permissions=True)

        _create_assignment_history(lead_doc.name, "Extension Request Rejected", None, user)
        should_send_email = frappe.db.get_single_value("Admin Settings", "send_mail_on_rejection")
        
        # Only proceed with email creation and sending if the checkbox is checked.
        if should_send_email:
            original_owner = req_doc.lead_owner
            if original_owner:
                subject = _("Update on your request for Lead {0}").format(lead_doc.name)
                
                # This is the professional email template with inline CSS
                rejection_email_message = f"""
                <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif; background-color: #f4f4f5; padding: 40px; text-align: center;">
                    <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border: 1px solid #e4e4e7; border-radius: 8px; overflow: hidden;">
                        
                        <div style="background-color: #dc2626; color: #ffffff; padding: 24px;">
                            <h1 style="margin: 0; font-size: 24px; font-weight: 600;">Lead Request Rejected</h1>
                        </div>

                        <div style="padding: 24px; text-align: left; color: #3f3f46;">
                            <p style="margin-bottom: 20px; font-size: 16px;">
                                Hi {original_owner},
                                <br><br>
                                Your request for a re-assignment of the lead below has been reviewed and rejected by management.
                            </p>

                            <div style="border-top: 1px solid #e4e4e7; border-bottom: 1px solid #e4e4e7; padding: 16px 0;">
                                <table style="width: 100%; border-collapse: collapse;">
                                    <tbody>
                                        <tr>
                                            <td style="padding: 8px; font-weight: 600;">Lead Name:</td>
                                            <td style="padding: 8px;">{lead_doc.lead_name}</td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 8px; font-weight: 600;">Lead ID:</td>
                                            <td style="padding: 8px;">{lead_doc.name}</td>
                                        </tr>
                                        {'<tr><td style="padding: 8px; font-weight: 600; vertical-align: top;">Reason:</td><td style="padding: 8px;">{reason}</td></tr>' if reason else ''}
                                    </tbody>
                                </table>
                            </div>

                            <p style="margin-top: 24px; font-size: 16px;">
                                The lead has been returned to the unassigned pool and is no longer assigned to you.
                            </p>
                        </div>

                        <div style="background-color: #f4f4f5; color: #71717a; padding: 16px; font-size: 12px; text-align: center;">
                            <p style="margin: 0;">This is an automated notification from your CRM system.</p>
                        </div>
                    </div>
                </div>
                """
                
                try:
                    send_custom_email(
                        to=[original_owner],
                        subject=subject,
                        message=rejection_email_message
                    )
                except Exception as e:
                    frappe.log_error(
                        title="Failed to send rejection email",
                        message=f"Could not send rejection email for Lead {lead_doc.name} to {original_owner}.\nError: {str(e)}"
                    )

        frappe.db.commit()
        frappe.msgprint(_("Request for Lead {0} has been rejected.").format(frappe.bold(lead_doc.name)))

    except Exception as e:
        frappe.db.rollback()
        frappe.throw(f"An error occurred while rejecting the request: {str(e)}")




@frappe.whitelist()
def get_assignment_timeout_minutes():
    """
    A safe, whitelisted function that allows any logged-in user to fetch
    ONLY the assignment_timeout_minutes setting, without needing direct
    permission to the Admin Settings doctype.
    """
    # This server-side code has permission to read the setting.
    timeout = frappe.db.get_single_value("Admin Settings", "assignment_timeout_minutes")
    
    # Return the value, or a safe default of 60 if it's not set.
    return int(timeout or 60)