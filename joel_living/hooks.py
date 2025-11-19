app_name = "joel_living"
app_title = "Joel Living"
app_publisher = "Subburaj"
app_description = "joel_living"
app_email = "subburaj@skadits.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "joel_living",
# 		"logo": "/assets/joel_living/logo.png",
# 		"title": "Joel Living",
# 		"route": "/joel_living",
# 		"has_permission": "joel_living.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/joel_living/css/joel_living.css"
# app_include_js = "/assets/joel_living/js/joel_living.js"

app_include_js = [
    "/assets/joel_living/js/toggle.js",
    "/assets/joel_living/js/workflow.js"
]
# app_include_css = "/assets/joel_living/css/style.css"


# include js, css files in header of web template
# web_include_css = "/assets/joel_living/css/joel_living.css"
# web_include_js = "/assets/joel_living/js/joel_living.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "joel_living/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "joel_living/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "joel_living.utils.jinja_methods",
# 	"filters": "joel_living.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "joel_living.install.before_install"
# after_install = "joel_living.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "joel_living.uninstall.before_uninstall"
# after_uninstall = "joel_living.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "joel_living.utils.before_app_install"
# after_app_install = "joel_living.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "joel_living.utils.before_app_uninstall"
# after_app_uninstall = "joel_living.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "joel_living.notifications.get_notification_config"

# Permissions
# -----------
permission_query_conditions = {
    "Lead": "joel_living.lead_permission.get_sales_agent_lead_conditions",
        "Admin Message Inbox": "joel_living.joel_living.doctype.admin_message.admin_message.system_inbox_permission"
}

has_permission = {
    "Lead": "joel_living.lead_permission.has_sales_agent_lead_permission",
}

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Lead": {
        "before_save": "joel_living.lead_permission.on_lead_assignment_change",
        "after_insert": "joel_living.lead_permission.after_insert_lead_assignment"
   
    },
    "Sales Registration Form": {
        "after_save": "joel_living.custom_lead.log_ip_address_and_changes"
    },
    "Version": {
        "before_save": "joel_living.custom_lead.set_version_ip_address"
    }
}

# Scheduled Tasks
# ---------------

scheduler_events = {

    "daily": [
        # This job finds ALL overdue leads and starts the process.
        "joel_living.lead_permission.unassign_overdue_leads",

        # This NEW job finds ONLY re-approved leads that have expired their 3-day deadline.
        "joel_living.lead_permission.dispatch_expired_reapproved_leads" 
    ],
    "cron": {
        "*/15 * * * *": [
            "joel_living.lead_permission.unassign_expired_open_leads" # every 15 minutes
        ],
         # Run every 5 minutes (check for 2-hour sessions and midnight logout)
        "*/5 * * * *": [
            "joel_living.custom_lead_changes.auto_logout_inactive_users"
        ],
        # Run again exactly at midnight Dubai time for safety
        "0 0 * * *": [
            "joel_living.custom_lead_changes.auto_logout_inactive_users"
        ]
    }
	# "all": [
	# 	"joel_living.tasks.all"
	# ],
	# "daily": [
	# 	"joel_living.tasks.daily"
	# ],
	# "hourly": [
	# 	"joel_living.tasks.hourly"
	# ],
	# "weekly": [
	# 	"joel_living.tasks.weekly"
	# ],
	# "monthly": [
	# 	"joel_living.tasks.monthly"
	# ],
}

# Testing
# -------

# before_tests = "joel_living.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "joel_living.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "joel_living.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["joel_living.utils.before_request"]
# after_request = ["joel_living.utils.after_request"]

# Job Events
# ----------
# before_job = ["joel_living.utils.before_job"]
# after_job = ["joel_living.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"joel_living.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

