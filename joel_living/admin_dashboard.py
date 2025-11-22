# import frappe
# from frappe.utils import flt, get_url, nowdate, add_days

# @frappe.whitelist()
# def get_lead_dashboard_data(lead_owner=None, from_date=None, to_date=None, custom_lead_category=None):
#     # --- Default Date Filter ---
#     # If no date range is provided, default to a precise 30-day period ending today.
#     if not from_date and not to_date:
#         to_date = nowdate()
#         from_date = add_days(to_date, -29)
        
   
#     if to_date:
#         to_date = f"{to_date} 23:59:59"

#     # --- ORM Filters ---
#     # The 'creation' filter now correctly uses the modified to_date with the time component.
#     orm_filters = {}
#     if lead_owner:
#         orm_filters["lead_owner"] = lead_owner
#     if custom_lead_category:
#         orm_filters["custom_lead_category"] = custom_lead_category
#     if from_date and to_date:
#         orm_filters["creation"] = ["between", (from_date, to_date)]
#     elif from_date:
#         orm_filters["creation"] = [">=", from_date]
#     elif to_date:
#         orm_filters["creation"] = ["<=", to_date]

#     # --- SQL Filters ---
#     # The SQL 'to_date' parameter will also correctly use the full datetime string.
#     sql_conditions, sql_params = ["1=1"], {}
#     if lead_owner:
#         sql_conditions.append("lead_owner = %(lead_owner)s")
#         sql_params["lead_owner"] = lead_owner
#     if custom_lead_category:
#         sql_conditions.append("custom_lead_category = %(custom_lead_category)s")
#         sql_params["custom_lead_category"] = custom_lead_category
#     if from_date:
#         sql_conditions.append("creation >= %(from_date)s")
#         sql_params["from_date"] = from_date
#     if to_date:
#         sql_conditions.append("creation <= %(to_date)s")
#         sql_params["to_date"] = to_date

#     where_clause = " AND ".join(sql_conditions)

#     # --- Summary Stats ---
#     new_leads = frappe.db.count("Lead", filters=orm_filters)
#     closed_leads = frappe.db.count("Lead", filters={**orm_filters, "custom_lead_status": "Closed"})
#     lost_leads = frappe.db.count("Lead", filters={**orm_filters, "custom_lead_status": "Lead Lost"})

#     total_sales = frappe.db.sql(
#         f"SELECT SUM(custom_budget_usd) AS total FROM `tabLead` WHERE custom_lead_status='Closed' AND {where_clause}",
#         sql_params, as_dict=True
#     )
#     total_sales_value = flt(total_sales[0].total) if total_sales and total_sales[0].total else 0

#     # --- Top Agents ---
#     top_agents = frappe.db.sql(
#         f"""
#         SELECT 
#             lead_owner AS name,
#             COUNT(name) AS total_leads,
#             SUM(CASE WHEN custom_lead_status = 'Closed' THEN 1 ELSE 0 END) AS closed_sales
#         FROM `tabLead`
#         WHERE lead_owner IS NOT NULL AND {where_clause}
#         GROUP BY lead_owner
#         ORDER BY closed_sales DESC
#         LIMIT 5
#         """,
#         sql_params, as_dict=True
#     )

#     # Assign top_agent safely
#     top_agent = top_agents[0] if top_agents else {}

#     # Assign profile images for all agents
#     for agent in top_agents:
#         image = frappe.db.get_value("User", agent["name"], "user_image")
#         agent["user_image"] = get_url(image) if image else None

#     # --- Top Agents Chart Data ---
#     top_agents_chart = {
#         "labels": [row["name"] for row in top_agents],
#         "datasets": [
#             {
#                 "name": "Closed Sales",
#                 "values": [row["closed_sales"] or 0 for row in top_agents]
#             }
#         ]
#     }

#     # --- Conversion Chart ---
#     open_leads = max(new_leads - closed_leads - lost_leads, 0)
#     conversion_data = {
#         "labels": ["Closed", "Lead Lost", "Open"],
#         "datasets": [{"name": "Leads", "values": [closed_leads, lost_leads, open_leads]}]
#     }

