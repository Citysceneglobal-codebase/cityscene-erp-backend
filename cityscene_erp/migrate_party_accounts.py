import frappe

def execute():
    companies = frappe.get_all("Company", pluck="name")
    
    # 1. Migrate Customers
    customers = frappe.get_all("Customer")
    customer_updates = 0
    
    for c in customers:
        customer = frappe.get_doc("Customer", c.name)
        updated = False
        
        for company in companies:
            abbr = frappe.db.get_value("Company", company, "abbr")
            if not abbr: continue
                
            expected_account_name = f"{customer.name} - {abbr}"
            
            account = frappe.db.get_value("Account", 
                {"name": expected_account_name, "company": company, "account_type": "Receivable", "is_group": 0},
                "name"
            )
            
            if account:
                exists = False
                for row in customer.get("accounts", []):
                    if row.company == company and row.account == account:
                        exists = True
                        break
                
                if not exists:
                    # Remove any existing row for this company that has a blank account or wrong account
                    customer.set("accounts", [row for row in customer.get("accounts", []) if row.company != company])
                    
                    customer.append("accounts", {
                        "company": company,
                        "account": account
                    })
                    updated = True
                
        if updated:
            customer.flags.ignore_permissions = True
            customer.flags.ignore_mandatory = True
            customer.flags.ignore_links = True
            customer.save(ignore_permissions=True)
            customer_updates += 1

    # 2. Migrate Suppliers
    suppliers = frappe.get_all("Supplier")
    supplier_updates = 0
    
    for s in suppliers:
        supplier = frappe.get_doc("Supplier", s.name)
        updated = False
        
        for company in companies:
            abbr = frappe.db.get_value("Company", company, "abbr")
            if not abbr: continue
                
            expected_account_name = f"{supplier.name} - {abbr}"
            
            account = frappe.db.get_value("Account", 
                {"name": expected_account_name, "company": company, "account_type": "Payable", "is_group": 0},
                "name"
            )
            
            if account:
                exists = False
                for row in supplier.get("accounts", []):
                    if row.company == company and row.account == account:
                        exists = True
                        break
                
                if not exists:
                    supplier.set("accounts", [row for row in supplier.get("accounts", []) if row.company != company])
                    
                    supplier.append("accounts", {
                        "company": company,
                        "account": account
                    })
                    updated = True
                
        if updated:
            supplier.flags.ignore_permissions = True
            supplier.flags.ignore_mandatory = True
            supplier.flags.ignore_links = True
            supplier.save(ignore_permissions=True)
            supplier_updates += 1
            
    frappe.db.commit()
    print(f"Migration Complete!")
    print(f"Customers updated: {customer_updates}")
    print(f"Suppliers updated: {supplier_updates}")
