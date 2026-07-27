import frappe

def compute_late_early(doc, method):
    if doc.shift and doc.time and doc.shift_actual_start and doc.shift_actual_end:
        shift = frappe.get_doc("Shift Type", doc.shift)
        late_grace = (shift.late_entry_grace_period or 0) * 60
        early_grace = (shift.early_exit_grace_period or 0) * 60
        
        if doc.log_type == "IN":
            diff = frappe.utils.time_diff_in_seconds(doc.time, doc.shift_actual_start)
            if diff > late_grace:
                doc.custom_is_late_checkin = 1
            else:
                doc.custom_is_late_checkin = 0
                
        elif doc.log_type == "OUT":
            diff = frappe.utils.time_diff_in_seconds(doc.shift_actual_end, doc.time)
            if diff > early_grace:
                doc.custom_is_early_checkout = 1
            else:
                doc.custom_is_early_checkout = 0
