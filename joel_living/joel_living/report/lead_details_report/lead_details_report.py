import frappe
from frappe import _

def execute(filters=None):
    """Main execution function called by Frappe to generate the report."""
    columns = get_columns()
    data = get_data(filters)
    # Generate the header HTML, including the tabs and role-based buttons
    html_card = generate_html_card() 
    
    # We return three values: columns, data, and the HTML to be displayed above the report
    return columns, data, html_card

def get_columns():
    """Defines the columns visible in the report's data table."""
 
    return [
        # REVISED: Change the label of the 'Select' column to include the Master Checkbox HTML
{"label": _("Select"), "fieldname": "select", "fieldtype": "Data", "width": 50}, 
        {"label": _("Lead Name"), "fieldname": "name", "fieldtype": "Link", "options": "Lead", "width": 200},
        {"label": _("Lead Category"), "fieldname": "custom_lead_category", "fieldtype": "Data", "width": 120},
        {"label": _("Lead Owner"), "fieldname": "lead_owner", "fieldtype": "Link", "options": "User", "width": 150},
        {"label": _("Status"), "fieldname": "custom_lead_status", "fieldtype": "Data", "width": 120},
        {"label": _("Hide Status"), "fieldname": "custom_hide_status", "fieldtype": "Data", "width": 120},
    ]

def get_data(filters):
    """Securely fetches all lead data needed for both display and the button logic in JavaScript."""
    fields_to_fetch = [
        "name", "custom_project", "custom_lead_category", "job_title", "lead_owner",
        "custom_budget_range", "custom_lead_status", "custom_main_lead_source",
        "custom_priority_", "mobile_no", "company_name",
        "custom_hide_status"
    ]
    
    orm_filters = {}
    
    # Apply Lead Owner Filter
    if filters.get("show_unassigned"):
        orm_filters['lead_owner'] = ["is", "not set"]
    else:
        if filters.get("lead_owner"):
            orm_filters['lead_owner'] = filters.get("lead_owner")
        if not filters.get("show_unassigned") and not filters.get("lead_owner"):
            orm_filters['lead_owner'] = ["is", "set"]

    # Apply Lead Category Filter (Set by custom tabs)
    if filters.get("custom_lead_category"):
        orm_filters['custom_lead_category'] = filters.get("custom_lead_category")

    return frappe.get_list("Lead", filters=orm_filters, fields=fields_to_fetch, order_by="creation desc")

def generate_html_card():
    """Generates the complete HTML for the tabs and action buttons based on the user's roles."""
    user_roles = frappe.get_roles()
    unrestricted_roles = ["System Manager", "Admin", "Super Admin", "Administrator", "Sales Manager"]
    is_unrestricted_user = any(role in user_roles for role in unrestricted_roles)
    is_sales_agent = 'Sales Agent' in user_roles and not is_unrestricted_user

    # Build the HTML for the filter tabs
    tab_items = ["All", "Fresh Lead", "Reshuffled Lead", "Lucky Lead", "Data Lead"]
    tabs_html = "".join([f'<a class="nav-link custom-report-tab" href="#" data-value="{item}">{item}</a>' for item in tab_items])

    # Build the HTML for the action buttons based on roles
    buttons_html = ""
    if is_sales_agent:
        buttons_html += '<button id="report-btn-request-hide" class="btn btn-sm btn-secondary">Request Hide</button>'
    
    if is_unrestricted_user:
        buttons_html += '<button id="report-btn-assign-lead" class="btn btn-sm btn-primary">Assign Lead</button>'
        buttons_html += '<button id="report-btn-approve-hide" class="btn btn-sm btn-success" style="margin-left:5px;">Approve Hide</button>'
        buttons_html += '<button id="report-btn-reject-hide" class="btn btn-sm btn-danger" style="margin-left:5px;">Reject Hide</button>'
        
    # FIX: Use inline onclick to call a window function for guaranteed execution.
    buttons_html += '<button id="report-btn-export" class="btn btn-sm btn-default" style="margin-left:5px;" onclick="handle_report_export()">Export to Excel</button>'

    # Combine everything into the final HTML structure
    html_card = f"""
        <div class="frappe-card" style="margin-bottom: 10px;">
            <div class="report-tabs-container">{tabs_html}</div>
        </div>
        <div id="report-custom-buttons" class="btn-group" style="margin-bottom: 10px;">{buttons_html}</div>
        <style>
            .report-tabs-container {{ background:#f2f2f2; border:1px solid #ddd; border-radius:6px; overflow-x:auto; display:flex; justify-content:center; }}
            .report-tabs-container > div {{ display:flex; }}
            .report-tabs-container .nav-link {{ flex-shrink:0; text-align:center; padding:6px 12px; border-right:1px solid #ddd; color:#000; font-weight:500;}}
            .report-tabs-container .nav-link:last-child {{ border-right:none; }}
            .report-tabs-container .nav-link.active {{ background-color:#000; color:#fff; }}
        </style>
    """
    return html_card