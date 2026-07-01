import frappe

def run():
    frappe.init(site='srbpower.local')
    frappe.connect()

    company = 'SRB POWER INDIA PVT. LTD.'
    
    # Get all Bank ledger accounts
    accounts = frappe.get_all('Account', filters={
        'account_type': 'Bank',
        'is_group': 0,
        'company': company
    }, fields=['name', 'account_name'])

    for acc in accounts:
        # Check if a Bank Account is already linked to this ledger
        existing_bank_account = frappe.db.exists('Bank Account', {'account': acc.name, 'company': company})
        
        if not existing_bank_account:
            bank_name = acc.account_name
            # create Bank if it does not exist
            if not frappe.db.exists('Bank', bank_name):
                b = frappe.get_doc({
                    'doctype': 'Bank',
                    'bank_name': bank_name
                })
                b.flags.ignore_permissions = True
                b.insert()
            
            # create Bank Account
            ba = frappe.get_doc({
                'doctype': 'Bank Account',
                'bank': bank_name,
                'account': acc.name,
                'account_name': bank_name,
                'company': company,
                'is_company_account': 1,
                'is_default': 0
            })
            ba.flags.ignore_permissions = True
            ba.insert()
            print(f'Created and linked Bank Account for ledger: {acc.name}')
        else:
            print(f'Bank Account already exists for ledger: {acc.name}')

    frappe.db.commit()
    print('Done generating Bank Accounts from ledgers.')

if __name__ == '__main__':
    run()
