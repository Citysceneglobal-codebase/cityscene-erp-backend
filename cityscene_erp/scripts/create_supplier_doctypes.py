import frappe

def execute():
    # 1. Create Child Table: Supplier Rate List Item
    if not frappe.db.exists("DocType", "Supplier Rate List Item"):
        doc = frappe.get_doc({
            "doctype": "DocType",
            "name": "Supplier Rate List Item",
            "module": "Cityscene Erp",
            "custom": 1,
            "istable": 1,
            "fields": [
                {
                    "fieldname": "item_code",
                    "label": "Item Code",
                    "fieldtype": "Link",
                    "options": "Item",
                    "in_list_view": 1,
                    "reqd": 1
                },
                {
                    "fieldname": "item_name",
                    "label": "Item Name",
                    "fieldtype": "Data",
                    "fetch_from": "item_code.item_name",
                    "in_list_view": 1
                },
                {
                    "fieldname": "uom",
                    "label": "UOM",
                    "fieldtype": "Link",
                    "options": "UOM",
                    "fetch_from": "item_code.stock_uom",
                    "in_list_view": 1
                },
                {
                    "fieldname": "rate",
                    "label": "Rate",
                    "fieldtype": "Currency",
                    "in_list_view": 1,
                    "reqd": 1
                }
            ]
        })
        doc.insert()
        frappe.db.commit()
        print("Created DocType: Supplier Rate List Item")

    # 2. Create Parent Table: Supplier Rate List
    if not frappe.db.exists("DocType", "Supplier Rate List"):
        doc = frappe.get_doc({
            "doctype": "DocType",
            "name": "Supplier Rate List",
            "module": "Cityscene Erp",
            "custom": 1,
            "is_submittable": 1,
            "fields": [
                {
                    "fieldname": "supplier",
                    "label": "Supplier",
                    "fieldtype": "Link",
                    "options": "Supplier",
                    "reqd": 1,
                    "in_list_view": 1,
                    "in_standard_filter": 1
                },
                {
                    "fieldname": "valid_from",
                    "label": "Valid From",
                    "fieldtype": "Date",
                    "reqd": 1,
                    "in_list_view": 1
                },
                {
                    "fieldname": "valid_upto",
                    "label": "Valid Upto",
                    "fieldtype": "Date",
                    "in_list_view": 1
                },
                {
                    "fieldname": "items",
                    "label": "Items",
                    "fieldtype": "Table",
                    "options": "Supplier Rate List Item",
                    "reqd": 1
                }
            ],
            "permissions": [
                {
                    "role": "System Manager",
                    "read": 1,
                    "write": 1,
                    "create": 1,
                    "submit": 1,
                    "cancel": 1,
                    "delete": 1
                },
                {
                    "role": "Purchase Manager",
                    "read": 1,
                    "write": 1,
                    "create": 1,
                    "submit": 1,
                    "cancel": 1
                },
                {
                    "role": "Supplier",
                    "read": 1,
                    "write": 1,
                    "create": 1
                }
            ]
        })
        doc.insert()
        frappe.db.commit()
        print("Created DocType: Supplier Rate List")

if __name__ == "__main__":
    execute()
