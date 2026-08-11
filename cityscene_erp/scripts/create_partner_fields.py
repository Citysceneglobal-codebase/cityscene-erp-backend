import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def execute():
    custom_fields = {
        "Sales Partner": [
            {
                "fieldname": "custom_approval_status",
                "label": "Approval Status",
                "fieldtype": "Select",
                "options": "Pending Confirmation\nApproved\nRejected",
                "default": "Pending Confirmation",
                "insert_after": "partner_name"
            }
        ],
        "Lead": [
            {
                "fieldname": "custom_channel_partner",
                "label": "Channel Partner",
                "fieldtype": "Link",
                "options": "Sales Partner",
                "insert_after": "lead_owner"
            }
        ]
    }
    create_custom_fields(custom_fields)
    frappe.db.commit()
    print("Custom fields created successfully.")
