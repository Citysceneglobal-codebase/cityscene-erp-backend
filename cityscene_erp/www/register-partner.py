import frappe

no_cache = 1

def get_context(context):
    if frappe.session.user != "Guest":
        frappe.local.flags.redirect_location = "/partner-dashboard"
        raise frappe.Redirect
    
    context.title = "Channel Partner Registration"
    context.parents = [{"name": "Home", "route": "/"}]
