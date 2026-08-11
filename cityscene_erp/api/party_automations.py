import frappe
from cityscene_erp.api.account_manager import auto_create_party_account

def auto_create_ledger_for_party(doc, method):
    """
    Hook for after_insert on Customer and Supplier to automatically create a dedicated ledger.
    """
    party_type = doc.doctype
    party = doc.name
    
    # Get the default company. If not set, try to find one.
    company = frappe.defaults.get_user_default("Company")
    if not company:
        company = frappe.db.get_single_value("Global Defaults", "default_company")
        
    if not company:
        return
        
    parent_account = None
    
    if party_type == "Customer":
        # First try company default receivable account
        default_acc = frappe.db.get_value("Company", company, "default_receivable_account")
        if default_acc:
            is_group = frappe.db.get_value("Account", default_acc, "is_group")
            if is_group:
                parent_account = default_acc
            else:
                parent_account = frappe.db.get_value("Account", default_acc, "parent_account")
        # If not set or no valid parent found, try to find a root level Receivable group (like Debtors)
        if not parent_account:
            parent_account = frappe.db.get_value("Account", {"account_type": "Receivable", "is_group": 1, "company": company})
            
    elif party_type == "Supplier":
        # First try company default payable account
        default_acc = frappe.db.get_value("Company", company, "default_payable_account")
        if default_acc:
            is_group = frappe.db.get_value("Account", default_acc, "is_group")
            if is_group:
                parent_account = default_acc
            else:
                parent_account = frappe.db.get_value("Account", default_acc, "parent_account")
        # If not set or no valid parent found, try to find a root level Payable group (like Creditors)
        if not parent_account:
            parent_account = frappe.db.get_value("Account", {"account_type": "Payable", "is_group": 1, "company": company})
            
    if parent_account:
        try:
            auto_create_party_account(party_type, party, company, parent_account)
        except Exception as e:
            frappe.log_error(message=frappe.get_traceback(), title=f"Failed to auto-create ledger for {party}")

def ensure_supplier_role_for_portal_users(doc, method=None):
    """
    Hook for on_update on Supplier to ensure portal users get the 'Supplier' role.
    """
    if not hasattr(doc, "portal_users"):
        return
        
    for pu in doc.portal_users:
        if pu.user:
            try:
                user_doc = frappe.get_doc("User", pu.user)
                if "Supplier" not in [r.role for r in user_doc.roles]:
                    user_doc.add_roles("Supplier")
            except Exception as e:
                frappe.log_error(message=frappe.get_traceback(), title=f"Failed to add Supplier role to {pu.user}")

def ensure_supplier_role_for_contact(doc, method=None):
    """
    Hook for on_update on Contact to ensure users linked to a Supplier get the 'Supplier' role.
    """
    if not doc.user:
        return
    
    is_supplier = False
    for link in doc.links:
        if link.link_doctype == "Supplier":
            is_supplier = True
            break
            
    if is_supplier:
        try:
            user_doc = frappe.get_doc("User", doc.user)
            if "Supplier" not in [r.role for r in user_doc.roles]:
                user_doc.add_roles("Supplier")
        except Exception as e:
            pass

def check_partner_approval(doc, method=None):
    """
    Hook for on_update on Sales Partner to ensure users linked to an Approved Partner get the 'Channel Partner' role.
    """
    if getattr(doc, "custom_approval_status", None) == "Approved":
        contacts = frappe.db.get_all("Dynamic Link", 
            {"link_doctype": "Sales Partner", "link_name": doc.name, "parenttype": "Contact"},
            pluck="parent")
            
        for contact_name in contacts:
            user = frappe.db.get_value("Contact", contact_name, "user")
            if user and user != "Guest":
                try:
                    user_doc = frappe.get_doc("User", user)
                    if "Channel Partner" not in [r.role for r in user_doc.roles]:
                        user_doc.add_roles("Channel Partner")
                        
                        # Optionally, if you wanted to send an email upon approval, you could do it here
                        # frappe.sendmail(recipients=[user], subject="Partner Account Approved", message="Your Channel Partner account has been approved. You can now access the portal.")
                except Exception as e:
                    frappe.log_error(message=frappe.get_traceback(), title=f"Failed to add Channel Partner role to {user}")

