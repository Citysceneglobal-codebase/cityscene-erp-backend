import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_field

def run():
    create_custom_field("Print Settings", {
        "fieldname": "custom_prompt_for_missing_company_details",
        "label": "Prompt for Missing Company Details",
        "fieldtype": "Check",
        "insert_after": "send_print_as_pdf",
        "default": "0",
        "description": "If enabled, prompts users to fill out missing Company details when printing."
    })
    frappe.db.commit()
    print("Done")
