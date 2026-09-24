import frappe
import os

def execute():
    js_path = frappe.get_app_path("hrms", "hr", "web_form", "job_application", "job_application.js")
    if os.path.exists(js_path):
        with open(js_path, "r") as f:
            js_code = f.read()
    else:
        print("ERROR: JS file not found!")
        return

    frappe.db.set_value("Web Form", "job-application", "client_script", js_code)
    frappe.db.commit()
    print("Synced JS from filesystem to DB successfully!")

