import frappe

# ---------------------------
# List View / Query Conditions
# ---------------------------



def get_sales_agent_lead_conditions(user):
    roles = frappe.get_roles(user)

    if any(r in roles for r in ["Admin", "Super Admin"]):
        return ""

    if "Sales Agent" not in roles:
        return ""

    # Start with only leads owned by the user
    conditions = [f"`tabLead`.lead_owner = {frappe.db.escape(user)}"]

    try:
        admin_settings = frappe.get_doc("Admin Settings")
    except frappe.DoesNotExistError:
        return "(" + " OR ".join(conditions) + ")"

    restrictions = getattr(admin_settings, "user_lead_restrictions", []) or []
    user_rows = [r for r in restrictions if r.user == user]

    # Check if user can see unassigned leads
    if not user_rows:
        # No restrictions → can see all unassigned leads
        conditions.append("`tabLead`.lead_owner IS NULL OR `tabLead`.lead_owner = ''")
    else:
        for r in user_rows:
            try:
                cats = frappe.parse_json(r.lead_category or "[]")
                sources = frappe.parse_json(r.main_lead_source or "[]")
            except Exception:
                continue
            
            sub_conditions = []
            cats.append("Meta Leads")  # Always include Meta Leads
            if cats:
                print(f"[DEBUG] User {user} restriction categories: {cats}")
                cats_sql = ",".join([frappe.db.escape(c) for c in cats])
                sub_conditions.append(f"`tabLead`.custom_lead_category IN ({cats_sql})")
            if sources:
                sources_sql = ",".join([frappe.db.escape(s) for s in sources])
                sub_conditions.append(f"`tabLead`.custom_main_lead_source IN ({sources_sql})")

            # Only unassigned leads
            sub_conditions.append("(`tabLead`.lead_owner IS NULL OR `tabLead`.lead_owner = '')")

            if sub_conditions:
                conditions.append("(" + " AND ".join(sub_conditions) + ")")

    final_condition = "(" + " OR ".join(conditions) + ")"
    print(f"[DEBUG] Final SQL condition for {user}: {final_condition}")
    return final_condition

# def get_sales_agent_lead_conditions(user):
#     roles = frappe.get_roles(user)
#     # print(f"[DEBUG] User: {user}, Roles: {roles}")

#     # Admin / Super Admin → see all
#     if any(r in roles for r in ["Admin", "Super Admin"]):
#         # print(f"[DEBUG] User {user} is Admin/Super Admin → all leads visible")
#         return ""

#     # Only Sales Agent → apply restrictions
#     if "Sales Agent" not in roles:
#         # print(f"[DEBUG] User {user} is NOT Sales Agent → all leads visible")
#         return ""

#     # print(f"[DEBUG] User {user} is Sales Agent → applying restrictions")

#     conditions = [
#         f"`tabLead`.lead_owner = {frappe.db.escape(user)}",
#         "`tabLead`.lead_owner IS NULL OR `tabLead`.lead_owner = ''"
#     ]

#     # Add unassigned leads based on Admin Settings
#     try:
#         admin_settings = frappe.get_doc("Admin Settings")
#     except frappe.DoesNotExistError:
#         return "(" + " OR ".join(conditions) + ")"

#     restrictions = getattr(admin_settings, "user_lead_restrictions", []) or []
#     user_rows = [r for r in restrictions if r.user == user]

#     for r in user_rows:
#         try:
#             cats = frappe.parse_json(r.lead_category or "[]")
#             sources = frappe.parse_json(r.main_lead_source or "[]")
#         except Exception:
#             continue

#         sub_conditions = []

#         if cats:
#             cats_sql = ",".join([frappe.db.escape(c) for c in cats])
#             sub_conditions.append(f"`tabLead`.custom_lead_category IN ({cats_sql})")
#         if sources:
#             sources_sql = ",".join([frappe.db.escape(s) for s in sources])
#             sub_conditions.append(f"`tabLead`.custom_main_lead_source IN ({sources_sql})")

#         # Only unassigned leads
#         sub_conditions.append("(`tabLead`.lead_owner IS NULL OR `tabLead`.lead_owner = '')")

#         if sub_conditions:
#             conditions.append("(" + " AND ".join(sub_conditions) + ")")

#     final_condition = "(" + " OR ".join(conditions) + ")"
#     print(f"[DEBUG] Final SQL condition for {user}: {final_condition}")
#     return final_condition



