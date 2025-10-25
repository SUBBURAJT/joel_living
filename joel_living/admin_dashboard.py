import frappe
from frappe.utils import flt

@frappe.whitelist()
def get_lead_dashboard_data(lead_owner=None, from_date=None, to_date=None, custom_lead_category=None):
    # Build filters
    conditions = ["1=1"]
    values = {}

    if lead_owner:
        conditions.append("lead_owner = %(lead_owner)s")
        values["lead_owner"] = lead_owner
    if custom_lead_category:
        conditions.append("custom_lead_category = %(custom_lead_category)s")
        values["custom_lead_category"] = custom_lead_category
    if from_date:
        conditions.append("creation >= %(from_date)s")
        values["from_date"] = from_date
    if to_date:
        conditions.append("creation <= %(to_date)s")
        values["to_date"] = to_date

    where_clause = " AND ".join(conditions)

    # Summary Stats
    new_leads = frappe.db.count("Lead", filters=values)
    closed_leads = frappe.db.count("Lead", filters={**values, "custom_lead_status": "Closed"})
    lost_leads = frappe.db.count("Lead", filters={**values, "custom_lead_status": "Lead Lost"})

    # Total Sales Value
    total_sales_value = frappe.db.sql(f"""
        SELECT SUM(custom_budget_usd) as total
        FROM `tabLead`
        WHERE custom_lead_status='Closed' AND {where_clause}
    """, values, as_dict=True)
    total_sales_value = flt(total_sales_value[0].total) if total_sales_value else 0

    # Top Agent
    top_agent = frappe.db.sql(f"""
        SELECT lead_owner as name, COUNT(name) as closed_sales
        FROM `tabLead`
        WHERE custom_lead_status='Closed' AND {where_clause}
        GROUP BY lead_owner
        ORDER BY closed_sales DESC
        LIMIT 1
    """, values, as_dict=True)
    top_agent = top_agent[0] if top_agent else None

    # Conversion Rate
    conversion_rate = {
        "labels": ["Closed", "Lead Lost", "Open"],
        "datasets": [
            {"name": "Leads", "values": [closed_leads, lost_leads, max(new_leads - closed_leads - lost_leads, 0)]}
        ]
    }

    # Category Stats
    category_stats = frappe.db.sql(f"""
        SELECT
            custom_lead_category as category,
            COUNT(name) as leads,
            SUM(CASE WHEN custom_lead_status='Closed' THEN 1 ELSE 0 END) as sales
        FROM `tabLead`
        WHERE {where_clause}
        GROUP BY custom_lead_category
    """, values, as_dict=True)

    categories = [row.category for row in category_stats]
    leads_values = [row.leads for row in category_stats]
    sales_values = [row.sales for row in category_stats]

    chart_data = {
        "labels": categories,
        "datasets": [
            {"name": "Leads", "values": leads_values},
            {"name": "Sales", "values": sales_values}
        ]
    }

    return {
        "summary_stats": {
            "new_leads": new_leads,
            "closed_leads": closed_leads,
            "lost_leads": lost_leads,
            "total_sales_value": total_sales_value
        },
        "top_agent": top_agent,
        "conversion_rate": conversion_rate,
        "category_stats": {
            "categories": categories,
            "chart_data": chart_data
        }
    }
