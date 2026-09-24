import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

def create_doctypes():
    # 1. Job Opening Question
    if not frappe.db.exists("DocType", "Job Opening Question"):
        doc = frappe.get_doc({
            "doctype": "DocType",
            "name": "Job Opening Question",
            "module": "Custom",
            "custom": 1,
            "istable": 1,
            "fields": [
                {"fieldname": "question", "fieldtype": "Data", "label": "Question", "in_list_view": 1, "reqd": 1},
                {"fieldname": "question_type", "fieldtype": "Select", "label": "Type", "options": "Data\nText\nSelect\nCheck\nInt", "in_list_view": 1, "reqd": 1, "default": "Data"},
                {"fieldname": "options", "fieldtype": "Text", "label": "Options (One per line)", "depends_on": "eval:doc.question_type=='Select'"},
                {"fieldname": "mandatory", "fieldtype": "Check", "label": "Mandatory", "default": "0", "in_list_view": 1}
            ]
        })
        doc.insert()

    # 2. Job Applicant Answer
    if not frappe.db.exists("DocType", "Job Applicant Answer"):
        doc = frappe.get_doc({
            "doctype": "DocType",
            "name": "Job Applicant Answer",
            "module": "Custom",
            "custom": 1,
            "istable": 1,
            "fields": [
                {"fieldname": "question", "fieldtype": "Data", "label": "Question", "in_list_view": 1, "read_only": 1},
                {"fieldname": "answer", "fieldtype": "Text", "label": "Answer", "in_list_view": 1, "read_only": 1}
            ]
        })
        doc.insert()

def add_custom_fields():
    custom_fields = {
        "Job Opening": [
            {
                "fieldname": "custom_job_questions",
                "label": "Job Questions",
                "fieldtype": "Table",
                "options": "Job Opening Question",
                "insert_after": "description"
            }
        ],
        "Job Applicant": [
            {
                "fieldname": "custom_answers_json",
                "label": "Answers JSON",
                "fieldtype": "Text",
                "hidden": 1,
                "insert_after": "cover_letter"
            },
            {
                "fieldname": "custom_job_answers",
                "label": "Job Answers",
                "fieldtype": "Table",
                "options": "Job Applicant Answer",
                "insert_after": "custom_answers_json"
            }
        ]
    }
    create_custom_fields(custom_fields)

def modify_web_form():
    custom_script = """
frappe.web_form.after_load = () => {
    let job_title = frappe.web_form.get_value('job_title');
    if (job_title) {
        frappe.call({
            method: 'frappe.client.get',
            args: {
                doctype: 'Job Opening',
                name: job_title
            },
            callback: function(r) {
                if (r.message && r.message.custom_job_questions) {
                    render_custom_questions(r.message.custom_job_questions);
                }
            }
        });
    }

    frappe.web_form.events.on('before_save', () => {
        let resume_link = frappe.web_form.get_value('resume_link');
        let resume_attachment = frappe.web_form.get_value('resume_attachment');
        
        if (!resume_link && !resume_attachment) {
            frappe.msgprint('Please provide either a Resume Link or upload a Resume Attachment.');
            return false;
        }

        let answers = [];
        $('.dynamic-question-input').each(function() {
            let q = $(this).data('question');
            let type = $(this).data('type');
            let val = $(this).val();
            if (type === 'Check') {
                val = $(this).is(':checked') ? 'Yes' : 'No';
            }
            if ($(this).attr('required') && !val) {
                frappe.msgprint(`Question "${q}" is mandatory.`);
                return false;
            }
            answers.push({question: q, answer: val});
        });
        
        frappe.web_form.set_value('custom_answers_json', JSON.stringify(answers));
    });
};

function render_custom_questions(questions) {
    if (questions.length === 0) return;
    
    let html = '<div class="custom-questions-section" style="margin-top: 30px; margin-bottom: 30px;">';
    html += '<h4>Job Specific Questions</h4>';
    
    questions.forEach((q, idx) => {
        html += `<div class="form-group">`;
        html += `<label class="control-label ${q.mandatory ? 'reqd' : ''}">${q.question}</label>`;
        
        if (q.question_type === 'Data') {
            html += `<input type="text" class="form-control dynamic-question-input" data-question="${q.question}" data-type="Data" ${q.mandatory ? 'required' : ''}>`;
        } else if (q.question_type === 'Text') {
            html += `<textarea class="form-control dynamic-question-input" data-question="${q.question}" data-type="Text" rows="3" ${q.mandatory ? 'required' : ''}></textarea>`;
        } else if (q.question_type === 'Int') {
            html += `<input type="number" class="form-control dynamic-question-input" data-question="${q.question}" data-type="Int" ${q.mandatory ? 'required' : ''}>`;
        } else if (q.question_type === 'Select') {
            let options = q.options ? q.options.split('\\n') : [];
            html += `<select class="form-control dynamic-question-input" data-question="${q.question}" data-type="Select" ${q.mandatory ? 'required' : ''}>`;
            html += `<option value=""></option>`;
            options.forEach(opt => {
                if (opt.trim()) {
                    html += `<option value="${opt.trim()}">${opt.trim()}</option>`;
                }
            });
            html += `</select>`;
        } else if (q.question_type === 'Check') {
            html += `<div class="checkbox"><label><input type="checkbox" class="dynamic-question-input" data-question="${q.question}" data-type="Check"> Yes</label></div>`;
        }
        
        html += `</div>`;
    });
    
    html += '</div>';
    
    $(html).insertAfter($('.frappe-control[data-fieldname="resume_attachment"]').parent());
}
"""

    frappe.db.set_value("Web Form", "job-application", "client_script", custom_script)
    frappe.db.set_value("Web Form", "job-application", "show_attachments", 1)

    if not frappe.db.exists("Web Form Field", {"parent": "job-application", "fieldname": "custom_answers_json"}):
        field_doc = frappe.get_doc({
            "doctype": "Web Form Field",
            "parent": "job-application",
            "parentfield": "web_form_fields",
            "parenttype": "Web Form",
            "fieldname": "custom_answers_json",
            "fieldtype": "Data",
            "label": "Custom Answers JSON",
            "hidden": 1
        })
        field_doc.flags.ignore_permissions = True
        field_doc.db_insert()
        
    if not frappe.db.exists("Web Form Field", {"parent": "job-application", "fieldname": "resume_attachment"}):
        field_doc = frappe.get_doc({
            "doctype": "Web Form Field",
            "parent": "job-application",
            "parentfield": "web_form_fields",
            "parenttype": "Web Form",
            "fieldname": "resume_attachment",
            "fieldtype": "Attach",
            "label": "Resume Attachment",
            "hidden": 0
        })
        field_doc.flags.ignore_permissions = True
        field_doc.db_insert()
    else:
        frappe.db.set_value("Web Form Field", {"parent": "job-application", "fieldname": "resume_attachment"}, "hidden", 0)

def create_all():
    create_doctypes()
    add_custom_fields()
    modify_web_form()
    frappe.db.commit()
    print("Done")

import frappe
from frappe.modules.export_file import export_to_files
def export():
    export_to_files(record_list=[['DocType', 'Job Opening Question'], ['DocType', 'Job Applicant Answer']])

