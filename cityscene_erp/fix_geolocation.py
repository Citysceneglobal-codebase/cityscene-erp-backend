import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter
import json

def execute():
    # Make geolocation editable (not read_only)
    make_property_setter("Employee Checkin", "geolocation", "read_only", 0, "Check")
    
    # Backfill existing records that have lat/lon but no geolocation
    records = frappe.db.get_all("Employee Checkin", filters={"latitude": ["!=", 0], "longitude": ["!=", 0], "geolocation": ["is", "not set"]}, fields=["name", "latitude", "longitude"])
    for rec in records:
        geo = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "type": "Point",
                    "coordinates": [rec.longitude, rec.latitude]
                }
            }]
        }
        frappe.db.set_value("Employee Checkin", rec.name, "geolocation", json.dumps(geo))
        
    frappe.db.commit()
    return f"Fixed read_only and backfilled {len(records)} records."
