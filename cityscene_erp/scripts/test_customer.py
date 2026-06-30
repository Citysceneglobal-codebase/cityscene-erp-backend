import frappe
def execute():
    if frappe.db.exists("Customer", "Test Automation Customer"):
        frappe.delete_doc("Customer", "Test Automation Customer")
    if frappe.db.exists("Account", "Test Automation Customer - SP"):
        frappe.delete_doc("Account", "Test Automation Customer - SP")
    frappe.db.commit()
