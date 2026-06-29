app_name = "wa_hr_api"
app_title = "WA HR API"
app_publisher = "PT Aluesa Global Digitek"
app_description = "API tambahan absensi dan cuti untuk integrasi WhatsApp"
app_email = "info@aluesagd.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "wa_hr_api",
# 		"logo": "/assets/wa_hr_api/logo.png",
# 		"title": "WA HR API",
# 		"route": "/wa_hr_api",
# 		"has_permission": "wa_hr_api.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/wa_hr_api/css/wa_hr_api.css"
# app_include_js = "/assets/wa_hr_api/js/wa_hr_api.js"

# include js, css files in header of web template
# web_include_css = "/assets/wa_hr_api/css/wa_hr_api.css"
# web_include_js = "/assets/wa_hr_api/js/wa_hr_api.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "wa_hr_api/public/scss/website"

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
# app_include_icons = "wa_hr_api/public/icons.svg"

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

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "wa_hr_api.utils.jinja_methods",
# 	"filters": "wa_hr_api.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "wa_hr_api.install.before_install"
# after_install = "wa_hr_api.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "wa_hr_api.uninstall.before_uninstall"
# after_uninstall = "wa_hr_api.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "wa_hr_api.utils.before_app_install"
# after_app_install = "wa_hr_api.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "wa_hr_api.utils.before_app_uninstall"
# after_app_uninstall = "wa_hr_api.utils.after_app_uninstall"

# Build
# ------------------
# To hook into the build process

# after_build = "wa_hr_api.build.after_build"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "wa_hr_api.notifications.get_notification_config"

fixtures = [
	{
		"doctype": "Custom Field",
		"filters": [["name", "like", "Job Applicant-%"]],
	},
	{
		"doctype": "Client Script",
		"filters": [["name", "=", "WA HR API - Job Applicant OCR"]],
	},
]

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Job Applicant": {
		"after_insert": "wa_hr_api.recruitment.auto_process_cv_with_ocr",
	}
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"wa_hr_api.tasks.all"
# 	],
# 	"daily": [
# 		"wa_hr_api.tasks.daily"
# 	],
# 	"hourly": [
# 		"wa_hr_api.tasks.hourly"
# 	],
# 	"weekly": [
# 		"wa_hr_api.tasks.weekly"
# 	],
# 	"monthly": [
# 		"wa_hr_api.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "wa_hr_api.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "wa_hr_api.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "wa_hr_api.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "wa_hr_api.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["wa_hr_api.utils.before_request"]
# after_request = ["wa_hr_api.utils.after_request"]

# Job Events
# ----------
# before_job = ["wa_hr_api.utils.before_job"]
# after_job = ["wa_hr_api.utils.after_job"]

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
# 	"wa_hr_api.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

