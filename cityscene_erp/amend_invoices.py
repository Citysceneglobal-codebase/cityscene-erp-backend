import frappe

def execute():
    invoices = frappe.get_all("Sales Invoice", filters={"customer": "Hinduja Renewables Energy Private Limited", "debit_to": "Debtors - SPPL", "docstatus": 1})
    
    for inv in invoices:
        doc = frappe.get_doc("Sales Invoice", inv.name)
        print(f"Cancelling {inv.name}...")
        doc.cancel()
        
        # Amend
        new_doc = frappe.copy_doc(doc)
        new_doc.docstatus = 0
        new_doc.amended_from = doc.name
        
        # We also need to set the correct naming series if it's auto, but let's see.
        
        # Fix debit_to
        new_doc.debit_to = "Hinduja Renewables Energy Private Limited - SPPL"
        
        # Save and submit
        new_doc.insert()
        new_doc.submit()
        print(f"Amended {inv.name} -> {new_doc.name} with correct debit_to account.")
        
    frappe.db.commit()
    print("Done amending mismatched invoices.")
