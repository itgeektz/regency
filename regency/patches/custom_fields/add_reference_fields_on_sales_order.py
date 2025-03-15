from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def execute():
    feilds = {
        "Sales Invoice Item": [
            {
                "fieldname": "dosage_info",
                "label": "Dosage Information",
                "fieldtype": "Small Text",
                "insert_after": "item_name",
                "red_only": 1,
                "bold": 1,
            },
        ],
        "Sales Order": [
            {
                "fieldname": "patient",
                "label": "Patient",
                "fieldtype": "Link",
                "options": "Patient",
                "insert_after": "customer_name",
            },
            {
                "fieldname": "patient_name",
                "label": "Patient Actual Name",
                "fieldtype": "Data",
                "insert_after": "patient",
                "mandatory_depends_on": "eval: doc.customer == 'Cash Customer' ",
            },
            {
                "fieldname": "patient_mobile_number",
                "label": "Patient Mobile Number",
                "fieldtype": "Data",
                "insert_after": "patient_name",
                "depends_on": "eval: doc.customer == 'Cash Customer' ",
            },
        ],
        "Sales Order Item": [
            {
                "fieldname": "dosage_info",
                "label": "Dosage Information",
                "fieldtype": "Small Text",
                "insert_after": "item_name",
                "red_only": 1,
                "bold": 1,
            },
            {
                "fieldname": "reference_dt",
                "label": "Reference DocType",
                "fieldtype": "Link",
                "options": "DocType",
                "insert_after": "blanket_order_rate",
                "read_only": 1,
            },
            {
                "fieldname": "reference_dn",
                "label": "Reference Name",
                "fieldtype": "Dynamic Link",
                "options": "reference_dt",
                "insert_after": "reference_dt",
                "read_only": 1,
            },
        ]
    }
    create_custom_fields(feilds, update=True)