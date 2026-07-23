import frappe
from frappe import _
import csv
import io

def get_supplier():
    user = frappe.session.user
    if user == "Guest":
        return None
    
    # Find contact linked to user
    contact = frappe.db.get_value("Contact", {"user": user})
    if not contact:
        return None
        
    # Find supplier linked to contact
    supplier = frappe.db.get_value("Dynamic Link", {
        "parent": contact,
        "parenttype": "Contact",
        "link_doctype": "Supplier"
    }, "link_name")
    
    return supplier

@frappe.whitelist()
def get_dashboard_stats():
    supplier = get_supplier()
    if not supplier:
        return {"active_pos": 0, "pending_invoices": 0, "rate_lists": 0}
        
    active_pos = frappe.db.count("Purchase Order", filters={
        "supplier": supplier,
        "status": ["in", ["Draft", "Submitted", "To Receive and Bill", "To Receive", "To Bill"]]
    })
    
    pending_invoices = frappe.db.count("Purchase Invoice", filters={
        "supplier": supplier,
        "status": ["in", ["Draft", "Unpaid", "Partly Paid"]]
    })
    
    rate_lists = frappe.db.count("Supplier Rate List", filters={
        "supplier": supplier,
        "docstatus": 1
    })
    
    return {
        "active_pos": active_pos,
        "pending_invoices": pending_invoices,
        "rate_lists": rate_lists
    }

@frappe.whitelist()
def upload_rate_list(valid_from: str, valid_upto: str = None):
    supplier = get_supplier()
    if not supplier:
        frappe.throw(_("Could not identify the Supplier for the logged-in user."))

    if 'file' not in frappe.request.files:
        frappe.throw(_("Please attach a CSV file."))

    file = frappe.request.files['file']
    file_content = file.stream.read().decode("utf-8")
    
    if not file_content:
        frappe.throw(_("File is empty."))

    csv_reader = csv.DictReader(io.StringIO(file_content))
    
    # Create the Supplier Rate List document
    doc = frappe.new_doc("Supplier Rate List")
    doc.supplier = supplier
    doc.valid_from = valid_from
    if valid_upto:
        doc.valid_upto = valid_upto
        
    items_added = 0
    
    for row in csv_reader:
        item_code = row.get("item_code") or row.get("Item Code")
        rate = row.get("rate") or row.get("Rate")
        
        if not item_code or not rate:
            continue
            
        if not frappe.db.exists("Item", item_code):
            continue
            
        try:
            rate_val = float(rate)
        except ValueError:
            continue
            
        doc.append("items", {
            "item_code": item_code,
            "rate": rate_val
        })
        items_added += 1

    if items_added == 0:
        frappe.throw(_("No valid items found in the CSV. Make sure item codes are valid and the header is 'item_code' and 'rate'."))

    doc.insert(ignore_permissions=True)
    doc.submit()
    
    return {"status": "success", "docname": doc.name}

@frappe.whitelist()
def download_template():
    csv_data = "item_code,rate\n"
    frappe.response['result'] = csv_data
    frappe.response['type'] = 'csv'
    frappe.response['doctype'] = "Supplier Rate List Template"
    frappe.response['filename'] = "supplier_rate_list_template.csv"

@frappe.whitelist()
def get_all_items(search_term: str = ""):
    filters = {}
    if search_term:
        filters["item_code"] = ["like", f"%{search_term}%"]
    
    items = frappe.get_all("Item", filters=filters, fields=["item_code", "item_name"], limit=50, ignore_permissions=True)
    return items

@frappe.whitelist()
def create_manual_rate_list(valid_from: str, items: str, valid_upto: str = None):
    supplier = get_supplier()
    if not supplier:
        frappe.throw(_("Could not identify the Supplier."))
        
    import json
    if isinstance(items, str):
        items = json.loads(items)
        
    if not items:
        frappe.throw(_("No items provided."))
        
    doc = frappe.new_doc("Supplier Rate List")
    doc.supplier = supplier
    doc.valid_from = valid_from
    if valid_upto:
        doc.valid_upto = valid_upto
        
    for item in items:
        doc.append("items", {
            "item_code": item.get("item_code"),
            "rate": float(item.get("rate") or 0)
        })
        
    doc.insert(ignore_permissions=True)
    doc.submit()
    return {"status": "success", "docname": doc.name}

@frappe.whitelist()
def get_active_supplier_rates(items: str):
    supplier = get_supplier()
    if not supplier:
        return {}
        
    import json
    if isinstance(items, str):
        items = json.loads(items)
        
    from frappe.utils import today
    current_date = today()
    
    rates = {}
    
    # We want to find the latest valid Rate List for this supplier
    rate_lists = frappe.get_all("Supplier Rate List", 
        filters={
            "supplier": supplier,
            "valid_from": ["<=", current_date],
            "docstatus": 1
        },
        or_filters=[
            ["Supplier Rate List", "valid_upto", ">=", current_date],
            ["Supplier Rate List", "valid_upto", "is", "not set"]
        ],
        order_by="creation desc",
        pluck="name",
        ignore_permissions=True
    )
    
    if not rate_lists:
        return {}
        
    # Pick the most recently created valid rate list
    latest_rate_list = frappe.get_doc("Supplier Rate List", rate_lists[0])
    
    for row in latest_rate_list.items:
        if row.item_code in items:
            rates[row.item_code] = row.rate
            
    return rates

@frappe.whitelist()
def get_rate_lists_details():
    supplier = get_supplier()
    if not supplier:
        return []
    
    rate_lists = frappe.get_all("Supplier Rate List", 
        filters={"supplier": supplier, "docstatus": 1},
        fields=["name", "valid_from", "valid_upto"],
        order_by="creation desc",
        ignore_permissions=True
    )
    
    for rl in rate_lists:
        items = frappe.get_all("Supplier Rate List Item",
            filters={"parent": rl.name},
            fields=["item_code", "rate"],
            ignore_permissions=True
        )
        
        # get item names
        for item in items:
            item_name = frappe.db.get_value("Item", item.item_code, "item_name")
            item["item_name"] = item_name or ""
            
        rl["items"] = items
        
    return rate_lists

@frappe.whitelist()
def submit_proactive_quotation(items):
    import json
    from frappe.utils import today
    
    user = frappe.session.user
    supplier = frappe.db.get_value("Portal User", {"user": user}, "parent")
    
    if not supplier:
        frappe.throw("You are not associated with any supplier profile.")
        
    items = json.loads(items)
    if not items:
        frappe.throw("Quotation must have at least one item.")
        
    company = frappe.defaults.get_user_default("Company")
    if not company:
        companies = frappe.get_all("Company", limit=1)
        if companies:
            company = companies[0].name
        else:
            frappe.throw("Default company not found in system.")
            
    doc = frappe.get_doc({
        "doctype": "Supplier Quotation",
        "supplier": supplier,
        "company": company,
        "transaction_date": today(),
        "items": items
    })
    
    doc.insert(ignore_permissions=True)
    doc.submit()
    
    return doc.name
