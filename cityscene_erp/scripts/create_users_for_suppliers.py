import frappe

def execute():
    suppliers = frappe.get_all("Supplier", fields=["name", "supplier_name"])
    print(f"Processing {len(suppliers)} Suppliers to create Portal Users...")
    
    users_created = 0
    users_linked = 0
    
    for supp in suppliers:
        supplier_doc = frappe.get_doc("Supplier", supp.name)
        
        # Check if already has portal users
        if len(supplier_doc.get("portal_users", [])) > 0:
            continue
            
        # Get primary contact or first contact
        contact_name = frappe.db.get_value("Dynamic Link", 
            {"link_doctype": "Supplier", "link_name": supp.name, "parenttype": "Contact"}, 
            "parent")
            
        if not contact_name:
            continue
            
        contact_doc = frappe.get_doc("Contact", contact_name)
        
        # Check if contact has email
        if not contact_doc.email_ids:
            continue
            
        primary_email = None
        for e in contact_doc.email_ids:
            if e.is_primary:
                primary_email = e.email_id
                break
        if not primary_email:
            primary_email = contact_doc.email_ids[0].email_id
            
        if not primary_email:
            continue
            
        # Check if user already exists
        user_name = None
        if frappe.db.exists("User", primary_email):
            user_name = primary_email
        else:
            # Create user
            user = frappe.get_doc({
                "doctype": "User",
                "email": primary_email,
                "first_name": contact_doc.first_name or supp.supplier_name,
                "last_name": contact_doc.last_name or "",
                "user_type": "Website User",
                "send_welcome_email": 0
            })
            user.insert(ignore_permissions=True)
            user_name = user.name
            users_created += 1
            
        # Add Supplier Role
        user_doc = frappe.get_doc("User", user_name)
        if "Supplier" not in [r.role for r in user_doc.roles]:
            user_doc.add_roles("Supplier")
            
        # Link to Contact if not linked
        if contact_doc.user != user_name:
            contact_doc.user = user_name
            contact_doc.flags.ignore_permissions = True
            contact_doc.save()
            
        # Add to Supplier portal_users
        supplier_doc.append("portal_users", {
            "user": user_name
        })
        supplier_doc.flags.ignore_permissions = True
        supplier_doc.flags.ignore_mandatory = True
        supplier_doc.save()
        users_linked += 1

    # Insert Client Script for User List to hide Website Users by default
    if not frappe.db.exists("Client Script", "Filter System Users Default"):
        doc = frappe.get_doc({
            "doctype": "Client Script",
            "name": "Filter System Users Default",
            "dt": "User",
            "view": "List",
            "module": "Cityscene Erp",
            "script": """
frappe.listview_settings['User'] = {
    onload: function(listview) {
        // If there are no filters currently applied, default to System Users
        let existing_filters = listview.filter_area.get();
        if (existing_filters.length === 0) {
            listview.filter_area.add([
                ['User', 'user_type', '=', 'System User']
            ]);
        }
    }
};
"""
        })
        doc.insert(ignore_permissions=True)
        print("Created Client Script to filter User list by default.")
        
    frappe.db.commit()
    print(f"Done! Created {users_created} new users and linked {users_linked} users to suppliers.")

