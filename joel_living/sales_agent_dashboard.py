



# import frappe
# from frappe.utils import flt, get_url, nowdate, add_days
# from collections import defaultdict

# @frappe.whitelist()
# def get_agent_dashboard_data(from_date=None, to_date=None, custom_lead_category=None):
#     current_user = frappe.session.user
    
#     # --- 1. Default Date Logic ---
#     if not from_date and not to_date:
#         to_date = nowdate()
#         from_date = add_days(to_date, -29)
    
#     to_date_time = f"{to_date} 23:59:59" if to_date else None

#     # --- 2. Personal Stats (My Data Only) ---
#     # Used for the Summary Cards
#     my_filters = {
#         "lead_owner": current_user,
#         "creation": ["between", [from_date, to_date_time]]
#     }
#     if custom_lead_category:
#         my_filters["custom_lead_category"] = custom_lead_category

#     # A. Summary Counts
#     new_leads_count = frappe.db.count("Lead", filters=my_filters)
    
#     # Closed (Based on Sales Closed Date)
#     closed_leads_count = frappe.db.count("Lead", filters={
#         "lead_owner": current_user,
#         "custom_lead_status": "Closed",
#         "custom_sales_closed_date": ["between", [from_date, to_date_time]]
#     })
    
#     # Lost (Based on Lost Date)
#     lost_leads_count = frappe.db.count("Lead", filters={
#         "lead_owner": current_user,
#         "custom_lead_status": "Lead Lost",
#         "custom_lead_lost_date": ["between", [from_date, to_date_time]]
#     })

#     # B. Total Sales Value (SQL for My Sales Only)
#     sales_params = {"owner": current_user, "from": from_date, "to": to_date_time}
#     conditions = ["s.status='Approved'", "s.owner=%(owner)s", "s.creation >= %(from)s", "s.creation <= %(to)s"]
#     join_clause = ""
#     if custom_lead_category:
#         join_clause = "INNER JOIN `tabLead` l ON s.lead = l.name"
#         conditions.append("l.custom_lead_category = %(cat)s")
#         sales_params["cat"] = custom_lead_category

#     my_sales_val = frappe.db.sql(f"""
#         SELECT SUM(s.unit_price) FROM `tabSales Registration Form` s {join_clause} WHERE {' AND '.join(conditions)}
#     """, sales_params)
#     total_sales_value = flt(my_sales_val[0][0]) if my_sales_val else 0.0

#     # --- 3. LEADERBOARD CHART (Comparision: Me vs Others) ---
#     # Query leads for ALL users to generate a rank list
#     # NOTE: filters are creation-date based for fairness in "Performance Period"
    
#     lb_params = {"start": from_date, "end": to_date_time}
#     lb_where = ["l.creation BETWEEN %(start)s AND %(end)s", "l.lead_owner IS NOT NULL", "l.lead_owner != ''"]
    
#     if custom_lead_category:
#         lb_where.append("l.custom_lead_category = %(cat)s")
#         lb_params["cat"] = custom_lead_category
    
#     lb_sql = " AND ".join(lb_where)

#     # Fetch Top 10 Agents by Closed Sales
#     leaderboard_data = frappe.db.sql(f"""
#         SELECT 
#             COALESCE(u.full_name, l.lead_owner) as agent_name,
#             COUNT(l.name) as total_leads,
#             SUM(CASE WHEN l.custom_lead_status='Closed' THEN 1 ELSE 0 END) as closed_sales
#         FROM `tabLead` l
#         LEFT JOIN `tabUser` u ON l.lead_owner = u.name
#         WHERE {lb_sql}
#         GROUP BY l.lead_owner
#         ORDER BY closed_sales DESC, total_leads DESC
#         LIMIT 10
#     """, lb_params, as_dict=True)

#     # Construct "My Performance vs Others" Chart
#     agent_performance_chart = {
#         "labels": [r["agent_name"] for r in leaderboard_data],
#         "datasets": [
#             {"name": "Closed Sales", "values": [r["closed_sales"] for r in leaderboard_data]}
#         ]
#     }

#     # Map for Tooltip (Shows Total Leads vs Closed Sales)
#     agent_lookup_map = {r["agent_name"]: r["total_leads"] for r in leaderboard_data}

#     # --- 4. Category Stats (Just for Me) ---
#     # The user specifically wanted "My" breakdown for categories usually
#     cat_params = my_filters.copy() # Reuse specific date filter from above
#     # Since frappe.get_all filters are restrictive, using simple SQL to aggregate "My Categories"
    
