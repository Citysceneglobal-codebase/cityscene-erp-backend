import frappe
from frappe import _

@frappe.whitelist()
def get_request_timeline(doctype: str, docname: str):
    """
    Returns the workflow timeline and the current pending approver.
    """
    if not frappe.has_permission(doctype, ptype="read", doc=docname):
        frappe.throw(_("No permission"), frappe.PermissionError)

    doc = frappe.get_doc(doctype, docname)
    workflow_state = doc.get("workflow_state")
    user = frappe.session.user
    
    # Get all workflow state changes from Version history
    versions = frappe.get_all(
        "Version",
        filters={"ref_doctype": doctype, "docname": docname},
        fields=["name", "creation", "owner", "data"],
        order_by="creation asc"
    )
    
    timeline = []
    
    # 1. Submission (Creation)
    timeline.append({
        "action": "Submitted",
        "actor": frappe.utils.get_fullname(doc.owner),
        "timestamp": doc.creation,
        "state": "Draft"
    })
    
    import json
    for v in versions:
        data = json.loads(v.data)
        if "changed" in data:
            for change in data["changed"]:
                if change[0] == "workflow_state":
                    timeline.append({
                        "action": "State Changed",
                        "actor": frappe.utils.get_fullname(v.owner),
                        "timestamp": v.creation,
                        "state": change[2]
                    })
    
    # 2. Determine Pending Approver
    pending_approver_name = None
    pending_approver_role = None
    is_current_user_approver = False
    
    user_roles = frappe.get_roles(user)
    
    if workflow_state == "Pending Reporting Manager Approval":
        pending_approver_role = "Reporting Manager"
        # Determine from Employee
        employee_id = doc.get("employee")
        if employee_id:
            emp = frappe.get_doc("Employee", employee_id)
            
            approver_user = None
            if doctype == "Leave Application" and emp.leave_approver:
                approver_user = emp.leave_approver
            elif doctype == "Expense Claim" and emp.expense_approver:
                approver_user = emp.expense_approver
            elif emp.reports_to:
                approver_user = frappe.db.get_value("Employee", emp.reports_to, "user_id")
                
            if approver_user:
                pending_approver_name = frappe.utils.get_fullname(approver_user)
                if approver_user == user or "HR Manager" in user_roles:
                        is_current_user_approver = True
    elif workflow_state == "Pending HR Approval":
        pending_approver_role = "HR Manager"
        pending_approver_name = "HR Department"
        if "HR Manager" in user_roles:
            is_current_user_approver = True
            
    return {
        "timeline": timeline,
        "current_state": workflow_state,
        "pending_approver_name": pending_approver_name,
        "pending_approver_role": pending_approver_role,
        "is_current_user_approver": is_current_user_approver
    }

@frappe.whitelist()
def process_workflow_action(doctype: str, docname: str, action: str):
    """
    Custom wrapper to process workflow actions and enforce strict hierarchy.
    """
    doc = frappe.get_doc(doctype, docname)
    user = frappe.session.user
    
    # Verify Reporting Manager hierarchy
    if action in ["Approve", "Reject"] and doc.workflow_state == "Pending Reporting Manager Approval":
        employee_id = doc.get("employee")
        if employee_id:
            emp = frappe.get_doc("Employee", employee_id)
            
            approver_user = None
            if doctype == "Leave Application" and emp.leave_approver:
                approver_user = emp.leave_approver
            elif doctype == "Expense Claim" and emp.expense_approver:
                approver_user = emp.expense_approver
            elif emp.reports_to:
                approver_user = frappe.db.get_value("Employee", emp.reports_to, "user_id")
            
            if approver_user:
                # If they are not the reporting manager, check if they are HR Manager (Bypass)
                if approver_user != user:
                    if "HR Manager" not in frappe.get_roles(user):
                        frappe.throw(_("Only the Reporting Manager ({0}) or HR Manager can approve this step.").format(frappe.utils.get_fullname(approver_user)))
                    else:
                        # HR Manager bypass! We override the action to "HR Approve"
                        if action == "Approve":
                            action = "HR Approve"
    
    # Apply standard workflow transition
    from frappe.model.workflow import apply_workflow
    apply_workflow(doc, action)
    
    # If the document is approved, ensure docstatus is updated and submitted
    doc.reload()
    if doc.workflow_state == "Approved" and doc.docstatus == 0:
        doc.submit()
        
        if doctype == "Attendance Request":
            # Auto-generate Check-ins
            try:
                if doc.custom_check_in_time:
                    frappe.get_doc({
                        "doctype": "Employee Checkin",
                        "employee": doc.employee,
                        "time": f"{doc.from_date} {doc.custom_check_in_time}",
                        "log_type": "IN"
                    }).insert(ignore_permissions=True)
                if doc.custom_check_out_time:
                    frappe.get_doc({
                        "doctype": "Employee Checkin",
                        "employee": doc.employee,
                        "time": f"{doc.to_date} {doc.custom_check_out_time}",
                        "log_type": "OUT"
                    }).insert(ignore_permissions=True)
            except Exception as e:
                frappe.log_error(title="Attendance Request Checkin Creation Error", message=str(e))
        
        
    return doc.as_dict()
