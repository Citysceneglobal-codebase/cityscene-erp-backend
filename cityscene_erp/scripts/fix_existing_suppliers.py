import frappe
from cityscene_erp.api.party_automations import (
    auto_create_ledger_for_party,
    ensure_supplier_role_for_portal_users,
    ensure_supplier_role_for_contact
)

def execute():
    # 1. Fix Suppliers (Ledgers and Portal Users)
    suppliers = frappe.get_all("Supplier", pluck="name")
    print(f"Checking {len(suppliers)} Suppliers...")
    
    for supp_name in suppliers:
        doc = frappe.get_doc("Supplier", supp_name)
        
        # Ensure Ledgers
        try:
            auto_create_ledger_for_party(doc, None)
        except Exception as e:
            print(f"Failed ledger creation for {supp_name}: {e}")
        
        # Ensure Portal Users Roles
        ensure_supplier_role_for_portal_users(doc, None)
        
    # 2. Fix Contacts (Supplier Roles)
    contacts = frappe.get_all("Contact", pluck="name")
    print(f"Checking {len(contacts)} Contacts...")
    
    for contact_name in contacts:
        doc = frappe.get_doc("Contact", contact_name)
        ensure_supplier_role_for_contact(doc, None)
        
    frappe.db.commit()
    print("Finished fixing existing suppliers and contacts!")
