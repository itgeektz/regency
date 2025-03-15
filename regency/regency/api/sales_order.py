import frappe

def validate(doc, method):
    for row in doc.items:
        if frappe.get_value("Item", row.item_code, "is_stock_item") == 1:
            set_dosage_infor_template(row)
            validate_stock_item(row, doc.set_warehouse, method)
        else:
            if row.reference_dt == "Drug Prescription":
                msgThrow(
                    (
                        f"Item: <b>{row.item_code}</b> RowNo: <b>{row.idx}</b> is not a stock item, delivery note cannot be create for this Item"
                    ),
                    method,
                )
    
def before_submit(doc, method):
    for row in doc.items:
        if frappe.get_value("Item", row.item_code, "is_stock_item") == 1:
            validate_stock_item(row, doc.set_warehouse, method)
    
def set_dosage_infor_template(row):
    row.reference_dt = "Drug Prescription"
    if not row.dosage_info:
        row.dosage_info = ", \n".join([
            "frequency: ",
            "period: ",
            "dosage_form: ",
            "interval: ",
            "interval_uom: ",
            "Doctor's comment: "
        ])
        frappe.msgprint(f"<strong>Please enter dosage information for item: {row.item_code}</strong>")

def validate_stock_item(item, warehouse, method):
    stock_qty = get_stock_availability(item.item_code, warehouse)
    if float(item.qty) > float(stock_qty):
            msgThrow(
                (
                    f"Available quantity for item: <h4 style='background-color:\
                    LightCoral'>{item.item_code} is {stock_qty}</h4>In {warehouse}."
                ),
                method,
            )
            return False

def get_stock_availability(item_code, warehouse):
    latest_sle = frappe.db.sql(
        """SELECT qty_after_transaction AS actual_qty
        FROM `tabStock Ledger Entry`
        WHERE item_code = %s AND warehouse = %s
          AND is_cancelled = 0
        ORDER BY creation DESC
        LIMIT 1""",
        (item_code, warehouse),
        as_dict=1,
    )

    sle_qty = latest_sle[0].actual_qty or 0 if latest_sle else 0
    return sle_qty

def msgThrow(msg, method="throw", alert=True):
    if method == "validate":
        frappe.msgprint(msg, alert=alert)
    else:
        frappe.throw(msg)