import frappe

def execute():
    # Check if employee for Administrator already exists
    emp = frappe.db.get_value("Employee", {"user_id": "Administrator"})
    if emp:
        return f"Employee {emp} already exists and is linked to Administrator."
    
    # Create new employee
    doc = frappe.get_doc({
        "doctype": "Employee",
        "first_name": "Admin",
        "last_name": "Test",
        "status": "Active",
        "gender": "Male",
        "date_of_birth": "1990-01-01",
        "date_of_joining": "2020-01-01",
        "company": "SRB Power",
        "user_id": "Administrator"
    })
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    return f"Created Employee {doc.name} for Administrator!"
