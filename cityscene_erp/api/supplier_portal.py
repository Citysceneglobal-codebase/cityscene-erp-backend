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
        description = row.get("description") or row.get("Description") or ""
        
        if not item_code or not rate:
            continue
            
        if not frappe.db.exists("Item", item_code):
            continue
            
        try:
            rate_val = float(rate)
        except ValueError:
            continue

        row_data = {
            "item_code": item_code,
            "rate": rate_val
        }
        # Add description only if the field exists on the child table
        try:
            row_data["description"] = description
            doc.append("items", row_data)
        except Exception:
            del row_data["description"]
            doc.append("items", row_data)
            
        items_added += 1

    if items_added == 0:
        frappe.throw(_("No valid items found in the CSV. Make sure item codes are valid and the header is 'item_code' and 'rate'."))

    doc.insert(ignore_permissions=True)
    doc.submit()
    
    return {"status": "success", "docname": doc.name}

@frappe.whitelist()
def download_template():
    csv_data = "item_code,rate,description\n"
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
        
    frappe.log_error(message=f"Received items: {items}", title="Supplier Portal Manual List Debug")
        
    if not items:
        frappe.throw(_("No items provided."))
        
    doc = frappe.new_doc("Supplier Rate List")
    doc.supplier = supplier
    doc.valid_from = valid_from
    if valid_upto:
        doc.valid_upto = valid_upto
        
    for item in items:
        row_data = {
            "item_code": item.get("item_code"),
            "rate": float(item.get("rate") or 0),
        }
        # Safely add description and attachment if the child table supports them
        try:
            row_data["description"] = item.get("description") or ""
            row_data["attachment"] = item.get("attachment") or ""
            doc.append("items", row_data)
        except Exception as e:
            frappe.log_error(message=f"Failed to append description/attachment. Error: {str(e)}", title="Supplier Portal Manual List Debug")
            del row_data["description"]
            del row_data["attachment"]
            doc.append("items", row_data)
        
    doc.insert(ignore_permissions=True)
    doc.submit()
    return {"status": "success", "docname": doc.name}

@frappe.whitelist()
def upload_supplier_attachment(filename: str, filecontent: str, mimetype: str = ""):
    """
    Accepts a base64-encoded file sent via frappe.call.
    Returns the public file URL.
    """
    supplier = get_supplier()
    if not supplier:
        frappe.throw(_("Could not identify the Supplier."))

    import base64

    try:
        content_bytes = base64.b64decode(filecontent)
    except Exception:
        frappe.throw(_("Invalid file content."))

    doc = frappe.get_doc({
        "doctype": "File",
        "file_name": filename,
        "is_private": 0,
        "content": content_bytes,
        "folder": "Home/Attachments"
    })
    doc.save(ignore_permissions=True)
    frappe.db.commit()

    return {"file_url": doc.file_url}

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
            fields=["item_code", "rate", "description", "attachment"],
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

@frappe.whitelist(allow_guest=True)
def register_new_supplier(company_name: str, contact_name: str, email: str, phone: str, gstin: str = None, pan: str = None, address_line1: str = None, address_line2: str = None, city: str = None, state: str = None, pincode: str = None):
    if not company_name or not contact_name or not email or not phone:
        frappe.throw(_("Company Name, Contact Name, Email, and Phone are required fields."))
        
    if frappe.db.exists("User", email):
        frappe.throw(_("User with email {0} already exists. Please log in or use a different email.").format(email))

    # Generate a random password
    password = frappe.generate_hash(length=10)

    # 1. Create Supplier
    supplier = frappe.get_doc({
        "doctype": "Supplier",
        "supplier_name": company_name,
        "supplier_group": "All Supplier Groups",
        "supplier_type": "Company",
        "pan": pan,
        "gst_category": "Registered Regular" if gstin else "Unregistered",
        "tax_id": gstin
    })
    supplier.insert(ignore_permissions=True)

    # 2. Create Address
    if address_line1 and city:
        address = frappe.get_doc({
            "doctype": "Address",
            "address_title": company_name,
            "address_type": "Billing",
            "address_line1": address_line1,
            "address_line2": address_line2,
            "city": city,
            "state": state,
            "pincode": pincode,
            "country": "India", # Defaulting to India
            "links": [{"link_doctype": "Supplier", "link_name": supplier.name}]
        })
        address.insert(ignore_permissions=True)

    # 3. Create Contact
    contact = frappe.get_doc({
        "doctype": "Contact",
        "first_name": contact_name,
        "email_id": email,
        "phone": phone,
        "is_primary_contact": 1,
        "links": [{"link_doctype": "Supplier", "link_name": supplier.name}]
    })
    contact.insert(ignore_permissions=True)

    # 4. Create User
    user = frappe.get_doc({
        "doctype": "User",
        "email": email,
        "first_name": contact_name,
        "send_welcome_email": 0,
        "new_password": password,
        "roles": [{"role": "Supplier"}]
    })
    user.flags.no_welcome_mail = True
    user.insert(ignore_permissions=True)

    # Link Contact to User
    frappe.db.set_value("Contact", contact.name, "user", user.name)
    
    # 5. Send Email with Credentials
    email_message = f"""
    <p>Dear {contact_name},</p>
    <p>Welcome to our Supplier Portal! Your registration has been successful.</p>
    <p>Here are your login credentials:</p>
    <ul>
        <li><b>Login ID:</b> {email}</li>
        <li><b>Password:</b> {password}</li>
    </ul>
    <p>Please log in and update your profile.</p>
    """
    try:
        frappe.sendmail(
            recipients=[email],
            subject="Welcome to Supplier Portal",
            message=email_message,
            now=True
        )
    except Exception as e:
        frappe.log_error(message=frappe.get_traceback(), title="Supplier Registration Email Failed")

    frappe.db.commit()

    return {
        "email": email,
        "password": password,
        "supplier_name": supplier.name
    }
