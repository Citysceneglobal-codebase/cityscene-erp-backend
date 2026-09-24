import frappe
import json


@frappe.whitelist(allow_guest=True)
def get_job_questions(job_title: str):
	if not job_title:
		return []

	questions = frappe.get_all(
		"Job Opening Question",
		filters={"parent": job_title, "parenttype": "Job Opening"},
		fields=["question", "question_type", "options", "mandatory"],
		order_by="idx asc",
		ignore_permissions=True
	)
	return questions


@frappe.whitelist(allow_guest=True)
def save_answers(applicant: str, answers_json: str):
	"""Called from the web form's after_save hook to save dynamic answers.
	Uses allow_guest=True because the applicant is not logged in.
	Validates that the applicant exists before writing to prevent abuse.
	"""
	if not applicant or not answers_json:
		return

	# Verify the applicant document actually exists (prevents abuse)
	if not frappe.db.exists("Job Applicant", applicant):
		frappe.throw("Invalid applicant reference.")

	try:
		answers = json.loads(answers_json)
	except (ValueError, TypeError):
		frappe.log_error(
			message=f"Invalid answers JSON for applicant {applicant}: {answers_json}",
			title="Recruitment: Invalid Answers JSON"
		)
		return

	# Load doc with ignore_permissions since user is a guest
	doc = frappe.get_doc("Job Applicant", applicant)
	doc.flags.ignore_permissions = True

	doc.set("custom_job_answers", [])
	for a in answers:
		doc.append("custom_job_answers", {
			"question": a.get("question"),
			"answer": str(a.get("answer", ""))
		})

	# Use db_update to avoid re-triggering hooks and validation
	doc.save(ignore_permissions=True)
	frappe.db.commit()

	return {"status": "ok", "total_answers": len(answers)}


def process_dynamic_answers(doc, method):
	"""Fallback hook: processes custom_answers_json if it arrives via form POST."""
	if doc.custom_answers_json:
		try:
			answers = json.loads(doc.custom_answers_json)
			doc.set("custom_job_answers", [])
			for a in answers:
				doc.append("custom_job_answers", {
					"question": a.get("question"),
					"answer": str(a.get("answer", ""))
				})
			doc.custom_answers_json = None
		except Exception:
			frappe.log_error(
				message=frappe.get_traceback(),
				title="Recruitment: Error parsing dynamic answers"
			)
