import frappe
from frappe import _

@frappe.whitelist()
def auto_create_party_account(party_type: str, party: str, company: str, parent_account: str):
    """
    Creates a dedicated CoA account for a party and links it in the accounts child table.
    """
    if not frappe.has_permission(party_type, "write"):
        frappe.throw(_("Not permitted to update {0}").format(party_type))
        
    abbr = frappe.db.get_value("Company", company, "abbr")
    if not abbr:
        frappe.throw(_("Company abbreviation not found"))
        
    account_name = f"{party} - {abbr}"
    
    # Check if account already exists
    existing_account = frappe.db.get_value("Account", {"name": account_name, "company": company})
    
    if not existing_account:
        # Determine account type based on party type
        account_type = "Receivable" if party_type == "Customer" else "Payable"
        
        # Create Account
        account = frappe.get_doc({
            "doctype": "Account",
            "account_name": party,
            "parent_account": parent_account,
            "company": company,
            "is_group": 0,
            "account_type": account_type,
            # Let ERPNext handle currency, etc.
        })
        account.flags.ignore_permissions = True
        account.insert()
        existing_account = account.name
        
    # Link to party
    party_doc = frappe.get_doc(party_type, party)
    
    # Check if already linked
    exists = False
    for row in party_doc.get("accounts", []):
        if row.company == company:
            if row.account == existing_account:
                exists = True
            else:
                row.account = existing_account
                exists = True
            break
            
    if not exists:
        party_doc.append("accounts", {
            "company": company,
            "account": existing_account
        })
        
    party_doc.flags.ignore_permissions = True
    party_doc.flags.ignore_mandatory = True
    party_doc.flags.ignore_links = True
    party_doc.save(ignore_permissions=True)
    
    return existing_account
