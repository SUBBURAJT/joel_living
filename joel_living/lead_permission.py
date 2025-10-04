import frappe

# ---------------------------
# List View / Query Conditions
# ---------------------------
def get_sales_agent_lead_conditions(user):
    roles = frappe.get_roles(user)
    # print(f"[DEBUG] User: {user}, Roles: {roles}")

    # Admin / Super Admin → see all
    if any(r in roles for r in ["Admin", "Super Admin"]):
        # print(f"[DEBUG] User {user} is Admin/Super Admin → all leads visible")
        return ""

    # Only Sales Agent → apply restrictions
    if "Sales Agent" not in roles:
        # print(f"[DEBUG] User {user} is NOT Sales Agent → all leads visible")
        return ""

    # print(f"[DEBUG] User {user} is Sales Agent → applying restrictions")

    conditions = [f"`tabLead`.lead_owner = {frappe.db.escape(user)}"]

    # Add unassigned leads based on Admin Settings
    try:
        admin_settings = frappe.get_doc("Admin Settings")
    except frappe.DoesNotExistError:
        return "(" + " OR ".join(conditions) + ")"

    restrictions = getattr(admin_settings, "user_lead_restrictions", []) or []
    user_rows = [r for r in restrictions if r.user == user]

    for r in user_rows:
        try:
            cats = frappe.parse_json(r.lead_category or "[]")
            sources = frappe.parse_json(r.main_lead_source or "[]")
        except Exception:
            continue

        sub_conditions = []

        if cats:
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
    # print(f"[DEBUG] Final SQL condition for {user}: {final_condition}")
    return final_condition

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
            return False

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
from frappe import _
def allow_write_for_lead_owner(doc, method):
    """Allow editing only if the user is lead_owner or lead is unassigned"""
    user = frappe.session.user
    roles = frappe.get_roles(user)

    if any(r in roles for r in ["Administrator", "Sales Manager"]):
        return  # Full access

    if "Sales Agent" in roles:
        if not doc.lead_owner:
            return  # Unassigned → can claim
        if doc.lead_owner == user:
            return  # Owner → full edit
        frappe.throw(_("You are not allowed to edit this Lead."))

import frappe

@frappe.whitelist()
def assign_lead_to_me(lead_name):
    """
    Assign the lead_owner to the session user, ignoring normal role permissions.
    Safe for Sales Agents without Write permission.
    """
    user = frappe.session.user

    # Fetch Lead doc ignoring permissions
    doc = frappe.get_doc("Lead", lead_name)

    if doc.lead_owner:
        frappe.throw(f"This Lead is already assigned to {doc.lead_owner}.")

    # Assign to current user
    doc.lead_owner = user

    # Save ignoring permissions
    doc.save(ignore_permissions=True)

    return {
        "status": "success",
        "message": f"Lead assigned to {user}"
    }
