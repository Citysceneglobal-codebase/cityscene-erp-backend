import frappe
from frappe import _

@frappe.whitelist()
def get_party_for_account(account: str, company: str):
    """Check if account is linked to a party"""
    party_acc = frappe.db.get_value("Party Account", {"account": account, "company": company}, ["parenttype", "parent"], as_dict=True)
    if party_acc:
        return {"party_type": party_acc.parenttype, "party": party_acc.parent}
    
    # Try finding an account where account_type is Receivable/Payable, though without Party Account it's tricky.
    # Usually party_account table handles it.
    return None

@frappe.whitelist()
def get_party_details(party_type: str = None, party: str = None, company: str = None, from_date: str = None, to_date: str = None, account: str = None):
    """Get comprehensive party or account accounting data"""
    
    # If only account is provided (no party)
    if account and not party:
        party_info = get_party_for_account(account, company)
        if party_info:
            party_type = party_info["party_type"]
            party = party_info["party"]
        else:
            balance = _get_balance(None, None, company, account, from_date, to_date)
            ledger = _get_ledger(None, None, company, account, from_date, to_date)
            payment_entries = _get_payment_entries(None, None, company, from_date, to_date, account=account)
            journal_entries = _get_journal_entries(None, None, company, from_date, to_date, account=account)
            
            return {
                "party_account": account,
                "balance": balance,
                "is_dual": False,
                "unpaid_invoices": [],
                "all_invoices": [],
                "uninvoiced_orders": [],
                "invoiced_orders": [],
                "all_orders": [],
                "payment_entries": payment_entries,
                "journal_entries": journal_entries,
                "ledger": ledger,
                "other_side": {},
                "cards": {
                    "total_outstanding": 0,
                    "total_orders_pending": 0,
                    "total_paid": sum(pe.get("paid_amount", 0) for pe in payment_entries),
                    "unpaid_count": 0,
                    "uninvoiced_count": 0,
                    "payment_count": len(payment_entries),
                }
            }

    # Check if party is both Customer and Supplier
    is_dual = False
    if party_type == "Customer":
        is_dual = frappe.db.exists("Supplier", party)
    else:
        is_dual = frappe.db.exists("Customer", party)
    
    # Get party account
    party_account = frappe.db.get_value("Party Account", 
        {"parent": party, "parenttype": party_type, "company": company}, "account")
    
    # Balance
    balance = _get_balance(party_type, party, company, party_account, from_date, to_date)
    
    # Unpaid invoices
    unpaid_invoices = _get_unpaid_invoices(party_type, party, company, from_date, to_date)
    
    # Uninvoiced orders
    uninvoiced_orders = _get_uninvoiced_orders(party_type, party, company, from_date, to_date)
    
    # Invoiced orders
    invoiced_orders = _get_invoiced_orders(party_type, party, company, from_date, to_date)
    
    # Payment entries
    payment_entries = _get_payment_entries(party_type, party, company, from_date, to_date)
    
    # Journal Entries
    journal_entries = _get_journal_entries(party_type, party, company, from_date, to_date)
    
    # General Ledger
    ledger = _get_ledger(party_type, party, company, party_account, from_date, to_date)
    
    # If dual party, get the other side too
    other_side = {}
    if is_dual:
        other_type = "Supplier" if party_type == "Customer" else "Customer"
        other_account = frappe.db.get_value("Party Account",
            {"parent": party, "parenttype": other_type, "company": company}, "account")
        other_side = {
            "party_type": other_type,
            "account": other_account,
            "balance": _get_balance(other_type, party, company, other_account, from_date, to_date),
            "unpaid_invoices": _get_unpaid_invoices(other_type, party, company, from_date, to_date),
            "uninvoiced_orders": _get_uninvoiced_orders(other_type, party, company, from_date, to_date),
            "payment_entries": _get_payment_entries(other_type, party, company, from_date, to_date),
            "journal_entries": _get_journal_entries(other_type, party, company, from_date, to_date),
        }
    
    # Summary cards
    total_outstanding = sum(inv.get("outstanding_amount", 0) for inv in unpaid_invoices)
    total_orders_pending = sum(o.get("pending_amount", 0) for o in uninvoiced_orders)
    total_paid = sum(pe.get("paid_amount", 0) for pe in payment_entries)
    # Get ALL invoices (for client-side filtering)
    all_invoices = _get_all_invoices(party_type, party, company, from_date, to_date)
    
    # Get ALL orders (for client-side filtering)
    all_orders = (uninvoiced_orders or []) + (invoiced_orders or [])
    
    return {
        "party_account": party_account,
        "balance": balance,
        "is_dual": is_dual,
        "unpaid_invoices": unpaid_invoices,
        "all_invoices": all_invoices,
        "uninvoiced_orders": uninvoiced_orders,
        "invoiced_orders": invoiced_orders,
        "all_orders": all_orders,
        "payment_entries": payment_entries,
        "journal_entries": journal_entries,
        "ledger": ledger,
        "other_side": other_side,
        "cards": {
            "total_outstanding": total_outstanding,
            "total_orders_pending": total_orders_pending,
            "total_paid": total_paid,
            "unpaid_count": len(unpaid_invoices),
            "uninvoiced_count": len(uninvoiced_orders),
            "payment_count": len(payment_entries),
        }
    }


