import frappe
from cityscene_erp.api.account_manager import auto_create_party_account
from cityscene_erp.api.party_automations import auto_create_ledger_for_party

def execute():
    """
    Run via: bench execute cityscene_erp.scripts.migrate_existing_parties.execute
    """
    frappe.flags.in_migrate = True
    
    customers = frappe.get_all("Customer")
    print(f"Found {len(customers)} customers. Processing...")
    for i, c in enumerate(customers):
        try:
            doc = frappe.get_doc("Customer", c.name)
            if not doc.get("accounts"):
                auto_create_ledger_for_party(doc, None)
                print(f"Created ledger for Customer: {doc.name}")
        except Exception as e:
            print(f"Error processing Customer {c.name}: {e}")
            
    suppliers = frappe.get_all("Supplier")
    print(f"Found {len(suppliers)} suppliers. Processing...")
    for i, s in enumerate(suppliers):
        try:
            doc = frappe.get_doc("Supplier", s.name)
            if not doc.get("accounts"):
                auto_create_ledger_for_party(doc, None)
                print(f"Created ledger for Supplier: {doc.name}")
        except Exception as e:
            print(f"Error processing Supplier {s.name}: {e}")
            
    print("Migration complete!")
