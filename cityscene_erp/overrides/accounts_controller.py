import frappe
from erpnext.controllers.accounts_controller import get_missing_company_details as original_func

@frappe.whitelist()
def get_missing_company_details(doctype, docname):
    if not frappe.db.get_single_value("Print Settings", "custom_prompt_for_missing_company_details"):
        return False
    return original_func(doctype, docname)