@frappe.whitelist()
def get_company_overview(company: str, from_date: str = None, to_date: str = None):
    """Get company-wide accounting overview when no party is selected"""
    
    date_filter = ""
    date_params = []
    
    if from_date and to_date:
        date_filter = " AND posting_date BETWEEN %s AND %s"
        date_params = [from_date, to_date]
        
        ord_date_filter = " AND transaction_date BETWEEN %s AND %s"
    elif from_date:
        date_filter = " AND posting_date >= %s"
        date_params = [from_date]
        ord_date_filter = " AND transaction_date >= %s"
    elif to_date:
        date_filter = " AND posting_date <= %s"
        date_params = [to_date]
        ord_date_filter = " AND transaction_date <= %s"
    else:
        ord_date_filter = ""

    # Top outstanding customers
    top_customers = frappe.db.sql(f"""
        SELECT customer as party, COALESCE(SUM(outstanding_amount), 0) as outstanding
        FROM `tabSales Invoice`
        WHERE company=%s AND docstatus=1 AND outstanding_amount > 0 {date_filter}
        GROUP BY customer ORDER BY outstanding DESC LIMIT 10
    """, [company] + date_params, as_dict=True)
    
    # Top outstanding suppliers
    top_suppliers = frappe.db.sql(f"""
        SELECT supplier as party, COALESCE(SUM(outstanding_amount), 0) as outstanding
        FROM `tabPurchase Invoice`
        WHERE company=%s AND docstatus=1 AND outstanding_amount > 0 {date_filter}
        GROUP BY supplier ORDER BY outstanding DESC LIMIT 10
    """, [company] + date_params, as_dict=True)
    
    # Total receivable
    total_receivable = frappe.db.sql(f"""
        SELECT COALESCE(SUM(outstanding_amount), 0) as total
        FROM `tabSales Invoice` WHERE company=%s AND docstatus=1 AND outstanding_amount > 0 {date_filter}
    """, [company] + date_params)[0][0] or 0
    
    # Total payable
    total_payable = frappe.db.sql(f"""
        SELECT COALESCE(SUM(outstanding_amount), 0) as total
        FROM `tabPurchase Invoice` WHERE company=%s AND docstatus=1 AND outstanding_amount > 0 {date_filter}
    """, [company] + date_params)[0][0] or 0
    
    # Uninvoiced sales orders
    uninvoiced_so = frappe.db.sql(f"""
        SELECT COUNT(*) as cnt, COALESCE(SUM(grand_total - COALESCE(per_billed, 0) * grand_total / 100), 0) as amount
        FROM `tabSales Order` WHERE company=%s AND docstatus=1 AND per_billed < 100 AND status != 'Cancelled' {ord_date_filter}
    """, [company] + date_params, as_dict=True)[0]
    
    uninvoiced_so_list = frappe.db.sql(f"""
        SELECT name, customer as party, transaction_date, grand_total, per_billed, 
               (grand_total - COALESCE(per_billed, 0) * grand_total / 100) as pending_amount
        FROM `tabSales Order` 
        WHERE company=%s AND docstatus=1 AND per_billed < 100 AND status != 'Cancelled' {ord_date_filter}
        ORDER BY transaction_date DESC LIMIT 100
    """, [company] + date_params, as_dict=True)
    
    # Uninvoiced purchase orders
    uninvoiced_po = frappe.db.sql(f"""
        SELECT COUNT(*) as cnt, COALESCE(SUM(grand_total - COALESCE(per_billed, 0) * grand_total / 100), 0) as amount
        FROM `tabPurchase Order` WHERE company=%s AND docstatus=1 AND per_billed < 100 AND status != 'Cancelled' {ord_date_filter}
    """, [company] + date_params, as_dict=True)[0]

    uninvoiced_po_list = frappe.db.sql(f"""
        SELECT name, supplier as party, transaction_date, grand_total, per_billed, 
               (grand_total - COALESCE(per_billed, 0) * grand_total / 100) as pending_amount
        FROM `tabPurchase Order` 
        WHERE company=%s AND docstatus=1 AND per_billed < 100 AND status != 'Cancelled' {ord_date_filter}
        ORDER BY transaction_date DESC LIMIT 100
    """, [company] + date_params, as_dict=True)
    
    # Recent payments
    pay_filters = {"company": company, "docstatus": 1}
    if from_date and to_date:
        pay_filters["posting_date"] = ["between", [from_date, to_date]]
    elif from_date:
        pay_filters["posting_date"] = [">=", from_date]
    elif to_date:
        pay_filters["posting_date"] = ["<=", to_date]
        
    recent_payments = frappe.get_all("Payment Entry",
        filters=pay_filters,
        fields=["name", "posting_date", "party_type", "party", "paid_amount", "payment_type"],
        order_by="posting_date desc", limit=10)
    
    # Monthly collection data
    monthly_data = frappe.db.sql(f"""
        SELECT DATE_FORMAT(posting_date, '%%Y-%%m') as month,
            SUM(CASE WHEN payment_type='Receive' THEN paid_amount ELSE 0 END) as received,
            SUM(CASE WHEN payment_type='Pay' THEN paid_amount ELSE 0 END) as paid
        FROM `tabPayment Entry`
        WHERE company=%s AND docstatus=1 {date_filter}
        GROUP BY DATE_FORMAT(posting_date, '%%Y-%%m')
        ORDER BY month
    """, [company] + date_params, as_dict=True)
    
    # Keep only the last 12 months to prevent chart overcrowding
    monthly_data = monthly_data[-12:] if monthly_data else []
    
    return {
        "total_receivable": total_receivable,
        "total_payable": total_payable,
        "top_customers": top_customers,
        "top_suppliers": top_suppliers,
        "uninvoiced_so": uninvoiced_so,
        "uninvoiced_po": uninvoiced_po,
        "uninvoiced_so_list": uninvoiced_so_list,
        "uninvoiced_po_list": uninvoiced_po_list,
        "recent_payments": recent_payments,
        "monthly_data": monthly_data,
    }