#     # --- Category Stats Chart ---
#     category_stats = frappe.db.sql(
#         f"""
#         SELECT custom_lead_category AS category,
#                COUNT(name) AS leads,
#                SUM(CASE WHEN custom_lead_status='Closed' THEN 1 ELSE 0 END) AS sales
#         FROM `tabLead`
#         WHERE custom_lead_category IS NOT NULL AND {where_clause}
#         GROUP BY custom_lead_category
#         ORDER BY category
#         """,
#         sql_params, as_dict=True
#     )
    
#     category_chart_data = {
#         "labels": [row["category"] for row in category_stats],
#         "datasets": [
#             {"name": "Leads", "values": [row["leads"] for row in category_stats]},
#             {"name": "Sales", "values": [row["sales"] for row in category_stats]},
#         ]
#     }

#     # --- Return Response ---
#     # Strip the time from the 'to_date' before sending back to the frontend for display consistency.
#     returned_to_date = to_date.split(" ")[0] if to_date else None
    
#     return {
#         "summary_stats": {
#             "new_leads": new_leads,
#             "closed_leads": closed_leads,
#             "lost_leads": lost_leads,
#             "total_sales_value": total_sales_value,
#         },
#         "top_agent": top_agent,
#         "top_agents_chart": top_agents_chart,
#         "conversion_rate": conversion_data,
#         "category_stats": {"chart_data": category_chart_data},
#         "date_range_applied": {
#             "from": from_date,
#             "to": returned_to_date
#         }
#     }








# import frappe
# from frappe.utils import flt, get_url, nowdate, add_days

# @frappe.whitelist()
# def get_sales_agents_for_filter():
#     """
#     Fetches users who explicitly have the 'Sales Agent' role.
#     """
#     return frappe.db.sql("""
#         SELECT DISTINCT u.name, u.full_name 
#         FROM `tabUser` u
#         JOIN `tabHas Role` hr ON hr.parent = u.name
#         WHERE hr.role = 'Sales Agent' AND u.enabled = 1
#         ORDER BY u.first_name ASC
#     """, as_dict=True)

# @frappe.whitelist()
# def get_lead_dashboard_data(lead_owner=None, from_date=None, to_date=None, custom_lead_category=None):
#     # --- 1. Date Range Logic ---
#     if not from_date and not to_date:
#         to_date = nowdate()
#         from_date = add_days(to_date, -29)
    
#     # Ensure we cover the full end-day time
#     to_date_time = f"{to_date} 23:59:59" if to_date else None
#     from_date_time = f"{from_date} 00:00:00" if from_date else None

#     # --- 2. Base Filters (Common) ---
#     base_filters = {}
#     if lead_owner:
#         base_filters["lead_owner"] = lead_owner
#     if custom_lead_category:
#         base_filters["custom_lead_category"] = custom_lead_category

#     # --- 3. Helper for constructing conditional filters ---
#     def get_specific_date_filter(date_field):
#         f = base_filters.copy()
#         if from_date and to_date:
#             f[date_field] = ["between", (from_date, to_date_time)]
#         elif from_date:
#             f[date_field] = [">=", from_date]
#         elif to_date:
#             f[date_field] = ["<=", to_date_time]
#         return f

#     # --- 4. Card Calculations ---
    
#     # A. New Leads (Filter: Creation Date)
#     new_leads_filters = get_specific_date_filter("creation")
#     new_leads_count = frappe.db.count("Lead", filters=new_leads_filters)

#     # B. Sales Closed (Filter: custom_sales_closed_date, Status: Closed)
#     closed_filters = get_specific_date_filter("custom_sales_closed_date")
#     closed_filters["custom_lead_status"] = "Closed"
#     closed_sales_count = frappe.db.count("Lead", filters=closed_filters)

