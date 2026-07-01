import frappe

def run():
    frappe.init(site='cityscene-srb-erp')
    frappe.connect()

    if not frappe.db.exists('DocType', 'Scope of Work Item'):
        doc = frappe.get_doc({
            'doctype': 'DocType',
            'name': 'Scope of Work Item',
            'module': 'Selling',
            'custom': 1,
            'istable': 1,
            'fields': [
                {
                    'fieldname': 'task_description',
                    'fieldtype': 'Data',
                    'label': 'Task Description'
                },
                {
                    'fieldname': 'srbpl_scope',
                    'fieldtype': 'Check',
                    'label': 'SRBPL Scope'
                }
            ]
        })
        doc.flags.ignore_permissions = True
        doc.insert(ignore_permissions=True)
        print('Created Scope of Work Item doctype locally.')
    else:
        print('Scope of Work Item already exists.')
    
    frappe.db.commit()

if __name__ == '__main__':
    run()
