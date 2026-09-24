import frappe

def execute():
    frappe.init(site="cityscene-srb-erp")
    frappe.connect()
    
    web_form = frappe.get_doc("Web Form", "job-application")
    
    new_script = """
frappe.ready(function() {
    setTimeout(() => {
        let job_title = frappe.utils.get_query_params().job_title;
        if (!job_title && frappe.web_form && frappe.web_form.doc) {
            job_title = frappe.web_form.doc.job_title;
        }
        
        if (job_title) {
            frappe.call({
                method: 'cityscene_erp.api.recruitment.get_job_questions',
                args: { job_title: job_title },
                callback: function(r) {
                    if (r.message && r.message.length > 0) {
                        render_questions(r.message);
                    }
                }
            });
        }
    }, 500); // 500ms delay to ensure form is fully rendered

    function render_questions(questions) {
        // Prevent duplicate rendering
        if ($('#custom_questions_container').length > 0) return;
        
        let container = $('<div id="custom_questions_container" style="margin-top: 30px; padding: 15px; background: #f9fafb; border: 1px solid #e2e8f0; border-radius: 8px;"><h4>Job Specific Questions</h4><hr></div>');
        
        // Find best place to append
        if ($('.web-form-actions').length) {
            container.insertBefore('.web-form-actions');
        } else if ($('.form-page').length) {
            $('.form-page').append(container);
        } else {
            $('form').append(container);
        }
        
        window.custom_job_questions = questions;

        questions.forEach((q, idx) => {
            let field_html = `<div class="form-group" style="margin-bottom: 15px;">
                <label style="font-weight: 500;">${q.question} ${q.mandatory ? '<span class="text-danger" title="Mandatory">*</span>' : ''}</label>
            `;
            if (q.question_type === 'Data' || q.question_type === 'Int' || q.question_type === 'Float') {
                field_html += `<input type="text" class="form-control custom-q-input" data-idx="${idx}" ${q.mandatory ? 'required' : ''}>`;
            } else if (q.question_type === 'Text') {
                field_html += `<textarea class="form-control custom-q-input" data-idx="${idx}" ${q.mandatory ? 'required' : ''}></textarea>`;
            } else if (q.question_type === 'Select' && q.options) {
                let options = q.options.split('\\n');
                field_html += `<select class="form-control custom-q-input" data-idx="${idx}" ${q.mandatory ? 'required' : ''}>
                    <option value="">Select...</option>`;
                options.forEach(opt => {
                    if (opt.trim()) {
                        field_html += `<option value="${opt.trim()}">${opt.trim()}</option>`;
                    }
                });
                field_html += `</select>`;
            } else if (q.question_type === 'Check') {
                field_html += `<div class="checkbox"><label><input type="checkbox" class="custom-q-input" data-idx="${idx}"> Yes</label></div>`;
            }
            field_html += `</div>`;
            container.append(field_html);
        });
    }

    if (frappe.web_form) {
        frappe.web_form.events.on("before_save", () => {
            if (!window.custom_job_questions) return true;
            
            let answers = [];
            let all_valid = true;
            
            window.custom_job_questions.forEach((q, idx) => {
                let el = $(`.custom-q-input[data-idx="${idx}"]`);
                let val = q.question_type === 'Check' ? (el.is(':checked') ? 'Yes' : 'No') : el.val();
                
                if (q.mandatory && !val) {
                    frappe.msgprint(`Please answer: ${q.question}`);
                    all_valid = false;
                }
                answers.push({
                    question: q.question,
                    answer: val
                });
            });

            if (!all_valid) {
                return false;
            }

            frappe.web_form.set_value('custom_answers_json', JSON.stringify(answers));
            return true;
        });
    }
});
"""
    web_form.client_script = new_script
    web_form.save(ignore_permissions=True)
    frappe.db.commit()

if __name__ == "__main__":
    execute()