#     # C. Lost Leads (Filter: custom_lead_lost_date, Status: Lead Lost)
#     lost_filters = get_specific_date_filter("custom_lead_lost_date")
#     lost_filters["custom_lead_status"] = "Lead Lost"
#     lost_leads_count = frappe.db.count("Lead", filters=lost_filters)

#     # D. Total Sales Value (From: Sales Registration Form)
#     # Requirement: Approved status, Unit Price sum, Filter by Owner/Creation
#     sales_conditions = ["status = 'Approved'"]
#     sales_params = {}

#     if lead_owner:
#         # Assuming the Agent is the 'owner' of the Sales Form
#         sales_conditions.append("owner = %(owner)s")
#         sales_params["owner"] = lead_owner
    
#     if from_date:
#         sales_conditions.append("creation >= %(from_date)s")
#         sales_params["from_date"] = from_date
#     if to_date:
#         sales_conditions.append("creation <= %(to_date)s")
#         sales_params["to_date"] = to_date_time

#     where_clause_sales = " AND ".join(sales_conditions)
    
#     sales_data = frappe.db.sql(f"""
#         SELECT SUM(unit_price) as total_val 
#         FROM `tabSales Registration Form`
#         WHERE {where_clause_sales}
#     """, sales_params, as_dict=True)

#     total_sales_value = flt(sales_data[0].total_val) if sales_data else 0

#     # --- 5. Chart Data Logic ---
    
#     # Logic for "Top Agent": Group by lead_owner using date filter logic (Defaulting to creation for performance, or closed date if preferred)
#     # To keep consistency with previous dashboards, we usually filter charts by Creation date of the Lead
#     chart_conditions = ["1=1"]
#     chart_params = {}
    
#     if lead_owner:
#         chart_conditions.append("lead_owner = %(lead_owner)s")
#         chart_params["lead_owner"] = lead_owner
#     if custom_lead_category:
#         chart_conditions.append("custom_lead_category = %(cat)s")
#         chart_params["cat"] = custom_lead_category
#     if from_date:
#         chart_conditions.append("creation >= %(start)s")
#         chart_params["start"] = from_date
#     if to_date:
#         chart_conditions.append("creation <= %(end)s")
#         chart_params["end"] = to_date_time

#     chart_where = " AND ".join(chart_conditions)

#     # Top Agent Query
#     top_agents_sql = frappe.db.sql(f"""
#         SELECT lead_owner AS name,
#                COUNT(name) AS total_leads,
#                SUM(CASE WHEN custom_lead_status = 'Closed' THEN 1 ELSE 0 END) AS closed_sales
#         FROM `tabLead`
#         WHERE lead_owner IS NOT NULL AND {chart_where}
#         GROUP BY lead_owner
#         ORDER BY closed_sales DESC
#         LIMIT 5
#     """, chart_params, as_dict=True)

#     top_agent_data = top_agents_sql[0] if top_agents_sql else {}
    
#     # Process images for top agents
#     for ag in top_agents_sql:
#         img_path = frappe.db.get_value("User", ag["name"], "user_image")
#         ag["user_image"] = get_url(img_path) if img_path else None

#     top_agents_chart = {
#         "labels": [r["name"] for r in top_agents_sql],
#         "datasets": [{"name": "Closed Sales", "values": [r["closed_sales"] for r in top_agents_sql]}]
#     }

#     # Category Chart Query
#     category_sql = frappe.db.sql(f"""
#         SELECT custom_lead_category as cat, 
#                COUNT(name) as leads,
#                SUM(CASE WHEN custom_lead_status='Closed' THEN 1 ELSE 0 END) as sales
#         FROM `tabLead`
#         WHERE custom_lead_category IS NOT NULL AND {chart_where}
#         GROUP BY custom_lead_category
#     """, chart_params, as_dict=True)

#     cat_chart_data = {
#         "labels": [r["cat"] for r in category_sql],
#         "datasets": [
#             {"name": "Leads", "values": [r["leads"] for r in category_sql]},
#             {"name": "Sales", "values": [r["sales"] for r in category_sql]}
#         ]
#     }
    
