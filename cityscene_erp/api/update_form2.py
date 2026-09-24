import frappe

def execute():
    frappe.init(site="cityscene-srb-erp")
    frappe.connect()
    
    # 1. Update idx to make sure minimum and maximum are side-by-side
    # Current indices (approx):
    # 9: Section Break
    # 10: currency
    # 11: Column Break (hidden) -> wait, let's unhide it.
    
    frappe.db.sql("""UPDATE `tabWeb Form Field` SET hidden=0 WHERE parent='job-application' AND name='i3npvb6g7l'""")
    
    # We want: 
    # Section Break (idx 9)
    # lower_range (idx 10)
    # Column Break (idx 11)
    # upper_range (idx 12)
    # currency (idx 13) - hidden
    
    frappe.db.sql("""UPDATE `tabWeb Form Field` SET idx=10 WHERE parent='job-application' AND fieldname='lower_range'""")
    frappe.db.sql("""UPDATE `tabWeb Form Field` SET idx=11 WHERE parent='job-application' AND name='i3npvb6g7l'""") # column break
    frappe.db.sql("""UPDATE `tabWeb Form Field` SET idx=12 WHERE parent='job-application' AND fieldname='upper_range'""")
    frappe.db.sql("""UPDATE `tabWeb Form Field` SET idx=13 WHERE parent='job-application' AND fieldname='currency'""")
    
    # Also delete the second column break just in case to clean it up
    frappe.db.sql("""DELETE FROM `tabWeb Form Field` WHERE parent='job-application' AND name='i3nig3jo3b'""")
    
    # 2. Update the client script to parse job_title correctly
    web_form = frappe.get_doc("Web Form", "job-application")
    
    new_script = """
frappe.ready(function() {
    frappe.web_form.after_load = () => {
        let job_title = frappe.web_form.doc.job_title || frappe.utils.get_query_params().job_title;
        console.log("Job Title for questions:", job_title);

        if (job_title) {
            frappe.call({
                method: 'cityscene_erp.api.recruitment.get_job_questions',
                args: {
                    job_title: job_title
                },
                callback: function(r) {
                    if (r.message && r.message.length > 0) {
                        render_questions(r.message);
                    }
                }
            });
        }

        function render_questions(questions) {
            let container = $('<div id="custom_questions_container" style="margin-top: 30px;"><h4>Job Specific Questions</h4></div>');
            $('.web-form-wrapper').append(container);
            window.custom_job_questions = questions;

            questions.forEach((q, idx) => {
                let field_html = `<div class="form-group" style="margin-bottom: 15px;">
                    <label>${q.question} ${q.mandatory ? '<span class="text-danger">*</span>' : ''}</label>
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
                        field_html += `<option value="${opt}">${opt}</option>`;
                    });
                    field_html += `</select>`;
                } else if (q.question_type === 'Check') {
                    field_html += `<br><input type="checkbox" class="custom-q-input" data-idx="${idx}"> Yes`;
                }
                field_html += `</div>`;
                container.append(field_html);
            });
        }

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
    };
});
"""
    web_form.client_script = new_script
    web_form.save(ignore_permissions=True)
    frappe.db.commit()

if __name__ == "__main__":
    execute()
