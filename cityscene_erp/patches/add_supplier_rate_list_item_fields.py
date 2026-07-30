import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def execute():
    custom_fields = {
        "Supplier Rate List Item": [
            {
                "fieldname": "description",
                "label": "Description",
                "fieldtype": "Small Text",
                "insert_after": "item_code"
            },
            {
                "fieldname": "attachment",
                "label": "Attachment",
                "fieldtype": "Attach",
                "insert_after": "description"
            }
        ]
    }
    
    create_custom_fields(custom_fields, ignore_validate=True)
    frappe.db.commit()
    print("Custom fields 'description' and 'attachment' added to 'Supplier Rate List Item'.")
