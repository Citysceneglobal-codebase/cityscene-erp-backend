import frappe
from frappe import _

@frappe.whitelist(allow_guest=True)
def register_new_partner(company_name: str, contact_name: str, email: str, phone: str, gstin: str = None, pan: str = None, address_line1: str = None, address_line2: str = None, city: str = None, state: str = None, pincode: str = None):
    if not company_name or not contact_name or not email or not phone:
        frappe.throw(_("Company Name, Contact Name, Email, and Phone are required fields."))
        
    if frappe.db.exists("User", email):
        frappe.throw(_("User with email {0} already exists. Please log in or use a different email.").format(email))

    # Generate a random password
    password = frappe.generate_hash(length=10)

    # 1. Create Sales Partner
    partner = frappe.get_doc({
        "doctype": "Sales Partner",
        "partner_name": company_name,
        "partner_type": "Retailer", # Need a generic partner type, or leave blank if not mandatory
        "custom_approval_status": "Pending Confirmation",
        "territory": "All Territories",
        "commission_rate": 0.0
    })
    
    # Optional fields if they exist in Sales Partner natively, but they don't, 
    # so we might want to just store PAN/GSTIN in address or custom fields. 
    # For now, we omit them if they don't exist natively.
    partner.insert(ignore_permissions=True)

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
            "links": [{"link_doctype": "Sales Partner", "link_name": partner.name}]
        })
        # Try setting PAN/GSTIN if it exists in Address (usually it's on Customer/Supplier)
        if gstin and hasattr(address, 'gstin'):
            address.gstin = gstin
        if pan and hasattr(address, 'pan'):
            address.pan = pan
            
        address.insert(ignore_permissions=True)

    # 3. Create Contact
    contact = frappe.get_doc({
        "doctype": "Contact",
        "first_name": contact_name,
        "email_id": email,
        "phone": phone,
        "is_primary_contact": 1,
        "links": [{"link_doctype": "Sales Partner", "link_name": partner.name}]
    })
    contact.insert(ignore_permissions=True)

    # 4. Create User
    # We will NOT assign the "Channel Partner" role until they are approved. 
    # For now, create the user with no roles or just "Guest".
    user = frappe.get_doc({
        "doctype": "User",
        "email": email,
        "first_name": contact_name,
        "send_welcome_email": 0,
        "new_password": password,
        "home_page": "/portal"
        # No roles initially until approved by admin
    })
    user.flags.no_welcome_mail = True
    user.insert(ignore_permissions=True)

    # Link Contact to User
    frappe.db.set_value("Contact", contact.name, "user", user.name)
    
    # 5. Send Email with Credentials (Optional, maybe say awaiting approval)
    email_message = f"""
    <p>Dear {contact_name},</p>
    <p>Your registration for the Channel Partner Portal has been received.</p>
    <p>Currently, your application is <b>Pending Confirmation</b> by our admin team.</p>
    <p>Once approved, you can log in using these credentials:</p>
    <ul>
        <li><b>Login ID:</b> {email}</li>
        <li><b>Password:</b> {password}</li>
    </ul>
    <p>We will notify you once your account is approved.</p>
    """
    try:
        frappe.sendmail(
            recipients=[email],
            subject="Partner Portal Registration Received",
            message=email_message,
            now=True
        )
    except Exception as e:
        frappe.log_error(message=frappe.get_traceback(), title="Partner Registration Email Failed")

    frappe.db.commit()

    return {
        "email": email,
        "password": password,
        "partner_name": partner.name
    }

def check_pending_partner_redirect(context):
    if context.get("pathname") != "me" or frappe.session.user == "Guest":
        return

    roles = frappe.get_roles(frappe.session.user)
    if "Channel Partner" not in roles and "Supplier" not in roles:
        contacts = frappe.db.get_all("Contact", {"user": frappe.session.user}, pluck="name")
        if contacts:
            partners = frappe.db.get_all("Dynamic Link", {
                "parent": ("in", contacts),
                "parenttype": "Contact",
                "link_doctype": "Sales Partner"
            }, pluck="link_name")
            for partner in partners:
                status = frappe.db.get_value("Sales Partner", partner, "custom_approval_status")
                if status == "Pending Confirmation":
                    frappe.local.flags.redirect_location = "/portal"
                    raise frappe.Redirect

