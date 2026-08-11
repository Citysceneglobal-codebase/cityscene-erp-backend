from frappe.www.me import get_context as frappe_get_context
import frappe

def get_context(context):
    frappe_get_context(context)
    
    # Check for pending partner status
    context.is_pending_partner = False
    roles = frappe.get_roles(frappe.session.user)
    if "Channel Partner" not in roles and "Supplier" not in roles:
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