#     cat_leads = frappe.db.get_all("Lead", filters=my_filters, fields=["custom_lead_category", "custom_lead_status"])
#     cat_stats = defaultdict(lambda: {"total": 0, "closed": 0})

#     for l in cat_leads:
#         c = l.custom_lead_category or "Uncategorized"
#         cat_stats[c]["total"] += 1
#         if l.custom_lead_status == "Closed":
#             cat_stats[c]["closed"] += 1
            
#     sorted_cats = sorted(cat_stats.keys())
    
#     category_stats_chart = {
#         "labels": sorted_cats,
#         "datasets": [
#             {"name": "My Leads", "values": [cat_stats[c]["total"] for c in sorted_cats]},
#             {"name": "My Sales", "values": [cat_stats[c]["closed"] for c in sorted_cats]}
#         ]
#     }

#     # --- 5. User Details Card ---
#     u_det = frappe.db.get_value("User", current_user, ["full_name", "user_image"], as_dict=True)
#     my_info = {
#         "name": u_det.full_name or current_user,
#         "user_image": get_url(u_det.user_image) if u_det.user_image else None,
#         "closed_sales": closed_leads_count,
#         "total_leads": new_leads_count
#     }

#     return {
#         "summary_stats": {
#             "new_leads": new_leads_count,
#             "closed_leads": closed_leads_count,
#             "lost_leads": lost_leads_count,
#             "total_sales_value": total_sales_value
#         },
#         "current_agent_details": my_info,
#         "agent_performance_chart": agent_performance_chart, # NOW LEADERBOARD
#         "agent_lookup_map": agent_lookup_map,               # NEW LOOKUP FOR JS
#         "category_stats_chart": category_stats_chart
#     }


import frappe
from frappe.utils import flt, get_url, nowdate, add_days, get_fullname
from collections import defaultdict

