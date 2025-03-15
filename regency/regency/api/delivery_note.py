import re
import frappe

def after_insert(doc, method):
    for row in doc.items:
        if "frequency" not in str(row.description):
            if row.si_detail:
                row.description = frappe.get_value("Sales Invoice Item", row.si_detail, "dosage_info")
    
    doc.save(ignore_permissions=True)

def on_submit(doc, method):
    if doc.form_sales_invoice and doc.patient and doc.reference_name:
        update_drug_prescription(doc)


def update_drug_prescription(doc):
    dni_items = []
    dn_rows_to_remove = []

    encounter_doc = frappe.get_doc("Patient Encounter", doc.reference_name)
    medical_code = str(encounter_doc.patient_encounter_final_diagnosis[0].medical_code) + "\n" + str(encounter_doc.patient_encounter_final_diagnosis[0].description)
    for row in doc.items:
        medication_details = frappe.get_value("Medication", {"item": row.item_code}, 
            ["name", "medication_name", "default_interval", "default_interval_uom",
            "default_prescription_duration", "default_dosage_form", "default_prescription_dosage", "default_comments"],
            as_dict=True
        )
        
        if not medication_details.name:
            frappe.throw(f"Item: <b>{row.item_code}</b> is not linked to any Medication. Please link item with Medication and try again.")
        
        dni_items.append(medication_details.name)

        if not row.reference_name:
            if row.description:
                frequency = re.search(r"frequency:\s*(.+)", row.description, re.MULTILINE)
                period = re.search(r"period:\s*(.+)", row.description, re.MULTILINE)
                dosage_form = re.search(r"dosage_form:\s*(.+)", row.description, re.MULTILINE)
                interval = re.search(r"interval:\s*(.+)", row.description, re.MULTILINE)
                interval_uom = re.search(r"interval_uom:\s*(.+)", row.description, re.MULTILINE)
                comment = re.search(r"Doctor's comment:\s*(.+)", row.description, re.MULTILINE)
            

            new_drug_row = {
                "drug_code": medication_details.name,
                "drug_name": medication_details.medication_name,
                "medical_code": medical_code,
                "prescribe": 1,
                "dosage": frequency.group(1) if frequency else medication_details.default_prescription_dosagge,
                "period": period.group(1) if period else medication_details.default_prescription_duration,
                "dosage_form": dosage_form.group(1) if dosage_form else medication_details.default_dosage_form,
                "interval": interval.group(1) if interval else medication_details.default_interval,
                "interval_uom": interval_uom.group(1) if interval_uom else medication_details.default_interval_uom,
                "comment": comment.group(1) if comment else medication_details.default_comment,
                "quantity": row.qty,
                "amount": row.rate,
                "dn_detail": row.name,
                "drug_prescription_created": 1,
                "deliery_quantity": row.qty,
                "invoiced": 1,
                "sales_invoice_number": doc.form_sales_invoice,
                "healthcare_service_unit": frappe.get_value("Healthcare Service Unit", 
                    {"service_unit_type": "Pharmacy", "company": doc.company, "warehouse": doc.set_warehouse}, "name"),
            }
            encounter_doc.append("drug_prescription", new_drug_row)

    for drug_row in encounter_doc.drug_prescription:
        if drug_row.prescribe == 1 and drug_row.drug_code not in dni_items:
            dn_rows_to_remove.append(drug_row)
    
    for d_row in dn_rows_to_remove:
        frappe.delete_doc(
            d_row.doctype,
            d_row.name,
            force=1,
            ignore_permissions=True,
            for_reload=True,
        )
    encounter_doc.db_update_all()
    