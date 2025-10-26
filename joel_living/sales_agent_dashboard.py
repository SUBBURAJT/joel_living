import frappe
from frappe.utils import nowdate, add_days
from collections import defaultdict

@frappe.whitelist()
def get_agent_dashboard_data(from_date=None, to_date=None, custom_lead_category=None):
    """
    Fetch dynamic dashboard data strictly for the logged-in sales agent.
    """
    current_user = frappe.session.user
    
    # Get current user details for the performance card
    user_details = frappe.get_value("User", current_user, ["full_name", "user_image"], as_dict=True)

    if not from_date and not to_date:
        to_date = nowdate()
        from_date = add_days(to_date, -29)
        
    # --- Date Handling for DateTime Fields (Key Change) ---
    # If a to_date is present, append the time to ensure the query includes
    # all records from that entire day, up to 23:59:59.
    # This corrects the issue where records from "today" were being excluded.
    if to_date:
        to_date = f"{to_date} 23:59:59"

    # --- Filters ---
    # `lead_owner` is now hard-coded to the logged-in user
    common_filters = {
        "lead_owner": current_user,
        "creation": ["between", [from_date, to_date]],
    }
    if custom_lead_category:
        common_filters["custom_lead_category"] = custom_lead_category

    # --- Summary Stats ---
    new_leads_count = frappe.db.count("Lead", filters=common_filters)
    closed_leads_count = frappe.db.count("Lead", filters={**common_filters, "custom_lead_status": "Closed"})
    lost_leads_count = frappe.db.count("Lead", filters={**common_filters, "custom_lead_status": "Lead Lost"})
    
    total_sales_value = frappe.db.get_value(
        "Lead",
        filters={**common_filters, "custom_lead_status": "Closed"},
        fieldname="SUM(custom_budget_usd)"
    ) or 0

    # --- Data for Charts (Leads & Sales by Category) ---
    leads_for_charts = frappe.get_all(
        "Lead",
        filters=common_filters,
        fields=["custom_lead_category", "custom_lead_status"]
    )

    stats_by_category = defaultdict(lambda: {"total_leads": 0, "closed_leads": 0})

    for lead in leads_for_charts:
        category = lead.get("custom_lead_category") or "Uncategorized"
        status = lead.get("custom_lead_status")
        stats_by_category[category]["total_leads"] += 1
        if status == "Closed":
            stats_by_category[category]["closed_leads"] += 1

    sorted_categories = sorted(stats_by_category.keys())
    
    # --- Agent Performance Info & Chart ---
    current_agent_details = {
        "name": user_details.full_name,
        "user_image": user_details.user_image,
        "closed_sales": closed_leads_count,
        "total_leads": new_leads_count
    }

    # Chart data showing sales closed by the agent across categories
    agent_performance_chart = {
        "labels": sorted_categories,
        "datasets": [
            {"name": "My Sales Closed", "values": [stats_by_category[cat]["closed_leads"] for cat in sorted_categories]}
        ]
    }
    
    # --- Category Stats Chart ---
    category_stats_chart = {
        "labels": sorted_categories,
        "datasets": [
            {"name": "Leads", "values": [stats_by_category[cat]["total_leads"] for cat in sorted_categories]},
            {"name": "Sales", "values": [stats_by_category[cat]["closed_leads"] for cat in sorted_categories]},
        ]
    }

    return {
        "summary_stats": {
            "new_leads": new_leads_count,
            "closed_leads": closed_leads_count,
            "lost_leads": lost_leads_count,
            "total_sales_value": total_sales_value
        },
        "current_agent_details": current_agent_details,
        "agent_performance_chart": agent_performance_chart,
        "category_stats_chart": category_stats_chart
    }