def _get_balance(party_type: str, party: str, company: str, party_account: str | None, from_date: str = None, to_date: str = None):
    date_filter = ""
    date_params = []
    if from_date and to_date:
        date_filter = " AND posting_date BETWEEN %s AND %s"
        date_params = [from_date, to_date]
    elif from_date:
        date_filter = " AND posting_date >= %s"
        date_params = [from_date]
    elif to_date:
        date_filter = " AND posting_date <= %s"
        date_params = [to_date]

    if party_account:
        result = frappe.db.sql(
            f"SELECT SUM(debit) - SUM(credit) FROM `tabGL Entry` WHERE account=%s AND is_cancelled=0 {date_filter}",
            [party_account] + date_params)
    else:
        result = frappe.db.sql(
            f"SELECT SUM(debit) - SUM(credit) FROM `tabGL Entry` WHERE party_type=%s AND party=%s AND company=%s AND is_cancelled=0 {date_filter}",
            [party_type, party, company] + date_params)
    
    balance = (result[0][0] or 0) if result else 0
    if party_type == "Supplier":
        balance = -balance
    return balance


def _apply_date_filter(filters, field_name, from_date, to_date):
    if from_date and to_date:
        filters[field_name] = ["between", [from_date, to_date]]
    elif from_date:
        filters[field_name] = [">=", from_date]
    elif to_date:
        filters[field_name] = ["<=", to_date]