def get_partner():
    user = frappe.session.user
    if user == "Guest":
        return None
        
    # Find all contacts linked to user
    contacts = frappe.get_all("Contact", filters={"user": user}, pluck="name")
    
    for contact in contacts:
        # Find partner linked to contact
        partner = frappe.db.get_value("Dynamic Link", {
            "parent": contact,
            "parenttype": "Contact",
            "link_doctype": "Sales Partner"
        }, "link_name")
        
        if partner:
            return partner
            
    return None

@frappe.whitelist()
def get_partner_lead(name):
    partner = get_partner()
    if not partner:
        frappe.throw(_("Not associated with any Channel Partner account."))
        
    frappe.flags.ignore_permissions = True
    try:
        lead = frappe.get_doc("Lead", name)
        if lead.custom_channel_partner != partner:
            frappe.throw(_("You don't have permission to read this lead."))
        
        doc_dict = lead.as_dict()
        doc_dict["documents"] = frappe.get_all("File", filters={"attached_to_doctype": "Lead", "attached_to_name": lead.name}, fields=["file_url", "file_name"], ignore_permissions=True)
        return doc_dict
    finally:
        frappe.flags.ignore_permissions = False

@frappe.whitelist()
def get_partner_leads():
    partner = get_partner()
    if not partner:
        return {"leads": [], "stats": {"total": 0, "converted": 0}}
        
    leads = frappe.get_all("Lead", filters={"custom_channel_partner": partner}, fields=["name", "lead_name", "first_name", "last_name", "email_id", "mobile_no", "status", "company_name"], ignore_permissions=True)
    
    # Get attachments for each lead
    for lead in leads:
        files = frappe.get_all("File", filters={"attached_to_doctype": "Lead", "attached_to_name": lead.name}, fields=["file_url", "file_name"], ignore_permissions=True)
        lead.documents = files
        
    converted = len([l for l in leads if l.status == "Converted"])
    
    return {
        "leads": leads,
        "stats": {
            "total": len(leads),
            "converted": converted
        }
    }

@frappe.whitelist()
def create_lead(**kwargs):
    partner = get_partner()
    if not partner:
        frappe.throw(_("Not associated with any Channel Partner account."))
        
    file_name = kwargs.pop("file_name", None)
    file_content = kwargs.pop("file_content", None)
    mime_type = kwargs.pop("mime_type", None)
    kwargs.pop("cmd", None)
    
    for key, value in kwargs.items():
        if value == "":
            kwargs[key] = None
            
    lead = frappe.new_doc("Lead")
    lead.update(kwargs)
    lead.custom_channel_partner = partner
    if not lead.status:
        lead.status = "Lead"
        
    lead.insert(ignore_permissions=True)
    
    if file_content and file_name:
        import base64
        try:
            content_bytes = base64.b64decode(file_content)
            doc = frappe.get_doc({
                "doctype": "File",
                "file_name": file_name,
                "is_private": 0,
                "content": content_bytes,
                "attached_to_doctype": "Lead",
                "attached_to_name": lead.name,
                "folder": "Home/Attachments"
            })
            doc.save(ignore_permissions=True)
            lead.db_set('custom_attach_bill', doc.file_url)
        except Exception as e:
            frappe.log_error(f"Failed to upload document for Lead {lead.name}. Error: {str(e)}", "Partner Portal Lead Document Upload")

    frappe.db.commit()
    return lead.name

