from frappe.www.portal import get_context as frappe_get_context
import frappe

def get_context(context, **dict_params):
    # Call the original frappe portal context logic
    context = frappe_get_context(context, **dict_params)
    
    # Add our custom context flags
    roles = frappe.get_roles(frappe.session.user)
    context.is_supplier = "Supplier" in roles
    
    if context.is_supplier:
        contact = frappe.db.get_value("Contact", {"user": frappe.session.user})
        if contact:
            supplier = frappe.db.get_value("Dynamic Link", {
                "parent": contact,
                "parenttype": "Contact",
                "link_doctype": "Supplier"
            }, "link_name")
            context.supplier_name = supplier or frappe.utils.get_fullname(frappe.session.user)
        else:
            context.supplier_name = frappe.utils.get_fullname(frappe.session.user)
    
    return context
