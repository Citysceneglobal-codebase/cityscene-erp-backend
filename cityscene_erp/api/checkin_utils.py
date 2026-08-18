import frappe
import base64
import os
from frappe import _
from frappe.utils import now_datetime, today, get_datetime


@frappe.whitelist()
def calculate_employee_daily_timings(employee_id: str) -> dict:
    """
    Returns total worked seconds for today and the last log action (IN/OUT)
    for the given employee. Used to restore timer state on page load.
    """
    if not employee_id:
        frappe.throw(_("Employee ID is required"))

    # Fetch today's checkin records ordered by time ascending
    records = frappe.get_all(
        "Employee Checkin",
        filters={
            "employee": employee_id,
            "time": ["between", [today() + " 00:00:00", today() + " 23:59:59"]],
        },
        fields=["log_type", "time"],
        order_by="time asc",
    )

    total_seconds = 0
    last_action = ""
    last_in_time = None

    for record in records:
        log_type = record.get("log_type", "")
        log_time = get_datetime(record.get("time"))

        if log_type == "IN":
            last_in_time = log_time
            last_action = "IN"
        elif log_type == "OUT":
            last_action = "OUT"
            if last_in_time:
                delta = (log_time - last_in_time).total_seconds()
                total_seconds += max(0, delta)
                last_in_time = None

    # If still checked in (open IN with no corresponding OUT), add live elapsed
    if last_action == "IN" and last_in_time:
        elapsed = (now_datetime() - last_in_time).total_seconds()
        total_seconds += max(0, elapsed)

    return {
        "total_seconds": int(total_seconds),
        "last_action": last_action,
    }


@frappe.whitelist()
def upload_selfie(
    base64_content: str,
    filename: str,
    doctype: str,
    docname: str,
    is_private: int = 1,
) -> str:
    """
    Decodes a base64 image string and attaches it to the given document.
    Returns the file URL.
    Compatible with Frappe v17 File attachment pattern.
    """
    if not base64_content:
        frappe.throw(_("No image content provided"))

    # Decode base64 → bytes
    try:
        file_content = base64.b64decode(base64_content)
    except Exception:
        frappe.throw(_("Invalid base64 image content"))

    # Create the file using Frappe's File DocType
    file_doc = frappe.get_doc(
        {
            "doctype": "File",
            "file_name": filename,
            "attached_to_doctype": doctype,
            "attached_to_name": docname,
            "is_private": int(is_private),
            "content": file_content,
        }
    )
    file_doc.save(ignore_permissions=True)

    # Update the selfie preview fields on the Employee Checkin form
    if doctype == "Employee Checkin" and docname:
        frappe.db.set_value(
            "Employee Checkin",
            docname,
            {
                "custom_selfie": file_doc.file_url,
                "selfie": file_doc.file_url,
            },
            update_modified=False,
        )

    return file_doc.file_url


@frappe.whitelist()
def get_daily_checkin_logs(employee_id: str, date: str) -> list:
    """
    Returns all check-in logs for a specific employee on a specific date,
    including the attached selfie image URL.
    """
    if not employee_id or not date:
        frappe.throw(_("Employee ID and Date are required"))

    start_time = f"{date} 00:00:00"
    end_time = f"{date} 23:59:59"

    records = frappe.get_all(
        "Employee Checkin",
        filters={
            "employee": employee_id,
            "time": ["between", [start_time, end_time]],
        },
        fields=["name", "log_type", "time", "latitude", "longitude", "device_id"],
        order_by="time desc",
    )

    for record in records:
        # Fetch the selfie image URL attached to this checkin
        file_doc = frappe.get_all(
            "File",
            filters={
                "attached_to_doctype": "Employee Checkin",
                "attached_to_name": record["name"],
            },
            fields=["file_url"],
            limit=1
        )
        record["image_url"] = file_doc[0]["file_url"] if file_doc else None

    return records
