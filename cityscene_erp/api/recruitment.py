import frappe
from frappe import _
import base64

@frappe.whitelist(allow_guest=True)
def get_active_jobs():
    """
    Fetches all active and published Job Openings.
    Returns: list of dicts with job details.
    """
    # Fetch jobs that are Open and Published
    jobs = frappe.get_all(
        "Job Opening",
        filters={
            "status": "Open",
            "publish": 1
        },
        fields=[
            "name", "job_title", "designation", "department", 
            "location", "description", "route"
        ]
    )
    
    return {"status": "success", "data": jobs}


@frappe.whitelist(allow_guest=True)
def apply_for_job(first_name: str, email_id: str, job_title: str, last_name: str = "", phone_number: str = "", resume_base64: str = "", resume_filename: str = ""):
    """
    Accepts job application from external website.
    Creates a Job Applicant and attaches the resume.
    """
    if not first_name or not email_id or not job_title:
        frappe.throw(_("First Name, Email, and Job Title are required."))
        
    # Verify the job exists
    if not frappe.db.exists("Job Opening", job_title):
        frappe.throw(_("The specified Job Opening does not exist or is closed."))
        
    # Create the Job Applicant record
    applicant = frappe.get_doc({
        "doctype": "Job Applicant",
        "first_name": first_name,
        "last_name": last_name,
        "email_id": email_id,
        "phone_number": phone_number,
        "job_title": job_title,
        "status": "Open"
    })
    applicant.insert(ignore_permissions=True)
    
    # Handle Resume Upload if provided
    file_url = None
    if resume_base64 and resume_filename:
        try:
            content_bytes = base64.b64decode(resume_base64)
            file_doc = frappe.get_doc({
                "doctype": "File",
                "file_name": resume_filename,
                "attached_to_doctype": "Job Applicant",
                "attached_to_name": applicant.name,
                "is_private": 1,
                "content": content_bytes,
                "folder": "Home/Attachments"
            })
            file_doc.save(ignore_permissions=True)
            file_url = file_doc.file_url
            
            # Link file to applicant's resume field if it exists
            if applicant.meta.has_field('resume_attachment'):
                applicant.db_set('resume_attachment', file_url)
                
        except Exception as e:
            frappe.log_error(f"Resume upload failed for {email_id}: {str(e)}", "Recruitment API Error")
            # We don't block the application if the resume fails, just log it.
            
    frappe.db.commit()
    
    return {
        "status": "success", 
        "message": _("Application submitted successfully."),
        "applicant_id": applicant.name,
        "resume_url": file_url
    }
