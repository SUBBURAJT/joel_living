import frappe
from frappe.utils import flt, get_url, nowdate, add_days

@frappe.whitelist()
def get_lead_dashboard_data(lead_owner=None, from_date=None, to_date=None, custom_lead_category=None):
    # --- Default Date Filter ---
    # If no date range is provided, default to a precise 30-day period ending today.
    if not from_date and not to_date:
        to_date = nowdate()
        from_date = add_days(to_date, -29)
        
    # --- Date Handling for DateTime Fields (Key Change) ---
    # If a to_date is present, append the time to ensure the query includes
    # all records from that entire day, up to 23:59:59.
    # This corrects the issue where records from "today" were being excluded.
    if to_date:
        to_date = f"{to_date} 23:59:59"

    # --- ORM Filters ---
    # The 'creation' filter now correctly uses the modified to_date with the time component.
    orm_filters = {}
    if lead_owner:
        orm_filters["lead_owner"] = lead_owner
    if custom_lead_category:
        orm_filters["custom_lead_category"] = custom_lead_category
    if from_date and to_date:
        orm_filters["creation"] = ["between", (from_date, to_date)]
    elif from_date:
        orm_filters["creation"] = [">=", from_date]
    elif to_date:
        orm_filters["creation"] = ["<=", to_date]

    # --- SQL Filters ---
    # The SQL 'to_date' parameter will also correctly use the full datetime string.
    sql_conditions, sql_params = ["1=1"], {}
    if lead_owner:
        sql_conditions.append("lead_owner = %(lead_owner)s")
        sql_params["lead_owner"] = lead_owner
    if custom_lead_category:
        sql_conditions.append("custom_lead_category = %(custom_lead_category)s")
        sql_params["custom_lead_category"] = custom_lead_category
    if from_date:
        sql_conditions.append("creation >= %(from_date)s")
        sql_params["from_date"] = from_date
    if to_date:
        sql_conditions.append("creation <= %(to_date)s")
        sql_params["to_date"] = to_date

    where_clause = " AND ".join(sql_conditions)

    # --- Summary Stats ---
    new_leads = frappe.db.count("Lead", filters=orm_filters)
    closed_leads = frappe.db.count("Lead", filters={**orm_filters, "custom_lead_status": "Closed"})
    lost_leads = frappe.db.count("Lead", filters={**orm_filters, "custom_lead_status": "Lead Lost"})

    total_sales = frappe.db.sql(
        f"SELECT SUM(custom_budget_usd) AS total FROM `tabLead` WHERE custom_lead_status='Closed' AND {where_clause}",
        sql_params, as_dict=True
    )
    total_sales_value = flt(total_sales[0].total) if total_sales and total_sales[0].total else 0

    # --- Top Agents ---
    top_agents = frappe.db.sql(
        f"""
        SELECT 
            lead_owner AS name,
            COUNT(name) AS total_leads,
            SUM(CASE WHEN custom_lead_status = 'Closed' THEN 1 ELSE 0 END) AS closed_sales
        FROM `tabLead`
        WHERE lead_owner IS NOT NULL AND {where_clause}
        GROUP BY lead_owner
        ORDER BY closed_sales DESC
        LIMIT 5
        """,
        sql_params, as_dict=True
    )

    # Assign top_agent safely
    top_agent = top_agents[0] if top_agents else {}

    # Assign profile images for all agents
    for agent in top_agents:
        image = frappe.db.get_value("User", agent["name"], "user_image")
        agent["user_image"] = get_url(image) if image else None

    # --- Top Agents Chart Data ---
    top_agents_chart = {
        "labels": [row["name"] for row in top_agents],
        "datasets": [
            {
                "name": "Closed Sales",
                "values": [row["closed_sales"] or 0 for row in top_agents]
            }
        ]
    }

    # --- Conversion Chart ---
    open_leads = max(new_leads - closed_leads - lost_leads, 0)
    conversion_data = {
        "labels": ["Closed", "Lead Lost", "Open"],
        "datasets": [{"name": "Leads", "values": [closed_leads, lost_leads, open_leads]}]
    }

    # --- Category Stats Chart ---
    category_stats = frappe.db.sql(
        f"""
        SELECT custom_lead_category AS category,
               COUNT(name) AS leads,
               SUM(CASE WHEN custom_lead_status='Closed' THEN 1 ELSE 0 END) AS sales
        FROM `tabLead`
        WHERE custom_lead_category IS NOT NULL AND {where_clause}
        GROUP BY custom_lead_category
        ORDER BY category
        """,
        sql_params, as_dict=True
    )
    
    category_chart_data = {
        "labels": [row["category"] for row in category_stats],
        "datasets": [
            {"name": "Leads", "values": [row["leads"] for row in category_stats]},
            {"name": "Sales", "values": [row["sales"] for row in category_stats]},
        ]
    }

    # --- Return Response ---
    # Strip the time from the 'to_date' before sending back to the frontend for display consistency.
    returned_to_date = to_date.split(" ")[0] if to_date else None
    
    return {
        "summary_stats": {
            "new_leads": new_leads,
            "closed_leads": closed_leads,
            "lost_leads": lost_leads,
            "total_sales_value": total_sales_value,
        },
        "top_agent": top_agent,
        "top_agents_chart": top_agents_chart,
        "conversion_rate": conversion_data,
        "category_stats": {"chart_data": category_chart_data},
        "date_range_applied": {
            "from": from_date,
            "to": returned_to_date
        }
    }