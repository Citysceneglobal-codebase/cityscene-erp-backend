import frappe

def execute():
    frappe.set_user("Guest")
    try:
        res = frappe.get_all("Job Opening Question", filters={"parent": "HR-OPN-2026-0001"}, fields=["question"], ignore_permissions=True)
        print("Guest result:", res)
    except frappe.PermissionError:
        print("PermissionError!")

