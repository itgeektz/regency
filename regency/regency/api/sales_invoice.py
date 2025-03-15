import frappe
from regency.regency.api.sales_order import validate_stock_item, msgThrow


def before_insert(doc, method):
    validate_accoounting_dimension


def before_submit(doc, method):
    # Do not validate Stock for Cash Inpatient Sales Invoice
    if doc.enabled_auto_create_delivery_notes == 0:
        return
    for row in doc.items:
        if frappe.get_value("Item", row.item_code, "is_stock_item") == 1:
            validate_stock_item(row, row.warehouse, method)


def validate_accoounting_dimension(doc):
    if doc.items[0].sales_order:
        order_doc = frappe.get_doc("Sales Order", doc.items[0].sales_order)

        for row in doc.get("items"):
            if not row.get("healthcare_practitioner"):
                row.healthcare_practitioner = order_doc.get("healthcare_practitioner")

            if not row.get("healthcare_service_unit"):
                row.healthcare_service_unit = order_doc.get("healthcare_service_unit")

            if not row.get("department"):
                row.department = order_doc.get("department")


def validate(doc, method):
    # Do not validate Stock for Cash Inpatient Sales Invoice
    if doc.enabled_auto_create_delivery_notes == 0:
        return
    if doc.items[0].sales_order and doc.items[0].reference_dt == "Drug Prescription":
        for row in doc.items:
            if frappe.get_value("Item", row.item_code, "is_stock_item") == 1:
                validate_stock_item(row, row.warehouse, method)
            else:
                if row.reference_dt == "Drug Prescription":
                    msgThrow(
                        (
                            f"Item: <b>{row.item_code}</b> RowNo: <b>{row.idx}</b> is not a stock item, delivery note cannot be create for this Item"
                        ),
                        method,
                    )
