import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_field

def run():
    # 1. Make standard rounding_adjustment editable
    if not frappe.db.exists("Property Setter", "Sales Invoice-rounding_adjustment-read_only"):
        frappe.get_doc({
            "doctype": "Property Setter",
            "doc_type": "Sales Invoice",
            "field_name": "rounding_adjustment",
            "property": "read_only",
            "value": "0",
            "property_type": "Check",
            "doctype_or_field": "DocField"
        }).insert(ignore_permissions=True)

    # 2. Add checkbox "Disable Auto Rounding"
    create_custom_field("Sales Invoice", {
        "fieldname": "custom_disable_auto_rounding",
        "label": "Disable Auto Rounding",
        "fieldtype": "Check",
        "insert_after": "disable_rounded_total",
        "default": "0"
    })

    # 3. Add custom manual rounding amount field
    create_custom_field("Sales Invoice", {
        "fieldname": "custom_manual_rounding_amount",
        "label": "Manual Rounding Amount",
        "fieldtype": "Currency",
        "insert_after": "custom_disable_auto_rounding",
        "depends_on": "eval:doc.custom_disable_auto_rounding==1"
    })

    # 4. Add Server Script to override backend math
    if not frappe.db.exists("Server Script", "Override Sales Invoice Rounding"):
        script = """
if doc.custom_disable_auto_rounding:
    from frappe.utils import flt
    doc.rounding_adjustment = flt(doc.custom_manual_rounding_amount)
    doc.rounded_total = doc.grand_total + doc.rounding_adjustment
    doc.base_rounding_adjustment = flt(doc.rounding_adjustment * doc.conversion_rate)
    doc.base_rounded_total = flt(doc.rounded_total * doc.conversion_rate)
"""
        frappe.get_doc({
            "doctype": "Server Script",
            "name": "Override Sales Invoice Rounding",
            "dt": "Sales Invoice",
            "script_type": "DocType Event",
            "doctype_event": "Before Save",
            "script": script,
            "disabled": 0
        }).insert(ignore_permissions=True)
    else:
        # Update existing script
        ss = frappe.get_doc("Server Script", "Override Sales Invoice Rounding")
        ss.script = """
if doc.custom_disable_auto_rounding:
    from frappe.utils import flt
    doc.rounding_adjustment = flt(doc.custom_manual_rounding_amount)
    doc.rounded_total = doc.grand_total + doc.rounding_adjustment
    doc.base_rounding_adjustment = flt(doc.rounding_adjustment * doc.conversion_rate)
    doc.base_rounded_total = flt(doc.rounded_total * doc.conversion_rate)
"""
        ss.save(ignore_permissions=True)

    frappe.db.commit()
    print("Manual Rounding Setup Complete")
