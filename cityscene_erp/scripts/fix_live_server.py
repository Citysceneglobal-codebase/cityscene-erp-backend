import frappe

def run():
    frappe.init(site='srbpower.local')
    frappe.connect()

    # 1. Fix Workspace Shortcut
    ws = frappe.get_doc('Workspace', 'Invoicing')
    exists = any(i.label == 'Party Accounting' for i in ws.shortcuts)
    if not exists:
        ws.append('shortcuts', {
            'type': 'Page',
            'label': 'Party Accounting',
            'link_to': 'party-accounting',
            'color': 'Grey'
        })
        ws.flags.ignore_permissions = True
        ws.save(ignore_permissions=True)
        print('Added Party Accounting to Invoicing Workspace shortcuts.')
    else:
        print('Party Accounting already in Invoicing shortcuts.')

    # 2. Fix Bank Accounts
    company = 'SRB POWER INDIA PVT. LTD.'
    parent_bank_account = frappe.db.get_value('Account', {'account_type': 'Bank', 'is_group': 1, 'company': company})
    
    bank_accounts = frappe.get_all('Bank Account', filters={'company': company}, fields=['name', 'bank', 'account'])
    for ba in bank_accounts:
        doc = frappe.get_doc('Bank Account', ba.name)
        
        # Ensure it is a company account
        doc.is_company_account = 1
        
        # Create Ledger Account if missing
        if not doc.account:
            acc_name = f"{ba.name} - SPIPL"
            existing = frappe.db.exists('Account', acc_name)
            if not existing:
                if parent_bank_account:
                    acc = frappe.get_doc({
                        'doctype': 'Account',
                        'account_name': ba.name,
                        'parent_account': parent_bank_account,
                        'company': company,
                        'is_group': 0,
                        'account_type': 'Bank'
                    })
                    acc.flags.ignore_permissions = True
                    acc.insert(ignore_permissions=True)
                    print(f'Created ledger account: {acc.name}')
                    doc.account = acc.name
                else:
                    print('Error: Could not find Bank parent account.')
            else:
                doc.account = existing

        doc.flags.ignore_permissions = True
        doc.save(ignore_permissions=True)
        print(f'Fixed Bank Account: {ba.name}')

    frappe.db.commit()
    print('Done.')

if __name__ == '__main__':
    run()
