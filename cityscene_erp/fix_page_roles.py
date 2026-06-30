import frappe

def execute():
    for page_name in ['party-accounting', 'account-mapping']:
        doc = frappe.get_doc('Page', page_name)
        doc.set('roles', [])
        doc.append('roles', {'role': 'All'})
        doc.append('roles', {'role': 'System Manager'})
        doc.append('roles', {'role': 'Accounts Manager'})
        doc.save(ignore_permissions=True)
    frappe.db.commit()
