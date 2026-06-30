frappe.pages['party-accounting'].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Party Accounting Dashboard',
		single_column: true
	});

	let $main = $(page.main);
	let current_data = null;
	let PAGE_SIZE = 20;

	// ─── PAGE HTML ───
	$main.html(`
		<div class="party-accounting-page" style="padding: 15px;">
			<!-- FILTERS ROW -->
			<div class="row" style="margin-bottom: 15px; padding: 10px; background: #f8f9fa; border-radius: 8px;">
				<div class="col-md-2"><label>Company</label><div id="filter-company"></div></div>
				<div class="col-md-2"><label>Account</label><div id="filter-account"></div></div>
				<div class="col-md-2"><label>Party Type</label><div id="filter-party-type"></div></div>
				<div class="col-md-2"><label>Party</label><div id="filter-party"></div></div>
				<div class="col"><label>From</label><div id="filter-from-date"></div></div>
				<div class="col"><label>To Date</label><div id="filter-to-date"></div></div>
				<div class="col-md-1"><label>&nbsp;</label><button class="btn btn-primary btn-sm" id="btn-reload-data" style="width: 100%; margin-top: 20px;">Load</button></div>
			</div>

			<!-- COMPANY OVERVIEW -->
			<div id="company-overview"></div>

			<!-- PARTY VIEW -->
			<div id="party-view" style="display:none;">
				<div class="row" id="summary-cards" style="margin-bottom: 20px;"></div>

				<div class="row" style="margin-bottom: 15px; padding: 15px; background: #f5f7fa; border-radius: 8px;">
					<div class="col-md-6">
						<h3 id="party-name-display" style="margin: 0;"></h3>
						<p class="text-muted" style="margin: 5px 0 0;">Dedicated Ledger: <b id="party-account-display"></b></p>
						<p id="dual-party-info" style="display:none; margin: 5px 0 0;"></p>
					</div>
					<div class="col-md-6 text-right">
						<h3 id="party-balance-display" style="margin: 0;"></h3>
						<p class="text-muted" style="margin: 5px 0 0;">Total Outstanding</p>
					</div>
				</div>

				<div id="chart-area" style="margin-bottom: 20px; padding: 15px; background: white; border: 1px solid #e8e8e8; border-radius: 8px;">
					<h5>Payment & Invoice Trend</h5>
					<div id="chart-container" style="height: 250px;"></div>
				</div>

				<!-- MANUAL TABS -->
				<div class="party-tabs-container">
					<div style="display:flex; border-bottom: 2px solid #dee2e6; margin-bottom: 0;">
						<div class="ptab active" data-tab="tab-unpaid" style="padding:10px 20px; cursor:pointer; border-bottom:2px solid #5e64ff; margin-bottom:-2px; font-weight:600;">Unpaid Invoices</div>
						<div class="ptab" data-tab="tab-uninvoiced" style="padding:10px 20px; cursor:pointer; margin-bottom:-2px;">Uninvoiced Orders</div>
						<div class="ptab" data-tab="tab-invoiced" style="padding:10px 20px; cursor:pointer; margin-bottom:-2px;">Invoiced Orders</div>
						<div class="ptab" data-tab="tab-payments" style="padding:10px 20px; cursor:pointer; margin-bottom:-2px;">Payments</div>
						<div class="ptab" data-tab="tab-journals" style="padding:10px 20px; cursor:pointer; margin-bottom:-2px;">Journal Entries</div>
						<div class="ptab" data-tab="tab-ledger" style="padding:10px 20px; cursor:pointer; margin-bottom:-2px;">General Ledger</div>
						<div class="ptab" data-tab="tab-other" style="padding:10px 20px; cursor:pointer; margin-bottom:-2px; display:none;" id="tab-other-btn">Other Side</div>
					</div>
					<div style="padding: 15px; background: white; border: 1px solid #dee2e6; border-top: none; border-radius: 0 0 8px 8px;">
						<div class="ptab-content" id="tab-unpaid"></div>
						<div class="ptab-content" id="tab-uninvoiced" style="display:none;"></div>
						<div class="ptab-content" id="tab-invoiced" style="display:none;"></div>
						<div class="ptab-content" id="tab-payments" style="display:none;"></div>
						<div class="ptab-content" id="tab-journals" style="display:none;"></div>
						<div class="ptab-content" id="tab-ledger" style="display:none;"></div>
						<div class="ptab-content" id="tab-other" style="display:none;"></div>
					</div>
				</div>
			</div>
		</div>
	`);

	// ─── MANUAL TAB SWITCHING ───
	$main.on('click', '.ptab', function () {
		let tab_id = $(this).data('tab');
		$main.find('.ptab').css({ 'border-bottom': 'none', 'font-weight': 'normal' }).removeClass('active');
		$(this).css({ 'border-bottom': '2px solid #5e64ff', 'font-weight': '600' }).addClass('active');
		$main.find('.ptab-content').hide();
		$main.find('#' + tab_id).show();
	});

	// ─── FILTER CONTROLS ───
	let company_field = _make_control($main.find('#filter-company'), {
		fieldtype: 'Link', options: 'Company', fieldname: 'company', placeholder: 'Company'
	});
	company_field.set_value(frappe.defaults.get_user_default('Company') || '');

	let party_type_field = _make_control($main.find('#filter-party-type'), {
		fieldtype: 'Select', options: '\nCustomer\nSupplier', fieldname: 'party_type', placeholder: 'Type'
	});
	party_type_field.set_value('Customer');

	let account_field = _make_control($main.find('#filter-account'), {
		fieldtype: 'Link', options: 'Account', fieldname: 'account', placeholder: 'Search Account'
	});

	let party_field = _make_control($main.find('#filter-party'), {
		fieldtype: 'Link', options: 'Customer', fieldname: 'party', placeholder: 'Leave blank for overview'
	});

	let from_date_field = _make_control($main.find('#filter-from-date'), { fieldtype: 'Date', fieldname: 'from_date', placeholder: 'From' });
	let to_date_field = _make_control($main.find('#filter-to-date'), { fieldtype: 'Date', fieldname: 'to_date', placeholder: 'To' });

	function _make_control(parent, df) {
		return frappe.ui.form.make_control({ df: df, parent: parent, render_input: true });
	}

	account_field.$input && account_field.$input.on('change', function () {
		let val = account_field.get_value();
		if (val && company_field.get_value()) {
			frappe.call({
				method: 'cityscene_erp.cityscene_erp.page.party_accounting.party_accounting.get_party_for_account',
				args: { account: val, company: company_field.get_value() },
				callback: function (r) {
					if (r.message && r.message.party) {
						party_type_field.set_value(r.message.party_type);
						setTimeout(() => party_field.set_value(r.message.party), 200);
					} else {
						party_field.set_value('');
					}
				}
			});
		}
	});

	party_type_field.$input && party_type_field.$input.on('change', function () {
		let val = party_type_field.get_value();
		if (val) { party_field.df.options = val; party_field.set_value(''); party_field.refresh(); }
	});

	$main.find('#btn-reload-data').on('click', function () {
		if (party_field.get_value() || account_field.get_value()) {
			load_party_data();
		} else if (company_field.get_value()) {
			load_company_overview();
		}
	});

	setTimeout(function () { if (company_field.get_value()) load_company_overview(); }, 500);


	// ═══════════════════════════════════════════
	// COMPANY OVERVIEW
	// ═══════════════════════════════════════════
	function load_company_overview() {
		let company = company_field.get_value();
		if (!company) return;
		let from_date = from_date_field.get_value();
		let to_date = to_date_field.get_value();

		$main.find('#party-view').hide();
		$main.find('#company-overview').show();
		frappe.call({
			method: 'cityscene_erp.cityscene_erp.page.party_accounting.party_accounting.get_company_overview',
			args: { company: company, from_date: from_date, to_date: to_date },
			freeze: true, freeze_message: 'Loading...',
			callback: function (r) { if (r.message) render_company_overview(r.message, company); }
		});
	}

	function render_company_overview(data, company) {
		let fmt = (v) => format_currency(v, frappe.defaults.get_default("currency"));
		$main.find('#company-overview').html(`
			<div class="row" style="margin-bottom: 20px;">
				${_card('Total Receivable', fmt(data.total_receivable), 'text-success', 'fa-arrow-down')}
				${_card('Total Payable', fmt(data.total_payable), 'text-danger', 'fa-arrow-up')}
				${_card('Uninvoiced SO', (data.uninvoiced_so.cnt || 0) + ' orders / ' + fmt(data.uninvoiced_so.amount || 0), 'text-warning', 'fa-file-text-o', null, 'card-so-modal')}
				${_card('Uninvoiced PO', (data.uninvoiced_po.cnt || 0) + ' orders / ' + fmt(data.uninvoiced_po.amount || 0), 'text-info', 'fa-file-text-o', null, 'card-po-modal')}
			</div>
			<div class="row">
				<div class="col-md-6">
					<div style="background:white; border:1px solid #e8e8e8; border-radius:8px; padding:15px; margin-bottom:15px;">
						<h5>Top 10 Outstanding Customers</h5>
						<table class="table table-sm table-hover"><thead><tr><th>Customer</th><th class="text-right">Outstanding</th></tr></thead>
						<tbody>${data.top_customers.map(c => '<tr><td><a href="#" class="party-link" data-party="' + c.party + '" data-type="Customer">' + c.party + '</a></td><td class="text-right text-danger">' + fmt(c.outstanding) + '</td></tr>').join('')}</tbody></table>
					</div>
				</div>
				<div class="col-md-6">
					<div style="background:white; border:1px solid #e8e8e8; border-radius:8px; padding:15px; margin-bottom:15px;">
						<h5>Top 10 Outstanding Suppliers</h5>
						<table class="table table-sm table-hover"><thead><tr><th>Supplier</th><th class="text-right">Outstanding</th></tr></thead>
						<tbody>${data.top_suppliers.map(s => '<tr><td><a href="#" class="party-link" data-party="' + s.party + '" data-type="Supplier">' + s.party + '</a></td><td class="text-right text-danger">' + fmt(s.outstanding) + '</td></tr>').join('')}</tbody></table>
					</div>
				</div>
			</div>
			<div style="background:white; border:1px solid #e8e8e8; border-radius:8px; padding:15px; margin-bottom:15px;">
				<h5>Recent Payments</h5>
				<table class="table table-sm table-hover"><thead><tr><th>Payment</th><th>Date</th><th>Party</th><th>Type</th><th class="text-right">Amount</th></tr></thead>
				<tbody>${data.recent_payments.map(p => '<tr><td><a href="/app/payment-entry/' + p.name + '">' + p.name + '</a></td><td>' + frappe.datetime.str_to_user(p.posting_date) + '</td><td><a href="#" class="party-link" data-party="' + p.party + '" data-type="' + (p.party_type || '') + '">' + p.party + '</a></td><td>' + p.payment_type + '</td><td class="text-right">' + fmt(p.paid_amount) + '</td></tr>').join('')}</tbody></table>
			</div>
			<div style="background:white; border:1px solid #e8e8e8; border-radius:8px; padding:15px;">
				<h5>Monthly Received vs Paid</h5>
				<div id="overview-chart-container" style="height:250px;"></div>
			</div>
		`);
		$main.find('.party-link').on('click', function (e) {
			e.preventDefault();
			let p = $(this).data('party'), t = $(this).data('type');
			
			from_date_field.set_value('');
			to_date_field.set_value('');
			
			let p1 = Promise.resolve();
			if (t && party_type_field.get_value() !== t) {
				// Explicitly update the options for the party link field
				party_field.df.options = t;
				party_field.refresh();
				p1 = party_type_field.set_value(t);
			}
			
			p1.then(() => {
				// wait a bit for frappe's internal field clear to finish
				setTimeout(() => {
					party_field.df.options = t || party_type_field.get_value();
					party_field.set_value(p).then(() => {
						load_party_data();
					});
				}, 200);
			});
		});

		// Modal for SO
		$main.find('.card-so-modal').on('click', function () {
			_show_uninvoiced_modal('Sales Order', data.uninvoiced_so_list, fmt);
		});

		// Modal for PO
		$main.find('.card-po-modal').on('click', function () {
			_show_uninvoiced_modal('Purchase Order', data.uninvoiced_po_list, fmt);
		});

		if (data.monthly_data && data.monthly_data.length) {
			try {
				new frappe.Chart('#overview-chart-container', {
					data: {
						labels: data.monthly_data.map(d => d.month), datasets: [
							{ name: 'Received', values: data.monthly_data.map(d => d.received || 0) },
							{ name: 'Paid', values: data.monthly_data.map(d => d.paid || 0) }
						]
					}, type: 'bar', height: 220, colors: ['#28a745', '#dc3545']
				});
			} catch (e) { }
		} else {
			$main.find('#overview-chart-container').html('<p class="text-muted text-center" style="padding-top: 50px;">No payment data found in selected period</p>');
		}
	}


	// ═══════════════════════════════════════════
	// PARTY DATA
	// ═══════════════════════════════════════════
	function load_party_data() {
		let party_type = party_type_field.get_value();
		let party = party_field.get_value();
		let account = account_field.get_value();
		let company = company_field.get_value();
		let from_date = from_date_field.get_value();
		let to_date = to_date_field.get_value();

		if (!company) return frappe.msgprint("Please select Company");
		if (!party && !account) return;

		$main.find('#company-overview').hide();
		$main.find('#party-view').show();
		frappe.call({
			method: 'cityscene_erp.cityscene_erp.page.party_accounting.party_accounting.get_party_details',
			args: { party_type, party, company, from_date, to_date, account },
			freeze: true, freeze_message: 'Loading...',
			callback: function (r) {
				if (r.message) { current_data = r.message; render_party_view(r.message, party_type, party, company, account); }
			}
		});
	}

	function render_party_view(data, party_type, party, company, account) {
		let fmt = (v) => format_currency(v, frappe.defaults.get_default("currency"));
		let c = data.cards;

		$main.find('#summary-cards').html(
			_card('Outstanding', fmt(c.total_outstanding), 'text-danger', 'fa-exclamation-circle', c.unpaid_count + ' invoices') +
			_card('Pending Orders', fmt(c.total_orders_pending), 'text-warning', 'fa-clock-o', c.uninvoiced_count + ' orders') +
			_card('Total Paid', fmt(c.total_paid), 'text-success', 'fa-check-circle', c.payment_count + ' payments') +
			_card('Balance', fmt(Math.abs(data.balance)) + (data.balance >= 0 ? ' Dr' : ' Cr'), data.balance >= 0 ? 'text-success' : 'text-danger', 'fa-balance-scale')
		);

		$main.find('#party-name-display').text(party || account);
		$main.find('#party-account-display').html(data.party_account
			? '<a href="/app/account/' + data.party_account + '">' + data.party_account + '</a>'
			: '<span class="text-danger">No dedicated account mapped!</span>');

		if (data.is_dual && data.other_side) {
			$main.find('#dual-party-info').show().html('<span class="badge" style="background:#17a2b8;color:white;">Also a ' + data.other_side.party_type + '</span> Account: <b>' + (data.other_side.account || 'Not mapped') + '</b>');
			$main.find('#tab-other-btn').show();
			render_other_side(data.other_side, party, company, fmt);
		} else {
			$main.find('#dual-party-info').hide();
			$main.find('#tab-other-btn').hide();
		}

		render_unpaid_tab(data, party_type, party, company, fmt);
		render_uninvoiced_tab(data, party_type, party, company, fmt);
		render_invoiced_tab(data, party_type, party, company, fmt);
		render_payments_tab(data, party_type, party, company, fmt);
		render_journals_tab(data, fmt);
		render_ledger_tab(data, party_type, party, company, fmt);
		render_party_chart(data, party_type, fmt);

		// Reset to first tab
		$main.find('.ptab').css({ 'border-bottom': 'none', 'font-weight': 'normal' }).first().css({ 'border-bottom': '2px solid #5e64ff', 'font-weight': '600' });
		$main.find('.ptab-content').hide();
		$main.find('#tab-unpaid').show();
	}


	// ═══════════════════════════════════════════
	// TAB: UNPAID INVOICES (with filters + pagination)
	// ═══════════════════════════════════════════
	function render_unpaid_tab(data, party_type, party, company, fmt) {
		let all_invoices = data.all_invoices || data.unpaid_invoices || [];
		let inv_dt = party_type === 'Customer' ? 'Sales Invoice' : 'Purchase Invoice';
		let slug = inv_dt.toLowerCase().replace(/ /g, '-');

		let $tab = $main.find('#tab-unpaid');
		$tab.html(`
			<div class="row" style="margin-bottom:10px; align-items:center;">
				<div class="col-md-3">
					<button class="btn btn-primary btn-sm btn-new-invoice"><i class="fa fa-plus"></i> New ${inv_dt}</button>
				</div>
				<div class="col-md-3">
					<select class="form-control form-control-sm inv-status-filter">
						<option value="unpaid">Unpaid Only</option>
						<option value="all">All Invoices</option>
						<option value="paid">Fully Paid</option>
						<option value="overdue">Overdue</option>
					</select>
				</div>
				<div class="col-md-6 text-right inv-pagination"></div>
			</div>
			<div class="inv-table-container"></div>
		`);

		let current_page = 1;
		let current_filter = 'unpaid';

		function render_inv_table() {
			let filtered = all_invoices;
			if (current_filter === 'unpaid') filtered = all_invoices.filter(i => i.outstanding_amount > 0);
			else if (current_filter === 'paid') filtered = all_invoices.filter(i => i.outstanding_amount <= 0);
			else if (current_filter === 'overdue') filtered = all_invoices.filter(i => i.outstanding_amount > 0 && i.due_date && frappe.datetime.get_diff(frappe.datetime.get_today(), i.due_date) > 0);

			let total_pages = Math.ceil(filtered.length / PAGE_SIZE) || 1;
			if (current_page > total_pages) current_page = total_pages;
			let start = (current_page - 1) * PAGE_SIZE;
			let page_data = filtered.slice(start, start + PAGE_SIZE);

			let html = `<table class="table table-sm table-bordered table-hover">
				<thead><tr><th>Invoice</th><th>Date</th><th>Due Date</th><th>Status</th><th class="text-right">Total</th><th class="text-right">Outstanding</th><th>Action</th></tr></thead><tbody>`;
			if (page_data.length) {
				page_data.forEach(function (inv) {
					let overdue = inv.due_date && inv.outstanding_amount > 0 && frappe.datetime.get_diff(frappe.datetime.get_today(), inv.due_date) > 0;
					html += '<tr' + (overdue ? ' style="background:#fff3cd;"' : '') + '><td><a href="/app/' + slug + '/' + inv.name + '">' + inv.name + '</a></td>' +
						'<td>' + frappe.datetime.str_to_user(inv.posting_date) + '</td>' +
						'<td>' + frappe.datetime.str_to_user(inv.due_date || '') + (overdue ? ' <span class="badge" style="background:#dc3545;color:white;">Overdue</span>' : '') + '</td>' +
						'<td>' + (inv.status || '') + '</td>' +
						'<td class="text-right">' + fmt(inv.grand_total) + '</td>' +
						'<td class="text-right ' + (inv.outstanding_amount > 0 ? 'text-danger' : 'text-success') + '"><b>' + fmt(inv.outstanding_amount) + '</b></td>' +
						'<td>' + (inv.outstanding_amount > 0 ? '<button class="btn btn-xs btn-success btn-pay-inv" data-invoice="' + inv.name + '"><i class="fa fa-money"></i> Pay</button>' : '<span class="text-success">✓ Paid</span>') + '</td></tr>';
				});
			} else {
				html += '<tr><td colspan="7" class="text-center text-muted">No invoices matching filter</td></tr>';
			}
			html += '</tbody></table>';
			$tab.find('.inv-table-container').html(html);
			$tab.find('.inv-pagination').html(_pagination(current_page, total_pages, filtered.length, 'inv'));

			// Pay button
			$tab.find('.btn-pay-inv').on('click', function () {
				let invoice_name = $(this).data('invoice');
				frappe.call({
					method: 'erpnext.accounts.doctype.payment_entry.payment_entry.get_payment_entry',
					args: { dt: inv_dt, dn: invoice_name },
					callback: function (r) {
						if (r.message) { frappe.model.sync(r.message); frappe.set_route('Form', r.message.doctype, r.message.name); }
					}
				});
			});
		}

		$tab.find('.inv-status-filter').on('change', function () { current_filter = $(this).val(); current_page = 1; render_inv_table(); });
		$tab.on('click', '.inv-page-btn', function () { current_page = parseInt($(this).data('page')); render_inv_table(); });
		$tab.find('.btn-new-invoice').on('click', function () {
			let args = { company: company }; args[party_type.toLowerCase()] = party;
			frappe.new_doc(inv_dt, args);
		});

		render_inv_table();
	}


	// ═══════════════════════════════════════════
	// TAB: UNINVOICED ORDERS (with filters + pagination)
	// ═══════════════════════════════════════════
	function render_uninvoiced_tab(data, party_type, party, company, fmt) {
		let all_orders = data.all_orders || data.uninvoiced_orders || [];
		let order_dt = party_type === 'Customer' ? 'Sales Order' : 'Purchase Order';
		let inv_dt = party_type === 'Customer' ? 'Sales Invoice' : 'Purchase Invoice';
		let slug = order_dt.toLowerCase().replace(/ /g, '-');

		let $tab = $main.find('#tab-uninvoiced');
		$tab.html(`
			<div class="row" style="margin-bottom:10px; align-items:center;">
				<div class="col-md-3"><label style="font-weight:600;">Orders</label></div>
				<div class="col-md-3">
					<select class="form-control form-control-sm ord-status-filter">
						<option value="uninvoiced">Uninvoiced / Partial</option>
						<option value="all">All Orders</option>
						<option value="fully_billed">Fully Billed</option>
					</select>
				</div>
				<div class="col-md-6 text-right ord-pagination"></div>
			</div>
			<div class="ord-table-container"></div>
		`);

		let current_page = 1;
		let current_filter = 'uninvoiced';
		// Combine uninvoiced + invoiced for "all" filter
		let combined = (data.uninvoiced_orders || []).concat(data.invoiced_orders || []);

		function render_ord_table() {
			let filtered = combined;
			if (current_filter === 'uninvoiced') filtered = combined.filter(o => (o.per_billed || 0) < 100);
			else if (current_filter === 'fully_billed') filtered = combined.filter(o => (o.per_billed || 0) >= 100);

			let total_pages = Math.ceil(filtered.length / PAGE_SIZE) || 1;
			if (current_page > total_pages) current_page = total_pages;
			let start = (current_page - 1) * PAGE_SIZE;
			let page_data = filtered.slice(start, start + PAGE_SIZE);

			let html = `<table class="table table-sm table-bordered table-hover">
				<thead><tr><th>Order</th><th>Date</th><th>Status</th><th class="text-right">Total</th><th class="text-right">% Billed</th><th class="text-right">Pending</th><th>Action</th></tr></thead><tbody>`;
			if (page_data.length) {
				page_data.forEach(function (o) {
					let pending = o.grand_total * (100 - (o.per_billed || 0)) / 100;
					let is_complete = (o.per_billed || 0) >= 100;
					html += '<tr><td><a href="/app/' + slug + '/' + o.name + '">' + o.name + '</a></td>' +
						'<td>' + frappe.datetime.str_to_user(o.transaction_date) + '</td>' +
						'<td>' + (o.status || '') + '</td>' +
						'<td class="text-right">' + fmt(o.grand_total) + '</td>' +
						'<td class="text-right">' + (o.per_billed || 0).toFixed(1) + '%</td>' +
						'<td class="text-right ' + (is_complete ? 'text-success' : 'text-warning') + '"><b>' + fmt(pending) + '</b></td>' +
						'<td>' + (!is_complete ? '<button class="btn btn-xs btn-primary btn-make-inv" data-order="' + o.name + '"><i class="fa fa-file-text-o"></i> Make Invoice</button>' : '<span class="text-success">✓ Billed</span>') + '</td></tr>';
				});
			} else {
				html += '<tr><td colspan="7" class="text-center text-muted">No orders matching filter</td></tr>';
			}
			html += '</tbody></table>';
			$tab.find('.ord-table-container').html(html);
			$tab.find('.ord-pagination').html(_pagination(current_page, total_pages, filtered.length, 'ord'));

			$tab.find('.btn-make-inv').on('click', function () {
				let order_name = $(this).data('order');
				let method = party_type === 'Customer'
					? 'erpnext.selling.doctype.sales_order.sales_order.make_sales_invoice'
					: 'erpnext.buying.doctype.purchase_order.purchase_order.make_purchase_invoice';
				frappe.call({
					method: method,
					args: { source_name: order_name },
					callback: function (r) {
						if (r.message) { var doc = frappe.model.sync(r.message); frappe.set_route('Form', r.message.doctype, r.message.name); }
					}
				});
			});
		}

		$tab.find('.ord-status-filter').on('change', function () { current_filter = $(this).val(); current_page = 1; render_ord_table(); });
		$tab.on('click', '.ord-page-btn', function () { current_page = parseInt($(this).data('page')); render_ord_table(); });
		render_ord_table();
	}


	// ═══════════════════════════════════════════
	// TAB: INVOICED ORDERS (merged into uninvoiced with filter)
	// ═══════════════════════════════════════════
	function render_invoiced_tab(data, party_type, party, company, fmt) {
		let orders = data.invoiced_orders || [];
		let slug = (party_type === 'Customer' ? 'Sales Order' : 'Purchase Order').toLowerCase().replace(/ /g, '-');

		let $tab = $main.find('#tab-invoiced');
		let current_page = 1;

		$tab.html(`<div class="text-right inv-ord-pagination" style="margin-bottom:10px;"></div><div class="inv-ord-table-container"></div>`);

		function render() {
			let total_pages = Math.ceil(orders.length / PAGE_SIZE) || 1;
			let start = (current_page - 1) * PAGE_SIZE;
			let page_data = orders.slice(start, start + PAGE_SIZE);

			let html = `<table class="table table-sm table-bordered table-hover">
				<thead><tr><th>Order</th><th>Date</th><th>Status</th><th class="text-right">Total</th><th class="text-right">% Billed</th></tr></thead><tbody>`;
			if (page_data.length) {
				page_data.forEach(function (o) {
					html += '<tr><td><a href="/app/' + slug + '/' + o.name + '">' + o.name + '</a></td><td>' + frappe.datetime.str_to_user(o.transaction_date) + '</td><td>' + (o.status || '') + '</td><td class="text-right">' + fmt(o.grand_total) + '</td><td class="text-right text-success">100%</td></tr>';
				});
			} else { html += '<tr><td colspan="5" class="text-center text-muted">No fully invoiced orders</td></tr>'; }
			html += '</tbody></table>';
			$tab.find('.inv-ord-table-container').html(html);
			$tab.find('.inv-ord-pagination').html(_pagination(current_page, total_pages, orders.length, 'invord'));
		}

		$tab.on('click', '.invord-page-btn', function () { current_page = parseInt($(this).data('page')); render(); });
		render();
	}


	// ═══════════════════════════════════════════
	// TAB: PAYMENTS (with filters + pagination)
	// ═══════════════════════════════════════════
	function render_payments_tab(data, party_type, party, company, fmt) {
		let payments = data.payment_entries || [];
		let $tab = $main.find('#tab-payments');

		$tab.html(`
			<div class="row" style="margin-bottom:10px; align-items:center;">
				<div class="col-md-3">
					<button class="btn btn-primary btn-sm btn-new-payment"><i class="fa fa-plus"></i> New Payment Entry</button>
				</div>
				<div class="col-md-3">
					<select class="form-control form-control-sm pay-type-filter">
						<option value="all">All Payments</option>
						<option value="Receive">Received</option>
						<option value="Pay">Paid</option>
					</select>
				</div>
				<div class="col-md-6 text-right pay-pagination"></div>
			</div>
			<div class="pay-table-container"></div>
		`);

		let current_page = 1;
		let current_filter = 'all';

		function render_pay() {
			let filtered = payments;
			if (current_filter !== 'all') filtered = payments.filter(p => p.payment_type === current_filter);

			let total_pages = Math.ceil(filtered.length / PAGE_SIZE) || 1;
			if (current_page > total_pages) current_page = total_pages;
			let start = (current_page - 1) * PAGE_SIZE;
			let page_data = filtered.slice(start, start + PAGE_SIZE);

			let html = `<table class="table table-sm table-bordered table-hover">
				<thead><tr><th>Payment</th><th>Date</th><th>Type</th><th>Mode</th><th>Ref No</th><th>Ref Date</th><th class="text-right">Amount</th></tr></thead><tbody>`;
			if (page_data.length) {
				page_data.forEach(function (p) {
					html += '<tr><td><a href="/app/payment-entry/' + p.name + '">' + p.name + '</a></td>' +
						'<td>' + frappe.datetime.str_to_user(p.posting_date) + '</td>' +
						'<td><span class="badge" style="background:' + (p.payment_type === 'Receive' ? '#28a745' : '#dc3545') + ';color:white;">' + p.payment_type + '</span></td>' +
						'<td>' + (p.mode_of_payment || '') + '</td>' +
						'<td>' + (p.reference_no || '') + '</td>' +
						'<td>' + frappe.datetime.str_to_user(p.reference_date || '') + '</td>' +
						'<td class="text-right"><b>' + fmt(p.paid_amount) + '</b></td></tr>';
				});
			} else { html += '<tr><td colspan="7" class="text-center text-muted">No payments matching filter</td></tr>'; }
			html += '</tbody></table>';
			$tab.find('.pay-table-container').html(html);
			$tab.find('.pay-pagination').html(_pagination(current_page, total_pages, filtered.length, 'pay'));
		}

		$tab.find('.pay-type-filter').on('change', function () { current_filter = $(this).val(); current_page = 1; render_pay(); });
		$tab.on('click', '.pay-page-btn', function () { current_page = parseInt($(this).data('page')); render_pay(); });
		$tab.find('.btn-new-payment').on('click', function () {
			frappe.new_doc('Payment Entry', { party_type, party, company, payment_type: party_type === 'Customer' ? 'Receive' : 'Pay' });
		});
		render_pay();
	}


	// ═══════════════════════════════════════════
	// TAB: JOURNAL ENTRIES
	// ═══════════════════════════════════════════
	function render_journals_tab(data, fmt) {
		let journals = data.journal_entries || [];
		let $tab = $main.find('#tab-journals');

		$tab.html(`
			<div class="row" style="margin-bottom:10px; align-items:center;">
				<div class="col-md-3">
					<button class="btn btn-primary btn-sm btn-new-jv"><i class="fa fa-plus"></i> New Journal Entry</button>
				</div>
			</div>
			<div class="table-responsive">
				<table class="table table-bordered table-hover table-sm">
					<thead class="thead-light">
						<tr>
							<th>Voucher No</th>
							<th>Posting Date</th>
							<th>Type</th>
							<th>Account</th>
							<th>Remarks</th>
							<th class="text-right">Debit</th>
							<th class="text-right">Credit</th>
						</tr>
					</thead>
					<tbody id="jv-tbody"></tbody>
				</table>
			</div>
			<div id="jv-pagination"></div>
		`);

		$tab.find('.btn-new-jv').on('click', function () {
			frappe.new_doc('Journal Entry');
		});

		let cur_page = 1;

		function render_list() {
			let total = journals.length;
			let max_page = Math.ceil(total / PAGE_SIZE) || 1;
			if (cur_page > max_page) cur_page = max_page;
			let start = (cur_page - 1) * PAGE_SIZE;
			let page_items = journals.slice(start, start + PAGE_SIZE);

			let html = '';
			if (!page_items.length) {
				html = '<tr><td colspan="7" class="text-center text-muted">No journal entries found.</td></tr>';
			} else {
				page_items.forEach(j => {
					html += `
						<tr>
							<td><a href="/app/journal-entry/${j.name}" style="font-weight:600;">${j.name}</a></td>
							<td>${frappe.datetime.str_to_user(j.posting_date)}</td>
							<td>${j.voucher_type}</td>
							<td>${j.account || ''}</td>
							<td style="max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${j.remarks || ''}">${j.remarks || ''}</td>
							<td class="text-right text-danger">${fmt(j.debit || 0)}</td>
							<td class="text-right text-success">${fmt(j.credit || 0)}</td>
						</tr>
					`;
				});
			}
			$tab.find('#jv-tbody').html(html);

			// Pagination
			let pag_html = '';
			if (total > PAGE_SIZE) {
				pag_html = `<div style="display:flex; justify-content:space-between; align-items:center; margin-top:10px;">
					<span class="text-muted">Showing ${start + 1} to ${Math.min(start + PAGE_SIZE, total)} of ${total}</span>
					<div class="btn-group">
						<button class="btn btn-default btn-sm btn-prev" ${cur_page === 1 ? 'disabled' : ''}>Prev</button>
						<button class="btn btn-default btn-sm btn-next" ${cur_page === max_page ? 'disabled' : ''}>Next</button>
					</div>
				</div>`;
			}
			$tab.find('#jv-pagination').html(pag_html);

			$tab.find('.btn-prev').off('click').on('click', () => { cur_page--; render_list(); });
			$tab.find('.btn-next').off('click').on('click', () => { cur_page++; render_list(); });
		}

		render_list();
	}


	// ═══════════════════════════════════════════
	// TAB: GENERAL LEDGER (with pagination)
	// ═══════════════════════════════════════════
	function render_ledger_tab(data, party_type, party, company, fmt) {
		let entries = data.ledger || [];
		let $tab = $main.find('#tab-ledger');

		$tab.html(`<div class="text-right led-pagination" style="margin-bottom:10px;"></div><div class="led-table-container"></div>`);

		let current_page = 1;

		function render_led() {
			let total_pages = Math.ceil(entries.length / PAGE_SIZE) || 1;
			if (current_page > total_pages) current_page = total_pages;
			let start = (current_page - 1) * PAGE_SIZE;
			let page_data = entries.slice(start, start + PAGE_SIZE);

			let html = `<table class="table table-sm table-bordered table-hover" style="font-size:12px;">
				<thead><tr><th>Date</th><th>Account</th><th>Voucher</th><th class="text-right">Debit</th><th class="text-right">Credit</th><th class="text-right">Balance</th><th>Remarks</th></tr></thead><tbody>`;
			if (page_data.length) {
				// Show Opening Balance for this page (if it's not the very first record)
				if (start > 0) {
					let prev_balance = entries[start - 1].balance || 0;
					html += `<tr style="background:#f8f9fa;">
						<td colspan="5" class="text-right"><b>Opening Balance</b></td>
						<td class="text-right"><b>${fmt(Math.abs(prev_balance))} ${prev_balance >= 0 ? 'Dr' : 'Cr'}</b></td>
						<td></td>
					</tr>`;
				}

				page_data.forEach(function (e) {
					let vs = (e.voucher_type || '').toLowerCase().replace(/ /g, '-');
					html += '<tr><td>' + frappe.datetime.str_to_user(e.posting_date) + '</td>' +
						'<td>' + (e.account || '') + '</td>' +
						'<td><a href="/app/' + vs + '/' + e.voucher_no + '" title="' + e.voucher_type + '">' + e.voucher_no + '</a></td>' +
						'<td class="text-right">' + (e.debit ? fmt(e.debit) : '') + '</td>' +
						'<td class="text-right">' + (e.credit ? fmt(e.credit) : '') + '</td>' +
						'<td class="text-right"><b>' + fmt(Math.abs(e.balance)) + (e.balance >= 0 ? ' Dr' : ' Cr') + '</b></td>' +
						'<td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="' + (e.remarks || '').replace(/"/g, '') + '">' + (e.remarks || '') + '</td></tr>';
				});

				// Show Closing Balance for this page
				let last_balance = page_data[page_data.length - 1].balance || 0;
				html += `<tr style="background:#f8f9fa;">
					<td colspan="5" class="text-right"><b>Closing Balance</b></td>
					<td class="text-right"><b>${fmt(Math.abs(last_balance))} ${last_balance >= 0 ? 'Dr' : 'Cr'}</b></td>
					<td></td>
				</tr>`;

			} else { html += '<tr><td colspan="7" class="text-center text-muted">No ledger entries</td></tr>'; }
			html += '</tbody></table>';
			$tab.find('.led-table-container').html(html);
			$tab.find('.led-pagination').html(_pagination(current_page, total_pages, entries.length, 'led'));
		}

		$tab.on('click', '.led-page-btn', function () { current_page = parseInt($(this).data('page')); render_led(); });
		render_led();
	}


	// ─── OTHER SIDE TAB ───
	function render_other_side(other, party, company, fmt) {
		let ot = other.party_type;
		let inv_dt = ot === 'Customer' ? 'Sales Invoice' : 'Purchase Invoice';
		let slug = inv_dt.toLowerCase().replace(/ /g, '-');
		let html = '<h5>As ' + ot + '</h5><p>Account: <b>' + (other.account || 'Not mapped') + '</b> | Balance: ' + fmt(Math.abs(other.balance || 0)) + (other.balance >= 0 ? ' Dr' : ' Cr') + '</p>';
		html += '<h6>Unpaid Invoices</h6><table class="table table-sm table-bordered"><thead><tr><th>Invoice</th><th>Date</th><th class="text-right">Outstanding</th></tr></thead><tbody>';
		if (other.unpaid_invoices && other.unpaid_invoices.length) {
			other.unpaid_invoices.forEach(function (inv) { html += '<tr><td><a href="/app/' + slug + '/' + inv.name + '">' + inv.name + '</a></td><td>' + frappe.datetime.str_to_user(inv.posting_date) + '</td><td class="text-right text-danger">' + fmt(inv.outstanding_amount) + '</td></tr>'; });
		} else { html += '<tr><td colspan="3" class="text-center text-muted">None</td></tr>'; }
		html += '</tbody></table>';
		html += '<h6>Payments</h6><table class="table table-sm table-bordered"><thead><tr><th>Payment</th><th>Date</th><th>Type</th><th class="text-right">Amount</th></tr></thead><tbody>';
		if (other.payment_entries && other.payment_entries.length) {
			other.payment_entries.forEach(function (p) { html += '<tr><td><a href="/app/payment-entry/' + p.name + '">' + p.name + '</a></td><td>' + frappe.datetime.str_to_user(p.posting_date) + '</td><td>' + p.payment_type + '</td><td class="text-right">' + fmt(p.paid_amount) + '</td></tr>'; });
		} else { html += '<tr><td colspan="4" class="text-center text-muted">None</td></tr>'; }
		html += '</tbody></table>';
		$main.find('#tab-other').html(html);
	}


	// ─── CHART ───
	function render_party_chart(data, party_type, fmt) {
		try {
			let months = {};
			(data.payment_entries || []).forEach(function (p) { let m = p.posting_date.substring(0, 7); if (!months[m]) months[m] = { paid: 0, invoiced: 0 }; months[m].paid += p.paid_amount || 0; });
			let all_inv = (data.unpaid_invoices || []).concat(data.invoiced_orders || []);
			all_inv.forEach(function (inv) { let d = inv.posting_date || inv.transaction_date; if (!d) return; let m = d.substring(0, 7); if (!months[m]) months[m] = { paid: 0, invoiced: 0 }; months[m].invoiced += inv.grand_total || 0; });
			let sorted = Object.keys(months).sort();
			if (sorted.length > 1) {
				new frappe.Chart('#chart-container', { data: { labels: sorted, datasets: [{ name: 'Invoiced', values: sorted.map(m => months[m].invoiced) }, { name: 'Paid', values: sorted.map(m => months[m].paid) }] }, type: 'bar', height: 220, colors: ['#5e64ff', '#28a745'] });
			} else { $main.find('#chart-container').html('<p class="text-muted text-center">Not enough data for chart</p>'); }
		} catch (e) { $main.find('#chart-container').html('<p class="text-muted text-center">Chart unavailable</p>'); }
	}


	// ─── PAGINATION HELPER ───
	function _pagination(current, total, count, prefix) {
		if (total <= 1) return '<span class="text-muted" style="font-size:12px;">Showing ' + count + ' records</span>';
		let html = '<span class="text-muted" style="font-size:12px; margin-right:10px;">Page ' + current + ' of ' + total + ' (' + count + ' records)</span>';
		if (current > 1) html += '<button class="btn btn-xs btn-default ' + prefix + '-page-btn" data-page="' + (current - 1) + '">‹ Prev</button> ';
		if (current < total) html += '<button class="btn btn-xs btn-default ' + prefix + '-page-btn" data-page="' + (current + 1) + '">Next ›</button>';
		return html;
	}

	// ─── CARD HELPER ───
	function _card(title, value, color, icon, subtitle, custom_class) {
		let cls = custom_class ? (' ' + custom_class) : '';
		let pointer = custom_class ? ' cursor:pointer;' : '';
		return '<div class="col-md-3' + cls + '"><div style="background:white; border:1px solid #e8e8e8; border-radius:8px; padding:15px; margin-bottom:10px; text-align:center;' + pointer + '">' +
			'<i class="fa ' + (icon || 'fa-info-circle') + '" style="font-size:20px; margin-bottom:8px; color:inherit;"></i>' +
			'<h4 class="' + color + '" style="margin:5px 0;">' + value + '</h4>' +
			'<p style="margin:0; font-weight:600; color:#6c757d; font-size:12px;">' + title + '</p>' +
			(subtitle ? '<p style="margin:0; color:#adb5bd; font-size:11px;">' + subtitle + '</p>' : '') +
			'</div></div>';
	}

	// ─── MODAL HELPER ───
	function _show_uninvoiced_modal(doctype, list, fmt) {
		let slug = doctype.toLowerCase().replace(/ /g, '-');
		let html = '<table class="table table-sm table-bordered table-hover"><thead><tr><th>Order</th><th>Date</th><th>Party</th><th class="text-right">Total</th><th class="text-right">Pending</th><th>Action</th></tr></thead><tbody>';
		if (list && list.length) {
			list.forEach(function (o) {
				html += '<tr><td><a href="/app/' + slug + '/' + o.name + '" target="_blank">' + o.name + '</a></td>' +
					'<td>' + frappe.datetime.str_to_user(o.transaction_date) + '</td>' +
					'<td>' + o.party + '</td>' +
					'<td class="text-right">' + fmt(o.grand_total) + '</td>' +
					'<td class="text-right text-warning"><b>' + fmt(o.pending_amount) + '</b></td>' +
					'<td><button class="btn btn-xs btn-primary btn-modal-make-inv" data-order="' + o.name + '">Make Invoice</button></td></tr>';
			});
		} else {
			html += '<tr><td colspan="6" class="text-center text-muted">No pending orders found.</td></tr>';
		}
		html += '</tbody></table>';

		let dialog = new frappe.ui.Dialog({
			title: 'Uninvoiced ' + doctype + 's',
			fields: [{ fieldtype: 'HTML', fieldname: 'html_table', options: html }],
			primary_action_label: 'Close',
			primary_action: function () { dialog.hide(); }
		});

		dialog.$wrapper.find('.btn-modal-make-inv').on('click', function () {
			let order_name = $(this).data('order');
			let method = doctype === 'Sales Order' ? 'erpnext.selling.doctype.sales_order.sales_order.make_sales_invoice' : 'erpnext.buying.doctype.purchase_order.purchase_order.make_purchase_invoice';
			frappe.call({
				method: method,
				args: { source_name: order_name },
				callback: function (r) {
					if (r.message) {
						dialog.hide();
						frappe.model.sync(r.message);
						frappe.set_route('Form', r.message.doctype, r.message.name);
					}
				}
			});
		});

		dialog.show();
	}
}