#     # Simple conversion for Donut
#     # Recalculate counts strictly based on creation range for chart visual consistency
#     c_closed = frappe.db.count("Lead", filters={**base_filters, "creation": ["between", [from_date, to_date_time]], "custom_lead_status": "Closed"})
#     c_lost = frappe.db.count("Lead", filters={**base_filters, "creation": ["between", [from_date, to_date_time]], "custom_lead_status": "Lead Lost"})
#     c_all = frappe.db.count("Lead", filters={**base_filters, "creation": ["between", [from_date, to_date_time]]})
#     c_open = max(c_all - c_closed - c_lost, 0)

#     return {
#         "summary_stats": {
#             "new_leads": new_leads_count,
#             "closed_sales": closed_sales_count,
#             "lost_leads": lost_leads_count,
#             "total_sales_value": total_sales_value,
#         },
#         "top_agent": top_agent_data,
#         "top_agents_chart": top_agents_chart,
#         "conversion_rate": {
#             "labels": ["Closed", "Lead Lost", "Open"],
#             "datasets": [{"name": "Status", "values": [c_closed, c_lost, c_open]}]
#         },
#         "category_stats": {"chart_data": cat_chart_data},
#         "applied_range": {"from": from_date, "to": to_date}
#     }



import frappe
from frappe.utils import flt, get_url, nowdate, add_days
import json