def _get_unpaid_invoices(party_type: str, party: str, company: str, from_date: str = None, to_date: str = None):
    filters = {"company": company, "docstatus": 1, "outstanding_amount": (">", 0)}
    if party_type == "Customer":
        filters["customer"] = party
        _apply_date_filter(filters, "posting_date", from_date, to_date)
        return frappe.get_all("Sales Invoice", filters=filters,
            fields=["name", "posting_date", "grand_total", "outstanding_amount", "due_date", "status"],
            order_by="posting_date desc")
    else:
        filters["supplier"] = party
        _apply_date_filter(filters, "posting_date", from_date, to_date)
        return frappe.get_all("Purchase Invoice", filters=filters,
            fields=["name", "posting_date", "grand_total", "outstanding_amount", "due_date", "status"],
            order_by="posting_date desc")


def _get_all_invoices(party_type: str, party: str, company: str, from_date: str = None, to_date: str = None):
    """Get ALL invoices (paid + unpaid) for client-side filtering"""
    filters = {"company": company, "docstatus": 1}
    _apply_date_filter(filters, "posting_date", from_date, to_date)
    
    if party_type == "Customer":
        filters["customer"] = party
        return frappe.get_all("Sales Invoice", filters=filters,
            fields=["name", "posting_date", "grand_total", "outstanding_amount", "due_date", "status"],
            order_by="posting_date desc", limit=200)
    else:
        filters["supplier"] = party
        return frappe.get_all("Purchase Invoice", filters=filters,
            fields=["name", "posting_date", "grand_total", "outstanding_amount", "due_date", "status"],
            order_by="posting_date desc", limit=200)


def _get_uninvoiced_orders(party_type: str, party: str, company: str, from_date: str = None, to_date: str = None):
    filters = {"company": company, "docstatus": 1, "per_billed": ("<", 100), "status": ("!=", "Cancelled")}
    _apply_date_filter(filters, "transaction_date", from_date, to_date)
    
    if party_type == "Customer":
        filters["customer"] = party
        orders = frappe.get_all("Sales Order", filters=filters,
            fields=["name", "transaction_date", "grand_total", "per_billed", "status", "delivery_status"],
            order_by="transaction_date desc")
    else:
        filters["supplier"] = party
        orders = frappe.get_all("Purchase Order", filters=filters,
            fields=["name", "transaction_date", "grand_total", "per_billed", "status"],
            order_by="transaction_date desc")
    
    for o in orders:
        o["pending_amount"] = o["grand_total"] * (100 - (o.get("per_billed") or 0)) / 100
    
    return orders


def _get_invoiced_orders(party_type: str, party: str, company: str, from_date: str = None, to_date: str = None):
    filters = {"company": company, "docstatus": 1, "per_billed": 100}
    _apply_date_filter(filters, "transaction_date", from_date, to_date)
    
    if party_type == "Customer":
        filters["customer"] = party
        return frappe.get_all("Sales Order", filters=filters,
            fields=["name", "transaction_date", "grand_total", "per_billed", "status"],
            order_by="transaction_date desc", limit=20)
    else:
        filters["supplier"] = party
        return frappe.get_all("Purchase Order", filters=filters,
            fields=["name", "transaction_date", "grand_total", "per_billed", "status"],
            order_by="transaction_date desc", limit=20)


