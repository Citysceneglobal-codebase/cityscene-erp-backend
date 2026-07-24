import frappe

def execute():
    # Insert or Update Client Script for User List to hide Website Users by default
    script_content = """
frappe.listview_settings['User'] = {
    onload: function(listview) {
        // Check if there is already a filter for user_type
        let existing_filters = listview.filter_area.get();
        let has_user_type_filter = false;
        
        for (let i = 0; i < existing_filters.length; i++) {
            if (existing_filters[i][1] === 'user_type') {
                has_user_type_filter = true;
                break;
            }
        }
        
        if (!has_user_type_filter) {
            listview.filter_area.add([
                ['User', 'user_type', '=', 'System User']
            ]);
        }
    }
};
"""
    if frappe.db.exists("Client Script", "Filter System Users Default"):
        doc = frappe.get_doc("Client Script", "Filter System Users Default")
        doc.script = script_content
        doc.save(ignore_permissions=True)
        print("Updated Client Script 'Filter System Users Default'.")
    else:
        doc = frappe.get_doc({
            "doctype": "Client Script",
            "name": "Filter System Users Default",
            "dt": "User",
            "view": "List",
            "module": "Cityscene Erp",
            "script": script_content
        })
        doc.insert(ignore_permissions=True)
        print("Created Client Script to filter User list by default.")
        
    frappe.db.commit()

