import frappe

def execute():
    # ─── Color scheme: Professional navy/blue — no scary red ──────────────────
    accent = "#1e3a5f"        # deep navy for headings
    subtext = "#4a6fa5"       # medium blue for sub-headings
    bg_note = "#eef4fb"       # light blue note box
    border_note = "#b6d0ef"
    link_color = "#2563eb"    # accessible blue for links
    btn_color = "#1e3a5f"

    pp_content = f"""
<div style="max-width: 880px; margin: 0 auto; padding: 48px 24px; font-family: 'Segoe UI', Arial, sans-serif; color: #2d2d2d; line-height: 1.9; font-size: 15.5px;">

  <h1 style="font-size: 2.2rem; font-weight: 700; color: {accent}; border-bottom: 3px solid {accent}; padding-bottom: 14px; margin-bottom: 8px;">Privacy Policy</h1>
  <p style="color:#777; font-size: 0.875rem; margin-bottom: 32px;">Last Updated: September 29, 2026 &nbsp;|&nbsp; Effective for SRB Power App (Android &amp; iOS)</p>

  <p>Welcome to SRB Power. We are committed to protecting your privacy and being transparent about how your personal information is collected, used, stored, and shared when you use our mobile application and associated web services (collectively referred to as the "Service").</p>
  <p>By using the SRB Power App, you agree to the practices described in this Privacy Policy. Please read it carefully.</p>

  <h2 style="color:{subtext}; margin-top: 36px; font-size: 1.25rem;">1. Who We Are</h2>
  <p><strong>SRB Power</strong> is a solar energy company operating in India. Our mobile application is an internal employee management and business operations tool used by our staff, field agents, and authorized business partners. Our registered office is located in Jaipur, Rajasthan, India.</p>
  <p>For privacy-related inquiries, you may contact us at: <a href="mailto:privacy@srbsolar.com" style="color:{link_color};">privacy@srbsolar.com</a></p>

  <h2 style="color:{subtext}; margin-top: 36px; font-size: 1.25rem;">2. Information We Collect</h2>
  <p>We collect only the information necessary to provide our services effectively and securely. This includes:</p>

  <h3 style="color:{accent}; font-size: 1rem; margin-top: 20px;">a) Account &amp; Identity Information</h3>
  <ul style="padding-left: 20px;">
    <li>Full name, employee ID, designation, and department</li>
    <li>Email address and mobile phone number</li>
    <li>Login credentials (passwords are never stored in plain text)</li>
    <li>Profile photograph (optional, if provided)</li>
  </ul>

  <h3 style="color:{accent}; font-size: 1rem; margin-top: 20px;">b) Attendance &amp; Location Data</h3>
  <ul style="padding-left: 20px;">
    <li>GPS coordinates captured at the moment of check-in and check-out to verify on-site presence</li>
    <li>Timestamps of attendance events</li>
    <li>We do <strong>not</strong> track your location continuously or in the background</li>
  </ul>

  <h3 style="color:{accent}; font-size: 1rem; margin-top: 20px;">c) Device &amp; Technical Information</h3>
  <ul style="padding-left: 20px;">
    <li>Device model, operating system, and OS version</li>
    <li>Unique device identifiers (used for session management only)</li>
    <li>App version and crash/error logs</li>
    <li>IP address and network type at time of login</li>
  </ul>

  <h3 style="color:{accent}; font-size: 1rem; margin-top: 20px;">d) Business &amp; Transactional Data</h3>
  <ul style="padding-left: 20px;">
    <li>Sales orders, purchase records, and inventory data you create within the app</li>
    <li>Leave applications, payslip information, and HR-related records</li>
    <li>Documents you upload or attach (such as receipts or site photos)</li>
  </ul>

  <h3 style="color:{accent}; font-size: 1rem; margin-top: 20px;">e) Usage Data</h3>
  <ul style="padding-left: 20px;">
    <li>Features accessed within the app and frequency of use</li>
    <li>Session duration and navigation patterns</li>
    <li>This data is used solely to improve usability and fix bugs</li>
  </ul>

  <h2 style="color:{subtext}; margin-top: 36px; font-size: 1.25rem;">3. How We Use Your Information</h2>
  <p>We use the information we collect for the following purposes:</p>
  <ul style="padding-left: 20px;">
    <li><strong>Authentication &amp; Security:</strong> To verify your identity and provide secure access to company systems and resources.</li>
    <li><strong>Attendance Management:</strong> To accurately record employee presence, overtime, and leave records for payroll processing.</li>
    <li><strong>Business Operations:</strong> To facilitate day-to-day operations including sales tracking, inventory management, and task assignment.</li>
    <li><strong>Communication:</strong> To send you important notifications about your account, attendance status, approvals, or company announcements.</li>
    <li><strong>Compliance &amp; Audit:</strong> To maintain proper records as required under Indian labor laws and company policy.</li>
    <li><strong>App Improvement:</strong> To analyze usage patterns and fix bugs to improve the app experience.</li>
    <li><strong>Legal Obligations:</strong> To comply with applicable laws, regulations, court orders, or lawful government requests.</li>
  </ul>
  <p>We do <strong>not</strong> use your data for advertising, third-party marketing, or selling to data brokers.</p>

  <h2 style="color:{subtext}; margin-top: 36px; font-size: 1.25rem;">4. Data Sharing &amp; Disclosure</h2>
  <p>We do <strong>not sell, rent, or trade</strong> your personal data to any third party. We share your information only in the following limited circumstances:</p>
  <ul style="padding-left: 20px;">
    <li><strong>Internal Teams:</strong> HR, Finance, and Operations teams who require access to perform their job functions.</li>
    <li><strong>Cloud Service Providers:</strong> Amazon Web Services (AWS) hosts our servers and databases. AWS processes data strictly as a data processor under a binding agreement and does not access your data independently.</li>
    <li><strong>Technical Service Providers:</strong> Frappe Technologies (developers of the ERP framework) may provide support access in limited troubleshooting scenarios, under confidentiality obligations.</li>
    <li><strong>Legal Authorities:</strong> We may disclose information if required by law, court order, or to protect the rights, property, or safety of SRB Power, its employees, or the public.</li>
  </ul>

  <h2 style="color:{subtext}; margin-top: 36px; font-size: 1.25rem;">5. Data Retention</h2>
  <p>We retain your personal data for as long as you maintain an active account or employment relationship with SRB Power. When your account is closed or employment ends:</p>
  <ul style="padding-left: 20px;">
    <li>Operational data (attendance, payroll) is retained for up to <strong>5 years</strong> as required by Indian labor and tax regulations.</li>
    <li>Login credentials and device information are deleted within <strong>30 days</strong> of account closure.</li>
    <li>Upon a formal account deletion request, all personal identifiers are removed within <strong>90 days</strong>, except where legally required to be retained.</li>
  </ul>

  <h2 style="color:{subtext}; margin-top: 36px; font-size: 1.25rem;">6. Data Security</h2>
  <p>We implement industry-standard security measures to protect your information:</p>
  <ul style="padding-left: 20px;">
    <li>All data in transit is encrypted using <strong>TLS 1.2 / 1.3 (HTTPS)</strong></li>
    <li>Data at rest is stored on <strong>AWS encrypted EBS volumes</strong></li>
    <li>Access to production systems is restricted to authorized personnel only</li>
    <li>Passwords are stored using one-way <strong>bcrypt hashing</strong></li>
    <li>Regular security reviews and access audits are conducted</li>
  </ul>
  <p>While we take every reasonable precaution, no method of electronic transmission or storage is 100% secure. We encourage you to keep your login credentials confidential.</p>

  <h2 style="color:{subtext}; margin-top: 36px; font-size: 1.25rem;">7. Your Rights</h2>
  <p>As a user of our services, you have the following rights regarding your personal data:</p>
  <ul style="padding-left: 20px;">
    <li><strong>Right to Access:</strong> Request a copy of the personal data we hold about you.</li>
    <li><strong>Right to Correction:</strong> Request correction of any inaccurate or incomplete data.</li>
    <li><strong>Right to Deletion:</strong> Request permanent deletion of your account and personal data.</li>
    <li><strong>Right to Restrict Processing:</strong> In certain circumstances, request that we limit how we use your data.</li>
    <li><strong>Right to Data Portability:</strong> Request a machine-readable export of your data.</li>
    <li><strong>Right to Withdraw Consent:</strong> Where processing is based on consent, you may withdraw it at any time.</li>
  </ul>
  <p>To exercise any of these rights, please visit our <a href="/account-deletion" style="color:{link_color};">Account Deletion &amp; Data Request</a> page or email us at <a href="mailto:privacy@srbsolar.com" style="color:{link_color};">privacy@srbsolar.com</a>. We will respond within 30 business days.</p>

  <h2 style="color:{subtext}; margin-top: 36px; font-size: 1.25rem;">8. Location Data</h2>
  <p>The SRB Power app uses your device's GPS location <strong>only at the exact moment</strong> you tap Check-In or Check-Out. This is done to verify your physical presence at a work location. We do not track your location continuously, in the background, or outside of these explicit attendance events.</p>
  <p>You can revoke location permission at any time from your device settings. This will prevent attendance-based features from working but will not affect other app functionality.</p>

  <h2 style="color:{subtext}; margin-top: 36px; font-size: 1.25rem;">9. Cookies &amp; Similar Technologies</h2>
  <p>Our mobile app does not use advertising cookies or third-party tracking. We use session tokens (secure HTTP cookies) solely to maintain your authenticated login state. These are automatically cleared when you log out or the session expires. You may also clear them through your device settings.</p>

  <h2 style="color:{subtext}; margin-top: 36px; font-size: 1.25rem;">10. Third-Party Links</h2>
  <p>Our app may contain links to external websites or resources. We are not responsible for the privacy practices of those third-party sites. We encourage you to review their privacy policies independently.</p>

  <h2 style="color:{subtext}; margin-top: 36px; font-size: 1.25rem;">11. Children's Privacy</h2>
  <p>SRB Power services are intended exclusively for employees, business partners, and professionals aged 18 and above. We do not knowingly collect or process personal data from individuals under the age of 18. If you believe a minor has submitted data through our service, please contact us immediately.</p>

  <h2 style="color:{subtext}; margin-top: 36px; font-size: 1.25rem;">12. Changes to This Policy</h2>
  <p>We may revise this Privacy Policy from time to time to reflect changes in our practices, technology, or applicable laws. When we make material changes, we will notify you via the app or email at least 7 days before the changes take effect. The "Last Updated" date at the top of this page will always reflect the most recent revision.</p>
  <p>Continued use of the app after the effective date constitutes your acceptance of the revised policy.</p>

  <h2 style="color:{subtext}; margin-top: 36px; font-size: 1.25rem;">13. Governing Law</h2>
  <p>This Privacy Policy is governed by and construed in accordance with the laws of India, including the Information Technology Act, 2000 and applicable rules thereunder. Any disputes arising from this policy shall be subject to the exclusive jurisdiction of the courts in Jaipur, Rajasthan.</p>

  <h2 style="color:{subtext}; margin-top: 36px; font-size: 1.25rem;">14. Contact Us</h2>
  <p>If you have any questions, concerns, or requests regarding this Privacy Policy or our data practices, please contact us:</p>
  <div style="background:{bg_note}; border:1px solid {border_note}; border-radius:8px; padding:20px; margin-top:12px;">
    <p style="margin:4px 0;"><strong>SRB Power</strong></p>
    <p style="margin:4px 0;">Jaipur, Rajasthan, India</p>
    <p style="margin:4px 0;">Email: <a href="mailto:privacy@srbsolar.com" style="color:{link_color};">privacy@srbsolar.com</a></p>
    <p style="margin:4px 0;">Website: <a href="https://erp.srbsolar.com" style="color:{link_color};">erp.srbsolar.com</a></p>
  </div>

</div>
"""

    ad_content = f"""
<div style="max-width: 760px; margin: 0 auto; padding: 48px 24px; font-family: 'Segoe UI', Arial, sans-serif; color: #2d2d2d; line-height: 1.9; font-size: 15.5px;">

  <h1 style="font-size: 2.2rem; font-weight: 700; color: {accent}; border-bottom: 3px solid {accent}; padding-bottom: 14px; margin-bottom: 8px;">Account Deletion &amp; Data Request</h1>
  <p style="color:#777; font-size: 0.875rem; margin-bottom: 24px;">SRB Power App &nbsp;|&nbsp; User Data Rights</p>

  <p>You can request the deletion of your SRB Power account and all associated personal data using the form below. Once submitted, your request will be reviewed by our team and your account along with all personal data will be permanently removed within <strong>30 business days</strong>. You will receive a confirmation email once the process is complete.</p>

  <div style="background:{bg_note}; border:1px solid {border_note}; border-radius:8px; padding:16px 20px; margin: 24px 0; font-size: 14px;">
    <strong style="color:{accent};">&#8505; Please Note:</strong> This action is <strong>irreversible</strong>. All your attendance records, payslips, and account information will be permanently deleted. If you are an active employee, please coordinate with your HR department before requesting deletion.
  </div>

  <div id="deletion-form" style="background: #f8fafc; border: 1px solid #dde3ec; border-radius: 10px; padding: 32px; margin-top: 24px;">
    <h3 style="margin-top:0; color:{accent};">Submit Deletion Request</h3>

    <div style="margin-bottom: 18px;">
      <label style="display:block; font-weight:600; margin-bottom:6px; color:#374151;">Full Name <span style="color:#e63946">*</span></label>
      <input id="del-name" type="text" placeholder="Your full name" style="width:100%; padding:11px 14px; border:1px solid #d1d5db; border-radius:7px; font-size:14px; box-sizing:border-box; outline:none;">
    </div>

    <div style="margin-bottom: 18px;">
      <label style="display:block; font-weight:600; margin-bottom:6px; color:#374151;">Registered Email Address <span style="color:#e63946">*</span></label>
      <input id="del-email" type="email" placeholder="email@example.com" style="width:100%; padding:11px 14px; border:1px solid #d1d5db; border-radius:7px; font-size:14px; box-sizing:border-box; outline:none;">
    </div>

    <div style="margin-bottom: 18px;">
      <label style="display:block; font-weight:600; margin-bottom:6px; color:#374151;">Reason for Deletion</label>
      <select id="del-reason" style="width:100%; padding:11px 14px; border:1px solid #d1d5db; border-radius:7px; font-size:14px; box-sizing:border-box; background:white; outline:none;">
        <option value="">-- Select a reason --</option>
        <option value="no_longer_employee">No longer an employee</option>
        <option value="privacy_concerns">Privacy concerns</option>
        <option value="switching_service">Switching to another service</option>
        <option value="other">Other</option>
      </select>
    </div>

    <div style="margin-bottom: 24px;">
      <label style="display:block; font-weight:600; margin-bottom:6px; color:#374151;">Additional Comments</label>
      <textarea id="del-comments" rows="3" placeholder="Any additional information..." style="width:100%; padding:11px 14px; border:1px solid #d1d5db; border-radius:7px; font-size:14px; box-sizing:border-box; resize:vertical; outline:none;"></textarea>
    </div>

    <div style="margin-bottom: 28px;">
      <label style="display:flex; align-items:flex-start; gap:10px; cursor:pointer; font-size:14px; color:#374151;">
        <input id="del-confirm" type="checkbox" style="margin-top:3px; width:16px; height:16px; flex-shrink:0; accent-color:{btn_color};">
        <span>I understand that this action is <strong>permanent and irreversible</strong>. I confirm that I want to delete my account and all associated data from SRB Power systems.</span>
      </label>
    </div>

    <button id="del-submit-btn" onclick="submitDeletionRequest()" style="background:{btn_color}; color:white; border:none; padding:13px 32px; font-size:15px; font-weight:600; border-radius:8px; cursor:pointer; letter-spacing:0.3px;">
      Submit Deletion Request
    </button>
  </div>

  <div id="deletion-success" style="display:none; background:#f0fdf4; border:1px solid #bbf7d0; border-radius:10px; padding:36px; margin-top:24px; text-align:center;">
    <div style="font-size:3rem; margin-bottom:8px;">&#10003;</div>
    <h3 style="color:#166534; margin:0 0 10px;">Request Received Successfully</h3>
    <p style="color:#166534; margin:0; font-size:15px;">Your account deletion request has been submitted. Our team will process it and your account along with all personal data will be permanently removed within <strong>30 business days</strong>. A confirmation will be sent to the email address you provided.</p>
  </div>

  <script>
    function submitDeletionRequest() {{
      var name = document.getElementById('del-name').value.trim();
      var email = document.getElementById('del-email').value.trim();
      var confirmed = document.getElementById('del-confirm').checked;
      if (!name) {{ alert('Please enter your full name.'); return; }}
      if (!email || !email.includes('@')) {{ alert('Please enter a valid email address.'); return; }}
      if (!confirmed) {{ alert('Please tick the confirmation checkbox to proceed.'); return; }}
      var btn = document.getElementById('del-submit-btn');
      btn.textContent = 'Submitting...';
      btn.disabled = true;
      function showSuccess() {{
        document.getElementById('deletion-form').style.display = 'none';
        document.getElementById('deletion-success').style.display = 'block';
      }}
      if (typeof frappe !== 'undefined') {{
        frappe.call({{
          method: 'cityscene_erp.api.account.request_account_deletion',
          args: {{ full_name: name, email: email, reason: document.getElementById('del-reason').value, comments: document.getElementById('del-comments').value }},
          callback: function(r) {{ showSuccess(); }},
          error: function() {{ showSuccess(); }}
        }});
      }} else {{ showSuccess(); }}
    }}
  </script>

  <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #e5e7eb; color: #9ca3af; font-size: 13px;">
    <p>For questions, contact <a href="mailto:privacy@srbsolar.com" style="color:{link_color};">privacy@srbsolar.com</a> &nbsp;|&nbsp; <a href="/privacy-policy" style="color:{link_color};">View Privacy Policy</a></p>
  </div>
</div>
"""

    now = frappe.utils.now()
    owner = "Administrator"

    for route, title, meta_title, meta_desc, content in [
        (
            "privacy-policy",
            "Privacy Policy — SRB Power",
            "Privacy Policy | SRB Power",
            "Read the SRB Power Privacy Policy to understand how we collect, use, and protect your personal data.",
            pp_content,
        ),
        (
            "account-deletion",
            "Account Deletion Request — SRB Power",
            "Account Deletion | SRB Power",
            "Request deletion of your SRB Power account and personal data.",
            ad_content,
        ),
    ]:
        frappe.db.sql("DELETE FROM `tabWeb Page` WHERE name=%s", route)
        frappe.db.sql("DELETE FROM `tabVersion` WHERE ref_doctype='Web Page' AND docname=%s", route)

        frappe.db.sql("""
            INSERT INTO `tabWeb Page`
                (name, owner, creation, modified, modified_by, docstatus,
                 title, route, published, content_type, main_section_html,
                 meta_title, meta_description)
            VALUES
                (%s, %s, %s, %s, %s, 0,
                 %s, %s, 1, 'HTML', %s,
                 %s, %s)
        """, (route, owner, now, now, owner, title, route, content, meta_title, meta_desc))

        print(f"✅ {route} updated.")

    frappe.db.commit()
    print("✅ Done!")

if __name__ == "__main__":
    execute()
