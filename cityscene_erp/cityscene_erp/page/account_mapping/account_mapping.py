import frappe

@frappe.whitelist()
def get_mapping_data(party_type: str, company: str, status: str = "All"):
    # Get all parties of the given type
    parties = frappe.get_all(party_type, fields=["name", "customer_group" if party_type=="Customer" else "supplier_group"])
    
    # Get accounts child table data for the company
    linked_accounts = frappe.get_all("Party Account", 
        filters={"parenttype": party_type, "company": company},
        fields=["parent", "account"]
    )
    
    # Map them for easy lookup
    account_map = {row.parent: row.account for row in linked_accounts}
    
    data = []
    for p in parties:
        account = account_map.get(p.name)
        is_mapped = 1 if account else 0
        
        if status == "Mapped" and not is_mapped: continue
        if status == "Unmapped" and is_mapped: continue
            
        data.append({
            "party": p.name,
            "group": p.customer_group if party_type=="Customer" else p.supplier_group,
            "account": account,
            "status": "Mapped" if is_mapped else "Not Mapped"
        })
        
    return data
