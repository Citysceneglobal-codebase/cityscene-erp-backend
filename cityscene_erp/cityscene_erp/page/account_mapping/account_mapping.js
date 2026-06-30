frappe.pages['account-mapping'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Account Mapping Manager',
		single_column: true
	});

	let $main = $(page.main);

	$main.html(`
		<div class="account-mapping-page" style="padding: 15px;">
			<div class="row mb-4" style="margin-bottom: 15px;">
				<div class="col-md-3">
					<label>Company</label>
					<div id="filter-company"></div>
				</div>
				<div class="col-md-3">
					<label>Party Type</label>
					<div id="filter-party-type"></div>
				</div>
				<div class="col-md-3">
					<label>Status</label>
					<div id="filter-status"></div>
				</div>
				<div class="col-md-3" style="padding-top: 22px;">
					<button class="btn btn-primary btn-sm" id="btn-load">Load</button>
				</div>
			</div>

			<div class="table-responsive">
				<table class="table table-bordered table-hover" id="mapping-table">
					<thead>
						<tr>
							<th>Party</th>
							<th>Group</th>
							<th>Dedicated Account</th>
							<th>Status</th>
							<th>Action</th>
						</tr>
					</thead>
					<tbody>
						<tr><td colspan="5" class="text-center text-muted">Click Load to view mapping data</td></tr>
					</tbody>
				</table>
			</div>
		</div>
	`);

	// Create filter controls
	let company_field = frappe.ui.form.make_control({
		df: {
			fieldtype: 'Link',
			options: 'Company',
			fieldname: 'company',
			placeholder: 'Select Company',
			default: frappe.defaults.get_user_default('Company')
		},
		parent: $main.find('#filter-company'),
		render_input: true
	});
	company_field.set_value(frappe.defaults.get_user_default('Company') || '');

	let party_type_field = frappe.ui.form.make_control({
		df: {
			fieldtype: 'Select',
			options: '\nCustomer\nSupplier',
			fieldname: 'party_type',
			placeholder: 'Select Party Type',
			default: 'Customer'
		},
		parent: $main.find('#filter-party-type'),
		render_input: true
	});
	party_type_field.set_value('Customer');

	let status_field = frappe.ui.form.make_control({
		df: {
			fieldtype: 'Select',
			options: '\nAll\nMapped\nUnmapped',
			fieldname: 'status',
			placeholder: 'Filter Status',
			default: 'All'
		},
		parent: $main.find('#filter-status'),
		render_input: true
	});
	status_field.set_value('All');

	$main.find('#btn-load').on('click', function() {
		load_data();
	});

	function load_data() {
		let party_type = party_type_field.get_value();
		let company = company_field.get_value();
		let status = status_field.get_value();

		if (!party_type || !company) {
			frappe.msgprint('Please select Company and Party Type.');
			return;
		}

		frappe.call({
			method: 'cityscene_erp.cityscene_erp.page.account_mapping.account_mapping.get_mapping_data',
			args: {
				party_type: party_type,
				company: company,
				status: status || 'All'
			},
			callback: function(r) {
				render_table(r.message || [], party_type, company);
			}
		});
	}

	function render_table(data, party_type, company) {
		let tbody = $main.find('#mapping-table tbody');
		tbody.empty();

		if (data.length > 0) {
			data.forEach(function(row) {
				let status_badge = row.status === 'Mapped'
					? '<span class="badge" style="background-color: #28a745; color: white;">✅ Mapped</span>'
					: '<span class="badge" style="background-color: #dc3545; color: white;">❌ Not Mapped</span>';

				let account_display = row.account
					? '<a href="/app/account/' + row.account + '">' + row.account + '</a>'
					: '<span class="text-muted">—</span>';

				let action_btn = row.status === 'Mapped'
					? ''
					: '<button class="btn btn-xs btn-primary btn-create" data-party="' + row.party + '">Create Account</button>';

				let tr = $('<tr>' +
					'<td><a href="/app/' + party_type.toLowerCase() + '/' + row.party + '">' + row.party + '</a></td>' +
					'<td>' + (row.group || '') + '</td>' +
					'<td>' + account_display + '</td>' +
					'<td>' + status_badge + '</td>' +
					'<td>' + action_btn + '</td>' +
				'</tr>').appendTo(tbody);

				tr.find('.btn-create').on('click', function() {
					let party = $(this).attr('data-party');
					prompt_create_account(party_type, party, company, function() { load_data(); });
				});
			});
		} else {
			tbody.html('<tr><td colspan="5" class="text-center text-muted">No records found</td></tr>');
		}
	}

	function prompt_create_account(party_type, party, company, callback) {
		let d = new frappe.ui.Dialog({
			title: __('Create Dedicated Ledger Account'),
			fields: [
				{
					label: 'Message',
					fieldtype: 'HTML',
					options: '<p><b>' + party + '</b> does not have a dedicated ledger in ' + company + '.</p><p>Please select a Parent Account to create it automatically.</p>'
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
								'company': company,
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
						company: company,
						parent_account: values.parent_account
					},
					callback: function(r) {
						if (r.message) {
							frappe.show_alert({message: __('Account created successfully'), indicator: 'green'});
							d.hide();
							if (callback) callback();
						}
					}
				});
			}
		});
		d.show();
	}
}