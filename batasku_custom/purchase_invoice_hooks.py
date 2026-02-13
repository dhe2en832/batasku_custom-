# import frappe

# def before_insert_fill_details(doc, method):
#     print(f"=== HOOK TRIGGERED: before_insert_fill_details ===")
#     print(f"Purchase Invoice: {doc.name}")
    
#     if not doc.items:
#         print("No items found, returning")
#         return

#     print(f"Processing {len(doc.items)} items")
    
#     for i, item in enumerate(doc.items):
#         print(f"Item {i+1}: {item.item_code}")
        
#         # ===============================
#         # ISI PR DETAIL
#         # ===============================
#         if item.purchase_receipt and not item.pr_detail:
#             print(f"Looking for PR item: {item.purchase_receipt}, {item.item_code}")
#             pr_item = frappe.db.get_value(
#                 "Purchase Receipt Item",
#                 {
#                     "parent": item.purchase_receipt,
#                     "item_code": item.item_code
#                 },
#                 "name"
#             )
#             if pr_item:
#                 item.pr_detail = pr_item
#                 print(f"Found PR item: {pr_item}")
#             else:
#                 print(f"PR item not found for {item.purchase_receipt}, {item.item_code}")

#         # ===============================
#         # ISI PO DETAIL
#         # ===============================
#         if item.purchase_order and not item.po_detail:
#             print(f"Looking for PO item: {item.purchase_order}, {item.item_code}")
#             po_item = frappe.db.get_value(
#                 "Purchase Order Item",
#                 {
#                     "parent": item.purchase_order,
#                     "item_code": item.item_code
#                 },
#                 "name"
#             )
#             if po_item:
#                 item.po_detail = po_item
#                 print(f"Found PO item: {po_item}")
#             else:
#                 print(f"PO item not found for {item.purchase_order}, {item.item_code}")
    
#     print("=== HOOK COMPLETED ===")

# def validate_fill_details(doc, method):
#     """Try using validate event instead"""
#     print(f"=== HOOK TRIGGERED: validate_fill_details ===")
#     print(f"Purchase Invoice: {doc.name}")
#     before_insert_fill_details(doc, method)

# def before_validate_fill_details(doc, method):
#     """Also fill details on update/validate"""
#     print(f"=== HOOK TRIGGERED: before_validate_fill_details ===")
#     before_insert_fill_details(doc, method)