@frappe.whitelist()
def get_lead_dashboard_data(lead_owner=None, from_date=None, to_date=None, custom_lead_category=None):
    # ... (Date & Filter Logic Remains Same) ...
    if not from_date and not to_date:
        to_date = nowdate()
        from_date = add_days(to_date, -29)
    
    to_date_time = f"{to_date} 23:59:59" if to_date else None
    
    base_filters = {}
    if lead_owner: base_filters["lead_owner"] = lead_owner
    if custom_lead_category: base_filters["custom_lead_category"] = custom_lead_category

    # ... (Stats Counts 1-4 Remain Same) ... 
    # 1. New Leads
    new_filters = base_filters.copy()
    new_filters["creation"] = ["between", (from_date, to_date_time)]
    new_leads_count = frappe.db.count("Lead", filters=new_filters)

    # 2. Sales Closed
    closed_filters = base_filters.copy()
    closed_filters["custom_sales_closed_date"] = ["between", (from_date, to_date_time)]
    closed_filters["custom_lead_status"] = "Closed"
    closed_sales_count = frappe.db.count("Lead", filters=closed_filters)

    # 3. Lost Leads
    lost_filters = base_filters.copy()
    lost_filters["custom_lead_lost_date"] = ["between", (from_date, to_date_time)]
    lost_filters["custom_lead_status"] = "Lead Lost"
    lost_leads_count = frappe.db.count("Lead", filters=lost_filters)

    # 4. Total Sales Value
    # build base conditions (use aliases s for sales, l for lead)
    sales_conditions = [
        "s.status = 'Approved'",
        "s.creation >= %(from)s",
        "s.creation <= %(to)s"
    ]
    sales_params = {"from": from_date, "to": to_date_time}

    if lead_owner:
        sales_conditions.append("s.owner = %(owner)s")
        sales_params["owner"] = lead_owner

    # join to Lead to filter by custom_lead_category
    join_sql = ""
    if custom_lead_category:
        join_sql = "JOIN `tabLead` l ON s.lead = l.name"
        sales_conditions.append("l.custom_lead_category = %(cat)s")
        sales_params["cat"] = custom_lead_category

    where_sql = " AND ".join(sales_conditions)

    total_sales_value = frappe.db.sql("""
        SELECT COALESCE(SUM(s.unit_price), 0)
        FROM `tabSales Registration Form` s
        {join}
        WHERE {where}
    """.format(join=join_sql, where=where_sql), sales_params)[0][0] or 0.0


    # --- 5. TOP AGENT CHART (UPDATED) ---
    
    # Setup Chart Filters
    chart_params = {"start": from_date, "end": to_date_time}
    chart_conditions = ["l.creation BETWEEN %(start)s AND %(end)s", "l.lead_owner IS NOT NULL", "l.lead_owner != ''"]
    if lead_owner:
        chart_conditions.append("l.lead_owner = %(lead_owner)s")
        chart_params["lead_owner"] = lead_owner
    if custom_lead_category:
        chart_conditions.append("l.custom_lead_category = %(cat)s")
        chart_params["cat"] = custom_lead_category

    where_sql = " AND ".join(chart_conditions)

    # Query
    top_agents_sql = frappe.db.sql(f"""
        SELECT 
            COALESCE(u.full_name, l.lead_owner) AS name,
            u.user_image, 
            COUNT(l.name) AS total_leads,
            SUM(CASE WHEN l.custom_lead_status = 'Closed' THEN 1 ELSE 0 END) AS closed_sales
        FROM `tabLead` l
        LEFT JOIN `tabUser` u ON l.lead_owner = u.name
        WHERE {where_sql}
        GROUP BY l.lead_owner
        ORDER BY closed_sales DESC, total_leads DESC
        LIMIT 5
    """, chart_params, as_dict=True)

    # Helper Maps
    # 1. Main Chart Data (Single Dataset = Single Bar)
    top_agents_chart = {
        "labels": [r["name"] for r in top_agents_sql],
        "datasets": [{"name": "Closed Sales", "values": [r["closed_sales"] for r in top_agents_sql]}]
    }
    
    # 2. Agent Lead Lookup Map (Used by JS for Tooltip)
    agent_lead_map = {r["name"]: r["total_leads"] for r in top_agents_sql}
    
    # 3. Top Agent Text Details
    top_agent_data = top_agents_sql[0] if top_agents_sql else {}
    if top_agent_data.get("user_image"):
         top_agent_data["user_image"] = get_url(top_agent_data["user_image"])

    # --- 6. OTHER CHARTS (Remains Same) ---
    
    # Category Chart
    category_sql = frappe.db.sql(f"""
        SELECT custom_lead_category as cat, COUNT(name) as leads, SUM(CASE WHEN custom_lead_status='Closed' THEN 1 ELSE 0 END) as sales
        FROM `tabLead` WHERE custom_lead_category IS NOT NULL AND creation BETWEEN %(start)s AND %(end)s GROUP BY custom_lead_category
    """, {"start": from_date, "end": to_date_time}, as_dict=True)

    cat_chart_data = {
        "labels": [r["cat"] for r in category_sql],
        "datasets": [
            {"name": "Leads", "values": [r["leads"] for r in category_sql]},
            {"name": "Sales", "values": [r["sales"] for r in category_sql]}
        ]
    }

    # Conversion Rate
    c_closed = closed_sales_count
    c_lost = lost_leads_count
    open_filters = base_filters.copy()
    open_filters["creation"] = ["between", (from_date, to_date_time)]
    open_filters["custom_lead_status"] = ["not in", ["Closed", "Lead Lost"]]
    c_open = frappe.db.count("Lead", filters=open_filters)

    return {
        "summary_stats": {
            "new_leads": new_leads_count,
            "closed_sales": closed_sales_count,
            "lost_leads": lost_leads_count,
            "total_sales_value": total_sales_value,
        },
        "top_agent": top_agent_data,
        "top_agents_chart": top_agents_chart,
        "agent_lead_map": agent_lead_map,  # <--- Sending map to JS
        "conversion_rate": {
            "labels": ["Closed", "Lead Lost", "Open"],
            "datasets": [{"name": "Status", "values": [c_closed, c_lost, c_open]}]
        },
        "category_stats": {"chart_data": cat_chart_data}
    }

@frappe.whitelist()
def get_sales_agents_for_filter():
    return frappe.db.sql("""
        SELECT DISTINCT u.name, u.full_name 
        FROM `tabUser` u
        JOIN `tabHas Role` hr ON hr.parent = u.name
        WHERE hr.role = 'Sales Agent' AND u.enabled = 1
        ORDER BY u.first_name ASC
    """, as_dict=True)