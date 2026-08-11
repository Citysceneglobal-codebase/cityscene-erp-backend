from frappe.www.portal import get_context as frappe_get_context
import frappe

def get_context(context, **dict_params):
    # Call the original frappe portal context logic
    context = frappe_get_context(context, **dict_params)
    
    # Add our custom context flags
    roles = frappe.get_roles(frappe.session.user)
    context.is_supplier = "Supplier" in roles
    context.is_partner = "Channel Partner" in roles
    
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
            
    if context.is_partner:
        contact = frappe.db.get_value("Contact", {"user": frappe.session.user})
        if contact:
            partner = frappe.db.get_value("Dynamic Link", {
                "parent": contact,
                "parenttype": "Contact",
                "link_doctype": "Sales Partner"
            }, "link_name")
            context.partner_name = partner or frappe.utils.get_fullname(frappe.session.user)
        else:
            context.partner_name = frappe.utils.get_fullname(frappe.session.user)
            
    # Check for pending partner status
    context.is_pending_partner = False
    if not context.is_partner and not context.is_supplier:
        contacts = frappe.db.get_all("Contact", {"user": frappe.session.user}, pluck="name")
        if contacts:
            partners = frappe.db.get_all("Dynamic Link", {
                "parent": ("in", contacts),
                "parenttype": "Contact",
                "link_doctype": "Sales Partner"
            }, pluck="link_name")
            for partner in partners:
                status = frappe.db.get_value("Sales Partner", partner, "custom_approval_status")
                if status == "Pending Confirmation":
                    context.is_pending_partner = True
                    break
    
    return context
