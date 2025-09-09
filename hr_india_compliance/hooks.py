from . import __version__ as app_version

app_name = "hr_india_compliance"
app_title = "Hr India Compliance"
app_publisher = "Dexciss Technology Pvt Ltd"
app_description = "Hr India Compliance"
app_email = "dexciss@gmail.com"
app_license = "Dexciss Technology Pvt Ltd"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/hr_india_compliance/css/hr_india_compliance.css"
# app_include_js = "/assets/hr_india_compliance/js/hr_india_compliance.js"

# include js, css files in header of web template
# web_include_css = "/assets/hr_india_compliance/css/hr_india_compliance.css"
# web_include_js = "/assets/hr_india_compliance/js/hr_india_compliance.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "hr_india_compliance/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
              "Salary Component":"public/js/custom_salary_component.js",
              "Branch" : "public/js/custom_plant.js",
              "Shift Type" : "public/js/custom_shift_type.js",
              "Salary Structure Assignment": "public/js/custom_salary_structure_assignment.js",
              "Staffing Plan" : "public/js/custom_staffing_plan.js",
              }
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
#	"methods": "hr_india_compliance.utils.jinja_methods",
#	"filters": "hr_india_compliance.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "hr_india_compliance.install.before_install"
# after_install = "hr_india_compliance.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "hr_india_compliance.uninstall.before_uninstall"
# after_uninstall = "hr_india_compliance.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "hr_india_compliance.utils.before_app_install"
# after_app_install = "hr_india_compliance.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "hr_india_compliance.utils.before_app_uninstall"
# after_app_uninstall = "hr_india_compliance.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "hr_india_compliance.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
#	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
#	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
#	"ToDo": "custom_app.overrides.CustomToDo"
# }
override_doctype_class = {
	'Leave Application': "hr_india_compliance.custom_leave_application.CustomLeaveApplication",
    'Payroll Entry': "hr_india_compliance.custom_payroll_entry.CustomPayrollEntry"
}

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Employee":{
        "before_save":"hr_india_compliance.employee.retierment_cal",
        "before_save":"hr_india_compliance.custom_employee.custom_before_save",
        "after_insert":"hr_india_compliance.custom_employee.create_leave_allocation"
	},
    "Salary Structure Assignment":{
        "validate":[
            "hr_india_compliance.salary_structure_assignment.update_salary_breakup",
        ],
	},
    "Salary Slip":{
        "before_cancel":"hr_india_compliance.hr_india_compliance.doctype.Custom_statistical_component_log.set_statistical_component_log_as_cancelled",
        "before_save":"hr_india_compliance.hr_india_compliance.custom_salary_slip.update_pf_checkbox",
        "before_submit":"hr_india_compliance.hr_india_compliance.doctype.Custom_statistical_component_log.before_submit"
    },
    "Leave Application":{
        "before_save":[
            "hr_india_compliance.hr_india_compliance.doctype.custom_leave_application.validate_leave_application"
        ],
    },
    "Attendance Request":{
        "on_submit":"hr_india_compliance.hr_india_compliance_utils.custom_attendance_request"
    },
    "Employee Checkin":{
        "validate":"hr_india_compliance.hr_india_compliance.custom_employee_checkin.validate",
        "before_insert":"hr_india_compliance.hr_india_compliance.custom_employee_checkin.before_insert"
        # "validate":"hr_india_compliance.hr_india_compliance_utils.update_on_validate",
        # "before_update_after_submit":"hr_india_compliance.hr_india_compliance_utils.update_on_validate",
    },
    "Staffing Plan":{
       "validate": "hr_india_compliance.custom_staffing_plan.validate"
    },
}


