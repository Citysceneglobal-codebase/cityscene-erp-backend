import frappe
from cityscene_erp.api.party_automations import auto_create_ledger_for_party

def run():
    frappe.init(site='srbpower.local')
    frappe.connect()

    company = 'SRB POWER INDIA PVT. LTD.'
    
    customers = frappe.get_all('Customer')
    for c in customers:
        doc = frappe.get_doc('Customer', c.name)
        if not any(a.company == company for a in doc.get('accounts')):
            print(f'Missing for Customer: {doc.name}')
            auto_create_ledger_for_party(doc, None)
            
    suppliers = frappe.get_all('Supplier')
    for s in suppliers:
        doc = frappe.get_doc('Supplier', s.name)
        if not any(a.company == company for a in doc.get('accounts')):
            print(f'Missing for Supplier: {doc.name}')
            auto_create_ledger_for_party(doc, None)
            
    frappe.db.commit()
    print('Finished checking all parties.')

if __name__ == '__main__':
    run()
