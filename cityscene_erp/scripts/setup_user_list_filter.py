import frappe

def execute():
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
    else:
        print("Client Script 'Filter System Users Default' already exists.")
        
    frappe.db.commit()

