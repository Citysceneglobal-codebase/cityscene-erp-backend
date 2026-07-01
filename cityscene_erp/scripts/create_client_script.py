import frappe

def run():
    if not frappe.db.exists("Client Script", "Payment Entry Date Automation"):
        doc = frappe.get_doc({
            "doctype": "Client Script",
            "dt": "Payment Entry",
            "name": "Payment Entry Date Automation",
            "module": "Accounts",
            "script": """
frappe.ui.form.on('Payment Entry', {
    posting_date: function(frm) {
        if (frm.doc.posting_date) {
            frm.set_value('reference_date', frm.doc.posting_date);
        }
    }
});
            """,
            "enabled": 1
        })
        doc.insert()
        frappe.db.commit()
        print("Client Script created successfully.")
    else:
        print("Client Script already exists.")
