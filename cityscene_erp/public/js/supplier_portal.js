// Supplier Portal Smart RFQ Autofill

frappe.ready(function() {
    // Check if we are on the RFQ portal page
    if (window.location.pathname.includes('/request-for-quotation/') || window.location.pathname.includes('/rfq/')) {
        autofill_supplier_rates();
    }
});

function autofill_supplier_rates() {
    // 1. Gather all item codes from the page
    let item_codes = [];
    
    // In standard RFQ portal, item_code isn't always directly exposed in a data attribute easily.
    // Wait, the global `doc` object has `doc.items`.
    if (window.doc && window.doc.items) {
        window.doc.items.forEach(item => {
            item_codes.push(item.item_code);
        });
    } else {
        return;
    }

    if (item_codes.length === 0) return;

    // 2. Fetch the rates for these items from the active Supplier Rate List
    frappe.call({
        method: "cityscene_erp.api.supplier_portal.get_active_supplier_rates",
        args: {
            items: JSON.stringify(item_codes)
        },
        callback: function(r) {
            if (r.message) {
                let rates = r.message;
                let autofilled = false;
                
                // 3. Populate the inputs
                window.doc.items.forEach(item => {
                    if (rates[item.item_code]) {
                        let rate = rates[item.item_code];
                        // Find the input corresponding to this item's idx
                        let rateInput = document.querySelector(`.rfq-rate[data-idx="${item.idx}"]`);
                        if (rateInput && parseFloat(rateInput.value) === 0) {
                            rateInput.value = rate;
                            autofilled = true;
                            // Trigger the change event so the standard Frappe JS recalculates amounts
                            let event = new Event('change');
                            rateInput.dispatchEvent(event);
                        }
                    }
                });
                
                if (autofilled) {
                    frappe.show_alert({
                        message: __('Rates automatically filled from your active Rate List!'),
                        indicator: 'green'
                    });
                }
            }
        }
    });
}