@frappe.whitelist()
def update_lead(name, **kwargs):
    partner = get_partner()
    if not partner:
        frappe.throw(_("Not associated with any Channel Partner account."))
        
    lead = frappe.get_doc("Lead", name)
    
    if lead.custom_channel_partner != partner:
        frappe.throw(_("You don't have permission to edit this lead."))
        
    if lead.status not in ["Lead", "Open"]:
        frappe.throw(_("You can only edit a lead while it is in 'Lead' or 'Open' status."))
        
    file_name = kwargs.pop("file_name", None)
    file_content = kwargs.pop("file_content", None)
    mime_type = kwargs.pop("mime_type", None)
    kwargs.pop("cmd", None)
    kwargs.pop("name", None)
    
    for key, value in kwargs.items():
        if value == "":
            kwargs[key] = None
            
    lead.update(kwargs)
    lead.save(ignore_permissions=True)
    
    if file_content and file_name:
        import base64
        try:
            content_bytes = base64.b64decode(file_content)
            doc = frappe.get_doc({
                "doctype": "File",
                "file_name": file_name,
                "is_private": 0,
                "content": content_bytes,
                "attached_to_doctype": "Lead",
                "attached_to_name": lead.name,
                "folder": "Home/Attachments"
            })
            doc.save(ignore_permissions=True)
            lead.db_set('custom_attach_bill', doc.file_url)
        except Exception as e:
            frappe.log_error(f"Failed to upload document for Lead {lead.name}. Error: {str(e)}", "Partner Portal Lead Document Upload")

    frappe.db.commit()
    return lead.name

@frappe.whitelist()
def get_user_role():
    user = frappe.session.user
    roles = frappe.get_roles(user)
    if "Channel Partner" in roles:
        return "Channel Partner"
    
    profile = frappe.db.get_value("User", user, "role_profile_name")
    if profile:
        return profile
        
    return "Employee"


@frappe.whitelist()
def get_partner_quotations(lead_name):
    partner = get_partner()
    if not partner:
        frappe.throw(_("Not associated with any Channel Partner account."))
        
    frappe.flags.ignore_permissions = True
    try:
        lead = frappe.get_doc("Lead", lead_name)
        if lead.custom_channel_partner != partner:
            frappe.throw(_("You don't have permission to read this lead's quotations."))
            
        quotations = frappe.get_all("Quotation", filters={"quotation_to": "Lead", "party_name": lead_name}, fields=["name", "grand_total", "status", "transaction_date", "valid_till"])
        return quotations
    finally:
        frappe.flags.ignore_permissions = False

@frappe.whitelist()
def get_partner_quotation(name):
    partner = get_partner()
    if not partner:
        frappe.throw(_("Not associated with any Channel Partner account."))
        
    frappe.flags.ignore_permissions = True
    try:
        quotation = frappe.get_doc("Quotation", name)
        if quotation.quotation_to == "Lead":
            lead = frappe.get_doc("Lead", quotation.party_name)
            if lead.custom_channel_partner != partner:
                frappe.throw(_("You don't have permission to read this quotation."))
        else:
            frappe.throw(_("You don't have permission to read this quotation."))
            
        return quotation.as_dict()
    finally:
        frappe.flags.ignore_permissions = False

@frappe.whitelist()
def get_partner_print_formats(doc_type):
    frappe.flags.ignore_permissions = True
    try:
        formats = frappe.get_all("Print Format", filters={"doc_type": doc_type}, fields=["name"])
        return formats
    finally:
        frappe.flags.ignore_permissions = False

@frappe.whitelist()
def download_partner_quotation_pdf(name, format):
    partner = get_partner()
    if not partner:
        frappe.throw(_("Not associated with any Channel Partner account."))
        
    frappe.flags.ignore_permissions = True
    try:
        quotation = frappe.get_doc("Quotation", name)
        if quotation.quotation_to == "Lead":
            lead = frappe.get_doc("Lead", quotation.party_name)
            if lead.custom_channel_partner != partner:
                frappe.throw(_("You don't have permission to read this quotation."))
        
        from frappe.utils.pdf import get_pdf
        html = frappe.get_print("Quotation", name, print_format=format)
        frappe.local.response.filename = f"{name}.pdf"
        frappe.local.response.filecontent = get_pdf(html)
        frappe.local.response.type = "pdf"
    finally:
        frappe.flags.ignore_permissions = False
