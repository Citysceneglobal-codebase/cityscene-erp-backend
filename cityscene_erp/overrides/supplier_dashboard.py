from frappe import _
from erpnext.buying.doctype.supplier.supplier_dashboard import get_data as get_default_data

def get_data(data=None):
    if not data:
        data = get_default_data()
        
    added = False
    for section in data.get("transactions", []):
        if section.get("label") == _("Pricing"):
            if "Supplier Rate List" not in section.get("items", []):
                section["items"].append("Supplier Rate List")
            added = True
            break
            
    if not added:
        data["transactions"].append({
            "label": _("Pricing"),
            "items": ["Supplier Rate List"]
        })
        
    return data
