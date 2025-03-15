import frappe
from frappe.utils import nowdate, add_days, getdate, cint, cstr


def get_childs_map():
    return [
        {
            "table": "lab_test_prescription",
            "template": "Lab Test Template",
            "item_field": "lab_test_code",
        },
        {
            "table": "radiology_procedure_prescription",
            "template": "Radiology Examination Template",
            "item_field": "radiology_examination_template",
        },
        {
            "table": "procedure_prescription",
            "template": "Clinical Procedure Template",
            "item_field": "procedure",
        },
        {
            "table": "drug_prescription",
            "template": "Medication",
            "item_field": "drug_code",
        },
        {
            "table": "therapies",
            "template": "Therapy Type",
            "item_field": "therapy_type",
        },
    ]


def on_submit(doc, method):
    if doc.inpatient_record and doc.insurance_subscription:
        create_sales_order(doc)
    elif not doc.inpatient_record:
        create_sales_order(doc)


def create_sales_order(doc):
    if doc.company == "Regency Medical Centre HQ":
        warehouse = "A Block Ground Floor Cash Pharmacy - RMCHQ"
    elif doc.company == "Regency Specialized Polyclinic For Dialysis and Chemotherapy":
        warehouse = "A Block Ground Floor Pharmacy - RSPDC"
    elif doc.company == "Regency Specialised Polyclinic":
        warehouse = "Ground Floor Pharmacy - RSP"
    else:
        frappe.throw(
            f"Sales order can not be created because of unkown warehouse to use for company: {doc.company}"
        )

    drug_items, lab_items, rpt_items = get_items_from_encounter(doc, warehouse)
    if len(drug_items) > 0:
        drug_order_name = create_sales_order_from_encounter(doc, drug_items, warehouse)
        if drug_order_name:
            frappe.msgprint("<b>Sales Order for Drug Items created Successfully</b>")

    if len(lab_items) > 0:
        lab_order_name = create_sales_order_from_encounter(doc, lab_items, warehouse)
        if lab_order_name:
            frappe.msgprint("<b>Sales Order for Lab Items created Successfully</b>")

    if len(rpt_items) > 0:
        rpt_order_name = create_sales_order_from_encounter(doc, rpt_items, warehouse)
        if rpt_order_name:
            frappe.msgprint(
                "<b>Sales Order for Radiology/Procedure/Therapy Items created Successfully</b>"
            )


def get_items_from_encounter(doc, warehouse):
    drug_items = []
    lab_items = []
    rpt_items = []
    for field in get_childs_map():
        for row in doc.get(field.get("table")):
            if (
                row.prescribe == 0
                or row.is_not_available_inhouse == 1
                or row.is_cancelled == 1
            ):
                continue

            item_code = frappe.get_value(
                field.get("template"), row.get(field.get("item_field")), "item"
            )
            item_name, item_description = frappe.get_value(
                "Item", item_code, ["item_name", "description"]
            )

            new_row = {
                "item_code": item_code,
                "item_name": item_name,
                "description": item_description,
                "qty": 1,
                "delivery_date": nowdate(),
                "warehouse": warehouse,
                "reference_dt": row.get("doctype"),
                "reference_dn": row.get("name"),
            }
            if row.doctype == "Drug Prescription":
                dosage = ", <br>".join(
                    [
                        "frequency: "
                        + str(row.get("dosage") or "No Prescription Dosage"),
                        "period: " + str(row.get("period") or "No Prescription Period"),
                        "dosage_form: " + str(row.get("dosage_form") or ""),
                        "interval: " + str(row.get("interval") or ""),
                        "interval_uom: " + str(row.get("interval_uom") or ""),
                        "medical_code: " + str(row.get("medical_code") or "No medical code"),
                        "Doctor's comment: "
                        + (row.get("comment") or "Take medication as per dosage."),
                    ]
                )
                new_row.update(
                    {"dosage_info": dosage, "qty": row.quantity - row.quantity_returned}
                )
                drug_items.append(new_row)

            elif row.doctype == "Lab Prescription":
                lab_items.append(new_row)

            else:
                rpt_items.append(new_row)

    return drug_items, lab_items, rpt_items


def create_sales_order_from_encounter(doc, items, warehouse):
    price_list = frappe.get_value(
        "Mode of Payment", doc.get("mode_of_payment"), "price_list"
    )
    if not price_list:
        price_list = frappe.get_value(
            "Company", doc.get("company"), "default_price_list"
        )
    if not price_list:
        frappe.throw("Please set Price List in Mode of Payment or Company")

    mobile = frappe.get_value("Patient", doc.get("patient"), "mobile")
    order_doc = frappe.new_doc("Sales Order")
    customer = frappe.get_value("Patient", doc.get("patient"), "customer")
    order_doc.update(
        {
            "company": doc.get("company"),
            "customer": customer,
            "patient": doc.get("patient"),
            "patient_name": doc.get("patient_name"),
            "patient_mobile_number": mobile,
            "transaction_date": nowdate(),
            "delivery_date": nowdate(),
            "price_list": price_list,
            "set_warehouse": warehouse,
            "items": items,
            "healthcare_service_unit": doc.get("healthcare_service_unit"),
            "healthcare_practitioner": doc.get("practitioner"),
            # "department": doc.get("medical_department"),
        }
    )
    order_doc.save(ignore_permissions=True)
    order_doc.reload()
    return order_doc.name
