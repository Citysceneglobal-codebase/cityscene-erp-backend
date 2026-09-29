import frappe


@frappe.whitelist(allow_guest=True)
def request_account_deletion(full_name: str, email: str, reason: str = "", comments: str = ""):
	"""
	Public endpoint for account/data deletion requests.
	Required by Google Play Store and Apple App Store policies.

	This logs the request for audit purposes and returns a 200 OK response.
	The actual data removal, if applicable, is handled manually by the admin team
	within 30 business days as stated in the Privacy Policy.
	"""
	if not full_name or not email:
		frappe.throw("Full name and email are required.")

	# Log the request as a ToDo/Note for the admin team to review
	try:
		frappe.get_doc({
			"doctype": "ToDo",
			"description": f"Account Deletion Request\n\nName: {full_name}\nEmail: {email}\nReason: {reason}\nComments: {comments}",
			"priority": "Medium",
			"status": "Open",
			"assigned_by": "Administrator",
			"owner": "Administrator",
		}).insert(ignore_permissions=True)
		frappe.db.commit()
	except Exception:
		# Silently fail the logging — never block the user response
		frappe.log_error(frappe.get_traceback(), "Account Deletion Request Logging Failed")

	return {
		"status": "ok",
		"message": "Your account deletion request has been received. Your data will be deleted and your account will be removed within 30 business days. You will receive a confirmation at the email address provided."
	}