@frappe.whitelist()
def get_agent_dashboard_data(from_date=None, to_date=None, custom_lead_category=None):
    current_user = frappe.session.user
    
    # --- 1. Default Date Logic ---
    if not from_date and not to_date:
        to_date = nowdate()
        from_date = add_days(to_date, -29)
    
    to_date_time = f"{to_date} 23:59:59" if to_date else None

    # --- 2. Define Base Filters ---
    
    # A. Cohort Filters (Creation Date) - Used for New Leads & The Chart
    cohort_filters = {
        "lead_owner": current_user,
        "creation": ["between", [from_date, to_date_time]]
    }
    
    if custom_lead_category:
        cohort_filters["custom_lead_category"] = custom_lead_category

    # B. Accounting Filters (Action Date) - Used for "Sales Closed" & "Lost" Summary Cards
    # We must start fresh or carefully copy to avoid overriding creation date
    accounting_base_filters = {"lead_owner": current_user}
    if custom_lead_category:
        accounting_base_filters["custom_lead_category"] = custom_lead_category

    # --- 3. Calculate Summary Card Stats (Accounting View) ---
    
    # Card 1: New Leads (Created in range)
    new_leads_count = frappe.db.count("Lead", filters=cohort_filters)
    
    # Card 2: Sales Closed (Actual Closing Date in range)
    closed_accounting_filters = accounting_base_filters.copy()
    closed_accounting_filters["custom_lead_status"] = "Closed"
    closed_accounting_filters["custom_sales_closed_date"] = ["between", [from_date, to_date_time]]
    closed_leads_count_card = frappe.db.count("Lead", filters=closed_accounting_filters)
    
    # Card 3: Lost Leads (Actual Lost Date in range)
    lost_accounting_filters = accounting_base_filters.copy()
    lost_accounting_filters["custom_lead_status"] = "Lead Lost"
    lost_accounting_filters["custom_lead_lost_date"] = ["between", [from_date, to_date_time]]
    lost_leads_count = frappe.db.count("Lead", filters=lost_accounting_filters)

    # Card 4: Total Sales Value (Joined logic, My Sales, Action Date)
    sales_params = {"owner": current_user, "from": from_date, "to": to_date_time}
    conditions = ["s.status='Approved'", "s.owner=%(owner)s", "s.creation >= %(from)s", "s.creation <= %(to)s"]
    join_clause = ""
    if custom_lead_category:
        join_clause = "INNER JOIN `tabLead` l ON s.lead = l.name"
        conditions.append("l.custom_lead_category = %(cat)s")
        sales_params["cat"] = custom_lead_category

    my_sales_val = frappe.db.sql(f"""
        SELECT SUM(s.unit_price) 
        FROM `tabSales Registration Form` s 
        {join_clause} 
        WHERE {' AND '.join(conditions)}
    """, sales_params)
    total_sales_value = flt(my_sales_val[0][0]) if my_sales_val else 0.0

    # --- 4. LEADERBOARD CHART (Cohort View) ---
    # Calculates performance based on Lead CREATION DATE
    
    lb_params = {"start": from_date, "end": to_date_time}
    lb_where = [
        "l.creation BETWEEN %(start)s AND %(end)s", 
        "l.lead_owner IS NOT NULL", 
        "l.lead_owner != ''"
    ]
    if custom_lead_category:
        lb_where.append("l.custom_lead_category = %(cat)s")
        lb_params["cat"] = custom_lead_category
    
    lb_sql = " AND ".join(lb_where)

    # Fetch Data
    leaderboard_data = frappe.db.sql(f"""
        SELECT 
            COALESCE(u.full_name, u.first_name, l.lead_owner) as agent_name,
            COUNT(l.name) as total_leads,
            SUM(CASE WHEN l.custom_lead_status='Closed' THEN 1 ELSE 0 END) as closed_sales
        FROM `tabLead` l
        LEFT JOIN `tabUser` u ON l.lead_owner = u.name
        WHERE {lb_sql}
        GROUP BY l.lead_owner
        ORDER BY closed_sales DESC, total_leads DESC
        LIMIT 10
    """, lb_params, as_dict=True)

    agent_performance_chart = {
        "labels": [r["agent_name"] for r in leaderboard_data],
        "datasets": [
            {"name": "Closed Sales", "values": [r["closed_sales"] for r in leaderboard_data]}
        ]
    }
    
    agent_lookup_map = {r["agent_name"]: r["total_leads"] for r in leaderboard_data}

    # --- 5. MY PERFORMANCE TEXT (The Fix) ---
    # We must calculate 'My Closed Sales' using the COHORT Logic (Creation Date)
    # so that it matches the visual Bar Chart height.
    
    my_perf_filters = cohort_filters.copy()
    my_perf_filters["custom_lead_status"] = "Closed"
    my_perf_closed_count_aligned_to_chart = frappe.db.count("Lead", filters=my_perf_filters)

    # User Profile Details
    my_full_name = get_fullname(current_user)
    u_det = frappe.db.get_value("User", current_user, "user_image", as_dict=True)
    
    my_info = {
        "name": my_full_name,
        "user_image": get_url(u_det.user_image) if u_det and u_det.user_image else None,
        "closed_sales": my_perf_closed_count_aligned_to_chart, # <-- Uses Chart Logic now
        "total_leads": new_leads_count
    }

    # --- 6. Category Stats (Strictly My Data, Ignore Cat Filter) ---
    cat_chart_filters = {
        "lead_owner": current_user,
        "creation": ["between", [from_date, to_date_time]]
    }
    cat_leads = frappe.db.get_all("Lead", filters=cat_chart_filters, fields=["custom_lead_category", "custom_lead_status"])
    cat_stats = defaultdict(lambda: {"total": 0, "closed": 0})

    for l in cat_leads:
        c = l.custom_lead_category or "Uncategorized"
        cat_stats[c]["total"] += 1
        if l.custom_lead_status == "Closed":
            cat_stats[c]["closed"] += 1
    
    sorted_cats = sorted(cat_stats.keys())
    
    category_stats_chart = {
        "labels": sorted_cats,
        "datasets": [
            {"name": "My Leads", "values": [cat_stats[c]["total"] for c in sorted_cats]},
            {"name": "My Sales", "values": [cat_stats[c]["closed"] for c in sorted_cats]}
        ]
    }

    return {
        "summary_stats": {
            "new_leads": new_leads_count,
            "closed_leads": closed_leads_count_card, # Accounting Logic for Top Card
            "lost_leads": lost_leads_count,
            "total_sales_value": total_sales_value
        },
        "current_agent_details": my_info,
        "agent_performance_chart": agent_performance_chart,
        "agent_lookup_map": agent_lookup_map,
        "category_stats_chart": category_stats_chart
    }