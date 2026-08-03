import frappe

no_cache = 1

def get_context(context):
    if frappe.session.user != "Guest":
        frappe.local.flags.redirect_location = "/portal"
        raise frappe.Redirect
    
    context.title = "Supplier Registration"
    context.parents = [{"name": "Home", "route": "/"}]
