import frappe

def execute():
    scripts = [
        {
            "dt": "Sales Invoice",
            "module": "Accounts",
            "script": """
frappe.ui.form.on('Sales Invoice', {
    customer: function(frm) {
        if (!frm.doc.customer || !frm.doc.company) return;
        
        frappe.call({
            method: 'erpnext.accounts.party.get_party_account',
            args: {
                party_type: 'Customer',
                party: frm.doc.customer,
                company: frm.doc.company
            },
            callback: function(r) {
                if (r.message) {
                    frm.set_value('debit_to', r.message);
                } else {
                    prompt_create_account(frm, 'Customer', frm.doc.customer, 'debit_to');
                }
            }
        });
    },
    validate: function(frm) {
        if (frm.doc.customer && frm.doc.debit_to) {
            // Simple check: the account name should start with customer name or we block
            // Actually, we can check if it's in the customer's accounts child table
            // But let's just ensure they don't use generic accounts.
            if (frm.doc.debit_to.indexOf('Debtors - ') > -1 && frm.doc.debit_to.indexOf(frm.doc.customer) === -1) {
                frappe.msgprint(__('You must use a dedicated Customer Ledger. Please clear the Customer field and reselect it to auto-create their ledger.'));
                frappe.validated = false;
            }
        }
    }
});

function prompt_create_account(frm, party_type, party, fieldname) {
    let d = new frappe.ui.Dialog({
        title: __('Create Dedicated Ledger Account'),
        fields: [
            {
                label: 'Message',
                fieldtype: 'HTML',
                options: `<p><b>${party}</b> does not have a dedicated ledger in ${frm.doc.company}.</p><p>Please select a Parent Account to create it automatically.</p>`
            },
            {
                label: 'Parent Account',
                fieldname: 'parent_account',
                fieldtype: 'Link',
                options: 'Account',
                reqd: 1,
                get_query: function() {
                    return {
                        filters: {
                            'is_group': 1,
                            'company': frm.doc.company,
                            'account_type': party_type === 'Customer' ? 'Receivable' : 'Payable'
                        }
                    };
                }
            }
        ],
        primary_action_label: 'Create Account',
        primary_action: function(values) {
            frappe.call({
                method: 'cityscene_erp.api.account_manager.auto_create_party_account',
                args: {
                    party_type: party_type,
                    party: party,
                    company: frm.doc.company,
                    parent_account: values.parent_account
                },
                callback: function(r) {
                    if (r.message) {
                        frm.set_value(fieldname, r.message);
                        frappe.show_alert({message: __('Account created successfully'), indicator: 'green'});
                        d.hide();
                    }
                }
            });
        }
    });
    
    // Prevent closing the dialog without creating an account
    d.get_close_btn().on('click', function() {
        frm.set_value(party_type.toLowerCase(), '');
        frm.set_value(fieldname, '');
    });
    
    d.show();
}
"""
        },
        {
            "dt": "Purchase Invoice",
            "module": "Accounts",
            "script": """
frappe.ui.form.on('Purchase Invoice', {
    supplier: function(frm) {
        if (!frm.doc.supplier || !frm.doc.company) return;
        
        frappe.call({
            method: 'erpnext.accounts.party.get_party_account',
            args: {
                party_type: 'Supplier',
                party: frm.doc.supplier,
                company: frm.doc.company
            },
            callback: function(r) {
                if (r.message) {
                    frm.set_value('credit_to', r.message);
                } else {
                    prompt_create_account(frm, 'Supplier', frm.doc.supplier, 'credit_to');
                }
            }
        });
    },
    validate: function(frm) {
        if (frm.doc.supplier && frm.doc.credit_to) {
            if (frm.doc.credit_to.indexOf('Creditors - ') > -1 && frm.doc.credit_to.indexOf(frm.doc.supplier) === -1) {
                frappe.msgprint(__('You must use a dedicated Supplier Ledger. Please clear the Supplier field and reselect it to auto-create their ledger.'));
                frappe.validated = false;
            }
        }
    }
});

function prompt_create_account(frm, party_type, party, fieldname) {
    let d = new frappe.ui.Dialog({
        title: __('Create Dedicated Ledger Account'),
        fields: [
            {
                label: 'Message',
                fieldtype: 'HTML',
                options: `<p><b>${party}</b> does not have a dedicated ledger in ${frm.doc.company}.</p><p>Please select a Parent Account to create it automatically.</p>`
            },
            {
                label: 'Parent Account',
                fieldname: 'parent_account',
                fieldtype: 'Link',
                options: 'Account',
                reqd: 1,
                get_query: function() {
                    return {
                        filters: {
                            'is_group': 1,
                            'company': frm.doc.company,
                            'account_type': party_type === 'Customer' ? 'Receivable' : 'Payable'
                        }
                    };
                }
            }
        ],
        primary_action_label: 'Create Account',
        primary_action: function(values) {
            frappe.call({
                method: 'cityscene_erp.api.account_manager.auto_create_party_account',
                args: {
                    party_type: party_type,
                    party: party,
                    company: frm.doc.company,
                    parent_account: values.parent_account
                },
                callback: function(r) {
                    if (r.message) {
                        frm.set_value(fieldname, r.message);
                        frappe.show_alert({message: __('Account created successfully'), indicator: 'green'});
                        d.hide();
                    }
                }
            });
        }
    });
    
    d.get_close_btn().on('click', function() {
        frm.set_value(party_type.toLowerCase(), '');
        frm.set_value(fieldname, '');
    });
    
    d.show();
}
"""
        },
        {
            "dt": "Payment Entry",
            "module": "Accounts",
            "script": """
frappe.ui.form.on('Payment Entry', {
    party: function(frm) {
        if (!frm.doc.party || !frm.doc.party_type || !frm.doc.company) return;
        
        frappe.call({
            method: 'erpnext.accounts.party.get_party_account',
            args: {
                party_type: frm.doc.party_type,
                party: frm.doc.party,
                company: frm.doc.company
            },
            callback: function(r) {
                if (r.message) {
                    frm.set_value('party_account', r.message);
                } else {
                    prompt_create_account(frm, frm.doc.party_type, frm.doc.party, 'party_account');
                }
            }
        });
    }
});

function prompt_create_account(frm, party_type, party, fieldname) {
    let d = new frappe.ui.Dialog({
        title: __('Create Dedicated Ledger Account'),
        fields: [
            {
                label: 'Message',
                fieldtype: 'HTML',
                options: `<p><b>${party}</b> does not have a dedicated ledger in ${frm.doc.company}.</p><p>Please select a Parent Account to create it automatically.</p>`
            },
            {
                label: 'Parent Account',
                fieldname: 'parent_account',
                fieldtype: 'Link',
                options: 'Account',
                reqd: 1,
                get_query: function() {
                    return {
                        filters: {
                            'is_group': 1,
                            'company': frm.doc.company,
                            'account_type': party_type === 'Customer' ? 'Receivable' : 'Payable'
                        }
                    };
                }
            }
        ],
        primary_action_label: 'Create Account',
        primary_action: function(values) {
            frappe.call({
                method: 'cityscene_erp.api.account_manager.auto_create_party_account',
                args: {
                    party_type: party_type,
                    party: party,
                    company: frm.doc.company,
                    parent_account: values.parent_account
                },
                callback: function(r) {
                    if (r.message) {
                        frm.set_value(fieldname, r.message);
                        frappe.show_alert({message: __('Account created successfully'), indicator: 'green'});
                        d.hide();
                    }
                }
            });
        }
    });
    
    d.get_close_btn().on('click', function() {
        frm.set_value('party', '');
        frm.set_value(fieldname, '');
    });
    
    d.show();
}
"""
        }
    ]
    
    for s in scripts:
        name = f"Auto-Map {s['dt']} Account"
        if frappe.db.exists("Client Script", name):
            doc = frappe.get_doc("Client Script", name)
            doc.script = s["script"]
            doc.save()
        else:
            doc = frappe.get_doc({
                "doctype": "Client Script",
                "dt": s["dt"],
                "name": name,
                "script": s["script"],
                "module": "Accounts",
                "enabled": 1
            })
            doc.insert()
            
    frappe.db.commit()
    print("Client Scripts Installed Successfully")