# Scheduled Tasks
scheduler_events = {
    "cron": {
        # "59 23 * * *": [
        #     "hr_india_compliance.hr_india_compliance.custom_shift_type.update_last_sync_of_checkin"
        # ],
        "0 3 * * *":[
            "hr_india_compliance.hr_india_compliance_utils.run_leave_allocation_method",
            # "hr_india_compliance.hr_india_compliance_utils.custom_leave_allocation_based_on_attendance"
            
        ]
    },
    "daily_long": [
            "hr_india_compliance.hr_india_compliance_utils.update_season_details",
            "hr_india_compliance.hr_india_compliance_utils.update_short_leave",
            # "hr_india_compliance.hr_india_compliance_utils._process_auto_attendance"
        ],
    "monthly":[
        "hr_india_compliance.hr_india_compliance.custom_shift_type.update_process_attendance_after"
    ]
}

# ---------------
# scheduler_events = {
    # "daily_long": [
	# 	"hr_india_compliance.custom_leave_allocation.custom_allocate_earned_leaves",
	# ],
#     "hourly": [
# 		"hr_india_compliance.custom_leave_allocation.stop_scheduled_job"
# 	],
# }
# bench_command = {
#     "migrate": "hr_india_compliance.custom_leave_allocation.stop_scheduled_job",
#     "update": "hr_india_compliance.custom_leave_allocation.stop_scheduled_job", 
# }
# scheduler_events = {
#	"all": [
#		"hr_india_compliance.tasks.all"
#	],
#	"daily": [
#		"hr_india_compliance.tasks.daily"
#	],
#	"hourly": [
#		"hr_india_compliance.tasks.hourly"
#	],
#	"weekly": [
#		"hr_india_compliance.tasks.weekly"
#	],
#	"monthly": [
#		"hr_india_compliance.tasks.monthly"
#	],
# }

# Testing
# -------

# before_tests = "hr_india_compliance.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
#	"frappe.desk.doctype.event.event.get_events": "hr_india_compliance.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
#	"Task": "hr_india_compliance.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["hr_india_compliance.utils.before_request"]
# after_request = ["hr_india_compliance.utils.after_request"]

# Job Events
# ----------
# before_job = ["hr_india_compliance.utils.before_job"]
# after_job = ["hr_india_compliance.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
#	{
#		"doctype": "{doctype_1}",
#		"filter_by": "{filter_by}",
#		"redact_fields": ["{field_1}", "{field_2}"],
#		"partial": 1,
#	},
#	{
#		"doctype": "{doctype_2}",
#		"filter_by": "{filter_by}",
#		"partial": 1,
#	},
#	{
#		"doctype": "{doctype_3}",
#		"strict": False,
#	},
#	{
#		"doctype": "{doctype_4}"
#	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
#	"hr_india_compliance.auth.validate"
# ]
# doctype_js = { 
# "Staffing Plan" : "public/js/staffing_plan.js",
#   }
# fixtures = [
#     "Staffing Plan",
# ]

fixtures = [
    {"dt": "Custom Field", "filters": {"module": "Hr India Compliance"}},
]

# fixtures = [{
#   'doctype': 'Custom Field',
#   'filters': {
#   'name': ['in', (
#       'Employee-custom_work_location',
#       "Branch-custom_hra_percentage",
#       "Branch-custom_production_incentive_based_on_",
#       'Branch-custom_pf_ceiling_limit',
#       "Branch-custom_welfare_fund_employee",
#       "Branch-custom_welfare_fund_employer",
#       "Branch-custom_hra_per",
#       "Branch-custom_tab_4",
#       "Branch-custom_allowances_and_deductions",
#       "Branch-custom_leave_combination",
#       "Branch-custom_lta_limit",
#       "Branch-custom_lta_allow_per",
#       "Branch-custom_bonus_limit",
#       "Branch-custom_section_break_ubiy3",
#       "Branch-custom_production_incentive_based_on",
#       "Branch-custom_pf_based_on",
#       "Branch-custom_section_break_eh3me",
#       "Branch-custom_professional_tax_applicable",
#       )]
#    }
# }]