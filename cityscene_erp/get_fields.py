import frappe

def execute():
    doctypes = ['Expense Claim', 'Attendance Request', 'Travel Request']
    for dt in doctypes:
        print(f"\n--- {dt} ---")
        try:
            meta = frappe.get_meta(dt)
            for f in meta.fields:
                if f.fieldtype not in ['Section Break', 'Column Break', 'HTML', 'Tab Break']:
                    print(f"{f.fieldname} ({f.fieldtype}): {f.label}")
        except Exception as e:
            print(f"Error fetching {dt}: {e}")