# ---------------------------
# Form / Document Access Check
# ---------------------------
@frappe.whitelist()
def has_sales_agent_lead_permission(doc, user):
    """
    Determine if a user has write access to a Lead.
    Returns True → full access (read/write)
    Returns False → read-only
    """
    roles = frappe.get_roles(user)

    # Admin / Super Admin → full access
    if any(r in roles for r in ["Admin", "Super Admin"]):
        return True

    # Non-Sales Agent → full access
    if "Sales Agent" not in roles:
        return True

    # Lead owner → full access
    if getattr(doc, "lead_owner", None) == user:
        return True

    # Sales Agent → unassigned lead → allow claiming if Admin Settings permit
    if not getattr(doc, "lead_owner", None):
        try:
            admin_settings = frappe.get_doc("Admin Settings")
        except frappe.DoesNotExistError:
            return False

        restrictions = getattr(admin_settings, "user_lead_restrictions", []) or []
        user_rows = [r for r in restrictions if r.user == user]
        if not user_rows:
            return True  # No restrictions → can claim any unassigned lead

        for r in user_rows:
            try:
                cats = frappe.parse_json(r.lead_category or "[]")
                sources = frappe.parse_json(r.main_lead_source or "[]")
            except Exception:
                continue

            if (not cats or getattr(doc, "custom_lead_category", None) in cats) and \
               (not sources or getattr(doc, "custom_main_lead_source", None) in sources):
                return True

    # All other Sales Agent → read-only
    return False
import frappe
from frappe.utils import now_datetime
from frappe.utils.background_jobs import enqueue
from frappe import _

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

import frappe
from frappe.utils import now_datetime, add_to_date
from frappe.utils.background_jobs import enqueue
import frappe
from frappe.utils import now_datetime, add_to_date
from frappe.utils.background_jobs import enqueue

@frappe.whitelist()
def assign_lead_to_me(lead_name, delay_hours=1):
    """
    Assign a lead to the current user and schedule unassign in delay_hours.
    """
    user = frappe.session.user
    doc = frappe.get_doc("Lead", lead_name)

    if doc.lead_owner:
        frappe.throw("Lead already assigned.")

    # Assign lead immediately
    doc.lead_owner = user
    doc.custom_lead_status = "Open"
    doc.custom_assigned_at = now_datetime()
    doc.save(ignore_permissions=True)
    frappe.db.commit()

    # Schedule delayed unassign job
    scheduled_time = add_to_date(doc.custom_assigned_at, hours=delay_hours)

    frappe.logger().info(f"[AssignLead] Current time: {now_datetime()}")
    frappe.logger().info(f"[AssignLead] Scheduled unassign time: {scheduled_time}")

    enqueue(
        "joel_living.lead_permission.delayed_unassign_job",
        queue="short",
        lead=lead_name,
        assigned_time=str(doc.custom_assigned_at),
        scheduled_time=scheduled_time,
        is_async=True,
        enqueue_after_commit=True
    )

    return {"status": "success", "message": f"Lead {lead_name} assigned to you"}


def delayed_unassign_job(lead, assigned_time, **kwargs):
    """
    Unassign lead if still Open and assignment unchanged.
    Logs debug information to track delay.
    """
    current_time = now_datetime()
    frappe.logger().info(f"[DelayedUnassign] Job triggered for Lead {lead} at {current_time}")
    frappe.logger().info(f"[DelayedUnassign] Expected assigned_time: {assigned_time}")

    try:
        doc = frappe.get_doc("Lead", lead)
        frappe.logger().info(f"[DelayedUnassign] Lead's current assigned_at: {doc.custom_assigned_at}")

        # Ensure exact match (ignore microseconds)
        assigned_time_doc = str(doc.custom_assigned_at).split('.')[0]
        assigned_time_job = str(assigned_time).split('.')[0]

        if (
            doc.custom_lead_status == "Open"
            and doc.lead_owner
            and assigned_time_doc == assigned_time_job
        ):
            old_owner = doc.lead_owner
            doc.lead_owner = None
            doc.custom_assigned_at = None
            doc.save(ignore_permissions=True)
            frappe.db.commit()
            frappe.logger().info(f"[DelayedUnassign] Lead {lead} unassigned (old owner: {old_owner})")
        else:
            frappe.logger().info(
                f"[DelayedUnassign] Lead {lead} not unassigned. "
                f"Status or assignment changed. Current: {doc.custom_lead_status}, "
                f"Owner: {doc.lead_owner}, Assigned_at: {doc.custom_assigned_at}"
            )

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), f"[DelayedUnassign] Error for Lead {lead}")
        frappe.logger().error(f"[DelayedUnassign] {e}")
