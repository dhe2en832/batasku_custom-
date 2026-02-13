import frappe

@frappe.whitelist()
def create_purchase_invoice_with_details(invoice_data):
    """
    Create Purchase Invoice with proper linkage to Purchase Receipt and Purchase Order
    """
    import json
    
    print("=== CREATE PURCHASE INVOICE WITH DETAILS ===")
    print(f"Raw invoice data type: {type(invoice_data)}")
    print(f"Raw invoice data: {invoice_data}")
    
    # Parse JSON string if needed
    if isinstance(invoice_data, str):
        print("Parsing JSON string...")
        invoice_data = json.loads(invoice_data)
    
    print(f"Parsed invoice data: {json.dumps(invoice_data, indent=2, default=str)}")
    
    try:
        # Create PI document
        pi = frappe.new_doc("Purchase Invoice")
        
        # Set basic fields
        pi.company = invoice_data.get("company")
        pi.supplier = invoice_data.get("supplier")
        pi.posting_date = invoice_data.get("posting_date")
        pi.due_date = invoice_data.get("due_date")
        pi.currency = invoice_data.get("currency", "IDR")
        pi.custom_notes_pi = invoice_data.get("custom_notes_pi", "")
        pi.remarks = invoice_data.get("remarks", "")
        
        print(f"PI basic fields set: company={pi.company}, supplier={pi.supplier}")
        print(f"Custom notes PI: {pi.custom_notes_pi}")
        print(f"Remarks: {pi.remarks}")
        print(f"Available invoice_data keys: {list(invoice_data.keys())}")
        
        # Add items with proper linkage
        for i, item_data in enumerate(invoice_data.get("items", [])):
            print(f"Processing item {i+1}: {item_data}")
            
            # Get PR item details
            pr_item_name = None
            if item_data.get("purchase_receipt") and item_data.get("purchase_receipt_item"):
                pr_item_name = frappe.db.get_value(
                    "Purchase Receipt Item",
                    {
                        "parent": item_data["purchase_receipt"],
                        "name": item_data["purchase_receipt_item"],
                        "item_code": item_data["item_code"]
                    },
                    "name"
                )
            
            # Get PO item details
            po_item_name = None
            if item_data.get("purchase_order") and item_data.get("purchase_order_item"):
                po_item_name = frappe.db.get_value(
                    "Purchase Order Item",
                    {
                        "parent": item_data["purchase_order"],
                        "name": item_data["purchase_order_item"],
                        "item_code": item_data["item_code"]
                    },
                    "name"
                )
            
            print(f"Found linkage: pr_detail={pr_item_name}, po_detail={po_item_name}")
            
            # Get quantities from frontend first, then fallback to database
            frontend_received_qty = item_data.get("received_qty", 0)
            frontend_rejected_qty = item_data.get("rejected_qty", 0)
            
            # Use frontend values if provided, otherwise fallback to database
            received_qty = frontend_received_qty if frontend_received_qty is not None and frontend_received_qty >= 0 else (frappe.db.get_value("Purchase Receipt Item", pr_item_name, "received_qty") or 0) if pr_item_name else 0
            rejected_qty = frontend_rejected_qty if frontend_rejected_qty is not None and frontend_rejected_qty >= 0 else (frappe.db.get_value("Purchase Receipt Item", pr_item_name, "rejected_qty") or 0) if pr_item_name else 0
            
            # Add item to PI
            pi.append("items", {
                "item_code": item_data["item_code"],
                "item_name": item_data.get("item_name", item_data["item_code"]),
                "description": item_data.get("description", item_data.get("item_name", item_data["item_code"])),
                "qty": item_data["qty"],
                "uom": item_data.get("uom", "Nos"),
                "rate": item_data["rate"],
                "warehouse": item_data.get("warehouse"),
                "purchase_receipt": item_data.get("purchase_receipt"),
                "purchase_order": item_data.get("purchase_order"),
                # Set linkage fields if found
                "pr_detail": pr_item_name,
                "po_detail": po_item_name,
                # Set quantities from frontend
                "received_qty": received_qty,
                "rejected_qty": rejected_qty,
            })
            
            # Debug: Check what we set vs what ERPNext might override
            print(f"Before save - Set: received={received_qty}, rejected={rejected_qty}")
            print(f"Before save - Linkage: pr_detail={pr_item_name}, po_detail={po_item_name}")
        
        # Save the document
        pi.insert()
        
        # Submit the document if needed
        if invoice_data.get("submit", False):
            pi.submit()
        
        print(f"PI created successfully: {pi.name}")
        
        # Debug: Check final values after save
        print("=== AFTER SAVE DEBUG ===")
        for item in pi.items:
            print(f"Item {item.idx}: {item.item_code}")
            print(f"  - received_qty: {item.received_qty}")
            print(f"  - rejected_qty: {item.rejected_qty}")
            print(f"  - pr_detail: {item.pr_detail}")
            print(f"  - po_detail: {item.po_detail}")
        
        return {
            "success": True,
            "message": "Purchase Invoice created successfully",
            "data": {
                "name": pi.name,
                "docstatus": pi.docstatus
            }
        }
        
    except Exception as e:
        print(f"=== CUSTOM API ERROR ===")
        print(f"Error type: {type(e)}")
        print(f"Error message: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        
        frappe.log_error(f"Error creating Purchase Invoice: {str(e)}\n\nTraceback:\n{traceback.format_exc()}", "Purchase Invoice API Error")
        return {
            "success": False,
            "message": str(e)
        }

@frappe.whitelist()
def fetch_pr_detail_for_pi(pr):
    """
    Fetch Purchase Receipt details for Purchase Invoice creation
    Includes received_qty and rejected_qty for each item
    """
    import json
    
    print(f"=== FETCH PR DETAIL FOR PI ===")
    print(f"PR: {pr}")
    
    try:
        # Check if PR exists and belongs to selected company
        if not frappe.db.exists("Purchase Receipt", pr):
            return {
                "success": False,
                "message": f"Purchase Receipt {pr} not found"
            }
        
        # Get PR details
        pr_doc = frappe.get_doc("Purchase Receipt", pr)
        
        print(f"PR found: {pr_doc.name}")
        print(f"Supplier: {pr_doc.supplier}")
        print(f"Company: {pr_doc.company}")
        print(f"Items count: {len(pr_doc.items)}")
        
        # Build response
        items = []
        for item in pr_doc.items:
            print(f"Processing item: {item.item_code}")
            print(f"  - received_qty: {item.received_qty}")
            print(f"  - rejected_qty: {item.rejected_qty}")
            print(f"  - accepted_qty: {item.accepted_qty}")
            print(f"  - billed_qty: {item.billed_qty}")
            print(f"  - outstanding_qty: {item.outstanding_qty}")
            
            items.append({
                "item_code": item.item_code,
                "item_name": item.item_name,
                "description": item.description,
                "qty": item.qty,
                "received_qty": item.received_qty or 0,
                "rejected_qty": item.rejected_qty or 0,
                "accepted_qty": item.accepted_qty or 0,
                "billed_qty": item.billed_qty or 0,
                "outstanding_qty": item.outstanding_qty or 0,
                "uom": item.uom,
                "rate": item.rate,
                "amount": item.amount,
                "warehouse": item.warehouse,
                "purchase_order": item.purchase_order,
                "purchase_order_item": item.purchase_order_item,
                # Use the actual field name from database
                "purchase_receipt_item": item.name
            })
        
        response = {
            "success": True,
            "data": {
                "name": pr_doc.name,
                "supplier": pr_doc.supplier,
                "supplier_name": pr_doc.supplier_name,
                "posting_date": pr_doc.posting_date.strftime("%Y-%m-%d"),
                "company": pr_doc.company,
                "currency": pr_doc.currency,
                "items": items,
                "custom_note_pr": pr_doc.custom_note_pr or ""
            }
        }
        
        print(f"Response prepared with {len(items)} items")
        return response
        
    except Exception as e:
        print(f"Error fetching PR details: {str(e)}")
        frappe.log_error(f"Error fetching PR details for {pr}: {str(e)}", "PR Detail Fetch Error")
        return {
            "success": False,
            "message": str(e)
        }
