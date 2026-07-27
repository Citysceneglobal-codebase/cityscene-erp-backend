import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

def execute():
    # 1. Unhide the built-in geolocation field
    make_property_setter("Employee Checkin", "geolocation", "hidden", 0, "Check")
    
    # 2. Add Custom Fields for the Selfie
    custom_fields = {
        "Employee Checkin": [
            {
                "fieldname": "custom_selfie",
                "label": "Selfie File",
                "fieldtype": "Attach Image",
                "insert_after": "geolocation",
                "hidden": 1 # Hide the attachment URL field
            },
            {
                "fieldname": "custom_selfie_preview",
                "label": "Selfie",
                "fieldtype": "Image",
                "options": "custom_selfie",
                "insert_after": "custom_selfie"
            }
        ]
    }
    
    create_custom_fields(custom_fields, update=True)
    frappe.db.commit()
    return "Custom fields added and geolocation unhidden!"
