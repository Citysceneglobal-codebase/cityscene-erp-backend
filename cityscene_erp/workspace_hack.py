import frappe

def run():
    for name in ["Buying", "Selling"]:
        ws = frappe.get_doc("Workspace Sidebar", name)
        ws.flags.ignore_links = True
        ws.flags.ignore_validate = True
        
        # Check if already added
        exists = any(i.link_to == "party-accounting" for i in ws.items)
        if not exists:
            ws.append("items", {
                "type": "Link",
                "label": "Party Accounting Dashboard",
                "link_to": "party-accounting",
                "link_type": "Page",
                "child": 0,
                "indent": 0,
                "icon": "accounting",
                "collapsible": 0
            })
            ws.save(ignore_permissions=True)
            print(f"Added to {name} Workspace Sidebar")
        else:
            print(f"Already exists in {name}")
    frappe.db.commit()