def _get_payment_entries(party_type: str, party: str, company: str, from_date: str = None, to_date: str = None, account: str = None):
    filters = {"company": company, "docstatus": 1}
    _apply_date_filter(filters, "posting_date", from_date, to_date)
    
    if account and not party:
        # Search by account if party is missing.
        # Payment Entry has no single account field, we must find where it's used.
        # It's easier to check GL entries or we can just skip or search 'paid_from' / 'paid_to'
        filters_1 = filters.copy()
        filters_1["paid_from"] = account
        filters_2 = filters.copy()
        filters_2["paid_to"] = account
        
        res1 = frappe.get_all("Payment Entry", filters=filters_1,
            fields=["name", "posting_date", "paid_amount", "payment_type", "mode_of_payment", "reference_no", "reference_date"], order_by="posting_date desc", limit=50)
        res2 = frappe.get_all("Payment Entry", filters=filters_2,
            fields=["name", "posting_date", "paid_amount", "payment_type", "mode_of_payment", "reference_no", "reference_date"], order_by="posting_date desc", limit=50)
        
        # Combine and sort
        combined = list({v['name']:v for v in res1 + res2}.values())
        combined.sort(key=lambda x: x['posting_date'], reverse=True)
        return combined[:50]
    
    filters["party_type"] = party_type
    filters["party"] = party
    
    return frappe.get_all("Payment Entry", filters=filters,
        fields=["name", "posting_date", "paid_amount", "payment_type", "mode_of_payment", "reference_no", "reference_date"],
        order_by="posting_date desc", limit=50)

def _get_journal_entries(party_type: str, party: str, company: str, from_date: str = None, to_date: str = None, account: str = None):
    date_filter = ""
    date_params = []
    if from_date and to_date:
        date_filter = " AND j.posting_date BETWEEN %s AND %s"
        date_params = [from_date, to_date]
    elif from_date:
        date_filter = " AND j.posting_date >= %s"
        date_params = [from_date]
    elif to_date:
        date_filter = " AND j.posting_date <= %s"
        date_params = [to_date]

    if account and not party:
        query = f"""
            SELECT j.name, j.posting_date, j.voucher_type, j.user_remark as remarks, a.debit, a.credit, a.account, a.party
            FROM `tabJournal Entry` j
            JOIN `tabJournal Entry Account` a ON j.name = a.parent
            WHERE j.company = %s AND j.docstatus = 1 AND a.account = %s {date_filter}
            ORDER BY j.posting_date DESC
            LIMIT 50
        """
        return frappe.db.sql(query, [company, account] + date_params, as_dict=True)
    
    query = f"""
        SELECT j.name, j.posting_date, j.voucher_type, j.user_remark as remarks, a.debit, a.credit, a.account
        FROM `tabJournal Entry` j
        JOIN `tabJournal Entry Account` a ON j.name = a.parent
        WHERE j.company = %s AND j.docstatus = 1 AND a.party_type = %s AND a.party = %s {date_filter}
        ORDER BY j.posting_date DESC
        LIMIT 50
    """
    return frappe.db.sql(query, [company, party_type, party] + date_params, as_dict=True)


def _get_ledger(party_type: str, party: str, company: str, party_account: str | None, from_date: str = None, to_date: str = None):
    filters = {"company": company, "is_cancelled": 0}
    _apply_date_filter(filters, "posting_date", from_date, to_date)
    
    if party_account:
        filters["account"] = party_account
    else:
        filters["party_type"] = party_type
        filters["party"] = party
    
    entries = frappe.get_all("GL Entry",
        filters=filters,
        fields=["posting_date", "account", "debit", "credit", "voucher_type", "voucher_no", "remarks", "against"],
        order_by="posting_date asc, creation asc",
        limit=200)
    
    # Calculate running balance
    running = 0
    for e in entries:
        running += (e.get("debit") or 0) - (e.get("credit") or 0)
        e["balance"] = running
    
    return entries
