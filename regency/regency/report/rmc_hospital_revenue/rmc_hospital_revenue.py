# Copyright (c) 2023, Aakvatech and contributors
# For license information, please see license.txt

import frappe
from frappe import msgprint, _


def execute(filters=None):
    columns = get_columns(filters)

    data = []

    app_data = get_insurance_appointment_transactions(filters)
    lab_data = get_insurance_lab_transactions(filters)
    rad_data = get_insurance_radiology_transactions(filters)
    proc_data = get_insurance_procedure_transactions(filters)
    drug_data = get_insurance_drug_transactions(filters)
    ther_data = get_insurance_therapy_transactions(filters)
    inptient_occupancy_data = get_insurance_transactions_for_inpatient_occupancy(
        filters
    )
    inpatient_consultance_data = get_insurance_transactions_for_inpatient_consultancy(
        filters
    )
    # cash_transaction_data = get_cash_transactions(filters)

    if app_data:
        data += app_data
    if lab_data:
        data += lab_data
    if rad_data:
        data += rad_data
    if proc_data:
        data += proc_data
    if drug_data:
        data += drug_data
    if ther_data:
        data += ther_data
    if inptient_occupancy_data:
        data += inptient_occupancy_data
    if inpatient_consultance_data:
        data += inpatient_consultance_data
    # if cash_transaction_data:
    #     data += cash_transaction_data

    return columns, data


def get_columns(filters):
    columns = [
        {"fieldname": "year", "fieldtype": "Int", "label": _("Year")},
        {"fieldname": "month", "fieldtype": "Data", "label": _("Month")},
        {
            "fieldname": "healthcare_practitioner",
            "fieldtype": "Data",
            "label": _("Practitioner"),
        },
        {
            "fieldname": "healthcare_practitioner_type",
            "fieldtype": "Data",
            "label": _("Practitioner Type"),
        },
        {
            "fieldname": "practitioner_hsu",
            "fieldtype": "Data",
            "label": _("Practitioner HSU"),
        },
        {
            "fieldname": "department_hsu",
            "fieldtype": "Data",
            "label": _("Department HSU"),
        },
        {"fieldname": "amount", "fieldtype": "Currency", "label": _("Amount")},
        {"fieldname": "department", "fieldtype": "Data", "label": _("Department")},
        {"fieldname": "payment_mode", "fieldtype": "Data", "label": _("Payment Mode")},
        {"fieldname": "speciality", "fieldtype": "Data", "label": _("Speciality")},
        {
            "fieldname": "main_department",
            "fieldtype": "Data",
            "label": _("Main Department"),
        },
        {"fieldname": "status", "fieldtype": "Data", "label": _("Status")},
    ]
    return columns


# Patient Consultanct Fees From Insurances
def get_insurance_appointment_transactions(filters):
    conditions = ""
    if filters.get("from_date"):
        conditions += "AND date(pa.appointment_date) >= %(from_date)s"
    if filters.get("to_date"):
        conditions += "AND date(pa.appointment_date) <= %(to_date)s"
    if filters.get("company"):
        conditions += "AND pa.company = %(company)s"

    data = frappe.db.sql(
        """
	    SELECT 
			YEAR(pa.appointment_date) AS year,
			MONTHNAME(pa.appointment_date) AS month,
			pa.practitioner AS healthcare_practitioner,
			hp.healthcare_practitioner_type AS healthcare_practitioner_type,
			pa.service_unit AS practitioner_hsu,
			pa.service_unit AS department_hsu,
			SUM(pa.paid_amount) AS amount,
			"Consultation" AS department,
			pa.coverage_plan_name AS payment_mode, 
			hp.department AS speciality,
			md.main_department AS main_department,
			"Submitted" AS status
		FROM `tabPatient Appointment` pa 
			INNER JOIN `tabHealthcare Practitioner` hp ON pa.practitioner = hp.name
			LEFT OUTER JOIN `tabMedical Department` md ON hp.department = md.name
		WHERE pa.status = 'Closed' 
		AND pa.insurance_subscription != ""
		AND pa.follow_up = 0 {conditions}
		GROUP BY 
			YEAR(pa.appointment_date), 
			MONTHNAME(pa.appointment_date), 
			pa.practitioner,
			hp.healthcare_practitioner_type,
			pa.service_unit, 
			pa.coverage_plan_name,
			hp.department,
			md.main_department
	""".format(
            conditions=conditions
        ),
        filters,
        as_dict=1,
    )
    return data


# Lab Revenue From Insurances
def get_insurance_lab_transactions(filters):
    conditions = get_conditions(filters)

    data = frappe.db.sql(
        """
	    SELECT 
			YEAR(pe.encounter_date) AS year, 
			MONTHNAME(pe.encounter_date) AS month, 
			pe.practitioner AS healthcare_practitioner,
			hp.healthcare_practitioner_type AS healthcare_practitioner_type,
			pe.healthcare_service_unit AS practitioner_hsu, 
			hsp.department_hsu AS department_hsu, 
			SUM(hsp.amount) AS amount, 
			"Lab" AS department, 
			pe.insurance_coverage_plan AS payment_mode, 
			hp.department AS speciality,
			md.main_department AS main_department,
			IF(hs_doc.docstatus = 1, "Submitted", "Draft") AS status
		FROM `tabLab Prescription` hsp
			INNER JOIN `tabPatient Encounter` pe ON hsp.parent = pe.name
			INNER JOIN `tabHealthcare Practitioner` hp ON pe.practitioner = hp.name
			LEFT OUTER JOIN `tabMedical Department` md ON hp.department = md.name
			LEFT OUTER JOIN `tabLab Test` hs_doc ON hsp.lab_test = hs_doc.name
		WHERE hsp.is_not_available_inhouse = 0
		AND hsp.is_cancelled = 0
		AND hsp.prescribe = 0 {conditions}
		GROUP BY 
			year(pe.encounter_date), 
			monthname(pe.encounter_date), 
			pe.practitioner,
			hp.healthcare_practitioner_type,
			pe.healthcare_service_unit, 
			hsp.department_hsu, 
			pe.insurance_coverage_plan,
			hp.department,
			md.main_department,
			hs_doc.docstatus
	""".format(
            conditions=conditions
        ),
        filters,
        as_dict=1,
    )
    return data


# Radiology Revenue From Insurances
def get_insurance_radiology_transactions(filters):
    conditions = get_conditions(filters)

    data = frappe.db.sql(
        """
	    SELECT 
			YEAR(pe.encounter_date) AS year, 
			MONTHNAME(pe.encounter_date) AS month, 
			pe.practitioner AS healthcare_practitioner,
			hp.healthcare_practitioner_type AS healthcare_practitioner_type,
			pe.healthcare_service_unit AS practitioner_hsu, 
			hsp.department_hsu AS department_hsu, 
			SUM(hsp.amount) AS amount, 
			"Radiology" AS department, 
			pe.insurance_coverage_plan AS payment_mode, 
			hp.department AS speciality,
			md.main_department AS main_department,
			IF(hs_doc.docstatus = 1, "Submitted", "Draft") AS status
		FROM `tabRadiology Procedure Prescription` hsp
			INNER JOIN `tabPatient Encounter` pe ON hsp.parent = pe.name
			INNER JOIN `tabHealthcare Practitioner` hp ON pe.practitioner = hp.name
			LEFT OUTER JOIN `tabMedical Department` md ON hp.department = md.name
			LEFT OUTER JOIN `tabRadiology Examination` hs_doc ON hsp.radiology_examination = hs_doc.name
		WHERE hsp.is_not_available_inhouse = 0 
		AND hsp.is_cancelled = 0
		AND hsp.prescribe = 0 {conditions}
		GROUP BY 
			year(pe.encounter_date), 
			month(pe.encounter_date), 
			pe.practitioner,
			hp.healthcare_practitioner_type,
			pe.healthcare_service_unit, 
			hsp.department_hsu, 
			pe.insurance_coverage_plan,
			hp.department,
			md.main_department,
			hs_doc.docstatus
	""".format(
            conditions=conditions
        ),
        filters,
        as_dict=1,
    )
    return data


# Clinical Procedure Revenue From Insurances
def get_insurance_procedure_transactions(filters):
    conditions = get_conditions(filters)

    return frappe.db.sql(
        """
		SELECT 
			YEAR(pe.encounter_date) AS year, 
			MONTHNAME(pe.encounter_date) AS month, 
			pe.practitioner AS healthcare_practitioner,
			hp.healthcare_practitioner_type AS healthcare_practitioner_type,
			pe.healthcare_service_unit AS practitioner_hsu, 
			hsp.department_hsu AS department_hsu, 
			SUM(hsp.amount) AS amount, 
			"Clinical Procedure" AS department, 
			pe.insurance_coverage_plan AS payment_mode, 
			hp.department AS speciality,
			md.main_department AS main_department,
			IF(hs_doc.docstatus = 1, "Submitted", "Draft") AS status
		FROM `tabProcedure Prescription` hsp
			INNER JOIN `tabPatient Encounter` pe ON pe.name = hsp.parent
			INNER JOIN `tabHealthcare Practitioner` hp ON pe.practitioner = hp.name
			LEFT OUTER JOIN `tabMedical Department` md ON hp.department = md.name
			LEFT OUTER JOIN `tabClinical Procedure` hs_doc ON hsp.clinical_procedure = hs_doc.name
		WHERE hsp.is_not_available_inhouse = 0
		AND hsp.is_cancelled = 0
		AND hsp.prescribe = 0 {conditions}
		GROUP BY 
			YEAR(pe.encounter_date), 
			MONTH(pe.encounter_date), 
			pe.practitioner,
			hp.healthcare_practitioner_type,
			pe.healthcare_service_unit, 
			hsp.department_hsu, 
			pe.insurance_coverage_plan,
			hp.department,
			md.main_department,
			hs_doc.docstatus
	""".format(
            conditions=conditions
        ),
        filters,
        as_dict=1,
    )


# Drug Prescription From Insurances
def get_insurance_drug_transactions(filters):
    conditions = get_conditions(filters)

    data = frappe.db.sql(
        """
		SELECT 
			YEAR(pe.encounter_date) AS year,
			MONTHNAME(pe.encounter_date) AS month,
			pe.practitioner AS healthcare_practitioner,
			hp.healthcare_practitioner_type AS healthcare_practitioner_type,
			pe.healthcare_service_unit AS practitioner_hsu,
			hsp.healthcare_service_unit  AS department_hsu, 
			SUM(hsp.amount * (hsp.quantity - hsp.quantity_returned)) AS amount, 
			"Medication" AS department,
			pe.insurance_coverage_plan AS payment_mode, 
			hp.department AS speciality,
			md.main_department AS main_department,
			IF(dn_detail IS NULL, "Draft", "Submitted") AS status
		FROM `tabDrug Prescription` hsp
			INNER JOIN `tabPatient Encounter` pe ON pe.name = hsp.parent
			INNER JOIN `tabHealthcare Practitioner` hp ON pe.practitioner = hp.name
			LEFT OUTER JOIN `tabMedical Department` md ON hp.department = md.name
		WHERE hsp.is_not_available_inhouse = 0
		AND hsp.is_cancelled = 0
		AND hsp.prescribe = 0 {conditions}
		GROUP BY 
			year(pe.encounter_date),
			month(pe.encounter_date),
			pe.practitioner,
			hp.healthcare_practitioner_type,
			pe.healthcare_service_unit, 
			hsp.healthcare_service_unit,
			pe.insurance_coverage_plan,
			hp.department,
			md.main_department,
			IF(dn_detail IS NULL, "Yes", "No")
	""".format(
            conditions=conditions
        ),
        filters,
        as_dict=1,
    )
    return data


# Therapy Revenue From Insurances
def get_insurance_therapy_transactions(filters):
    conditions = get_conditions(filters)

    data = frappe.db.sql(
        """
		SELECT 
			YEAR(pe.encounter_date) AS year,
			MONTHNAME(pe.encounter_date) AS month,
			pe.practitioner AS healthcare_practitioner,
			hp.healthcare_practitioner_type AS healthcare_practitioner_type,
			pe.healthcare_service_unit AS practitioner_hsu,
			hsp.department_hsu AS department_hsu,
			SUM(hsp.amount) AS amount,
			"Therapy" AS department,
			pe.insurance_coverage_plan AS payment_mode, 
			hp.department AS speciality,
			md.main_department AS main_department,
			IF(1 = 1, "Submitted", "Draft") AS status
		FROM `tabTherapy Plan Detail` hsp
			INNER JOIN `tabPatient Encounter` pe ON pe.name = hsp.parent
			INNER JOIN `tabHealthcare Practitioner` hp ON pe.practitioner = hp.name
			LEFT OUTER JOIN `tabMedical Department` md ON hp.department = md.name
		WHERE hsp.is_not_available_inhouse = 0
		AND hsp.is_cancelled = 0
		AND hsp.prescribe = 0 {conditions}
		GROUP BY 
			YEAR(pe.encounter_date),
			MONTH(pe.encounter_date),
			pe.practitioner,
			hp.healthcare_practitioner_type,
			pe.healthcare_service_unit,
			hsp.department_hsu,
			pe.insurance_coverage_plan, 
			hp.department,
			md.main_department, 1
	""".format(
            conditions=conditions
        ),
        filters,
        as_dict=1,
    )
    return data


def get_conditions(filters):
    conditions = ""

    if filters.get("from_date"):
        conditions += "AND pe.encounter_date >= %(from_date)s"
    if filters.get("to_date"):
        conditions += "AND pe.encounter_date <= %(to_date)s"
    if filters.get("company"):
        conditions += "AND pe.company = %(company)s "
        conditions += "AND pe.docstatus = 1 "

    return conditions


# IPD Bed Charges From Insurances
def get_insurance_transactions_for_inpatient_occupancy(filters):
    # enc_conditions = get_conditions(filters)
    # ipd_conditions = get_ipd_conditions(filters)

    data = frappe.db.sql(
        """
		SELECT 
			YEAR(DATE(ipd_occ.check_in)) AS year,
			MONTHNAME(DATE(ipd_occ.check_in)) AS month,
			null AS healthcare_practitioner,
			null AS healthcare_practitioner_type,
			null AS practitioner_hsu,
			ipd_occ.service_unit AS department_hsu,
			SUM(ipd_occ.amount) as amount, 
			"IPD" AS department,
			pa.coverage_plan_name AS payment_mode,
			hsut.item_group AS speciality,
			null AS main_department,
			"Confirmed" AS status
		FROM `tabInpatient Occupancy` ipd_occ
			INNER JOIN `tabInpatient Record` ipd_rec ON ipd_occ.parent = ipd_rec.name
			INNER JOIN `tabHealthcare Service Unit` hsu ON ipd_occ.service_unit = hsu.name
			INNER JOIN `tabHealthcare Service Unit Type` hsut ON hsu.service_unit_type = hsut.name
			INNER JOIN `tabPatient Appointment` pa ON ipd_rec.patient_appointment = pa.name
		WHERE ipd_occ.is_confirmed = 1
		AND DATE(ipd_occ.check_in) BETWEEN %(from_date)s AND %(to_date)s
		AND ipd_rec.company = %(company)s
		AND ipd_rec.insurance_subscription != ""
		GROUP BY 
			YEAR(DATE(ipd_rec.admitted_datetime)), 
			MONTHNAME(DATE(ipd_rec.admitted_datetime)), 
			ipd_occ.service_unit,
			hsut.item_group, 
			pa.coverage_plan_name
	""",
        filters,
        as_dict=1,
    )
    return data


# IPD Consultancy From Insurances
def get_insurance_transactions_for_inpatient_consultancy(filters):
    enc_conditions = get_conditions(filters)
    ipd_conditions = get_ipd_conditions(filters)

    data = frappe.db.sql(
        """
		SELECT 
			YEAR(DATE(ipd_cons.date)) AS year, 
			MONTHNAME(DATE(ipd_cons.date)) AS month,
			pe.practitioner AS healthcare_practitioner,
			hp.healthcare_practitioner_type AS healthcare_practitioner_type,
			pe.healthcare_service_unit AS practitioner_hsu, 
			null AS department_hsu,
			SUM(ipd_cons.rate) AS amount, 
			"IPD" AS department,
			pa.coverage_plan_name AS payment_mode,
			it.item_group AS speciality, 
			null AS main_department, "Confirmed" AS status
		FROM `tabInpatient Consultancy` ipd_cons
			INNER JOIN `tabInpatient Record` ipd_rec ON ipd_cons.parent = ipd_rec.name
			INNER JOIN `tabPatient Appointment` pa ON ipd_rec.patient_appointment = pa.name
			INNER JOIN `tabItem` it ON ipd_cons.consultation_item = it.item_name
			LEFT OUTER JOIN `tabPatient Encounter` pe ON ipd_cons.encounter = pe.name
			LEFT OUTER JOIN `tabHealthcare Practitioner` hp ON pe.practitioner = hp.name
		WHERE ipd_cons.is_confirmed = 1
		AND ipd_cons.date BETWEEN %(from_date)s AND %(to_date)s
		AND ipd_rec.company = %(company)s
		AND ipd_rec.insurance_subscription != ""
		GROUP BY 
			YEAR(DATE(ipd_rec.admitted_datetime)),
			MONTHNAME(DATE(ipd_rec.admitted_datetime)),
			pe.practitioner,
			hp.healthcare_practitioner_type,
			it.item_group,
			pe.healthcare_service_unit,
			pa.coverage_plan_name
	""",
        filters,
        as_dict=1,
    )
    return data


def get_ipd_conditions(filters):
    ipd_conditions = ""

    if filters.get("from_date"):
        ipd_conditions += "and DATE(ipd_rec.admitted_datetime) >= %(from_date)s"
    if filters.get("to_date"):
        ipd_conditions += "and DATE(ipd_rec.admitted_datetime) <= %(to_date)s"
    if filters.get("from_date"):
        ipd_conditions += "and ipd_rec.discharge_date >= %(from_date)s"  # Assumption
    if filters.get("to_date"):
        ipd_conditions += "and ipd_rec.discharge_date <= %(to_date)s"  # Assumption
    if filters.get("company"):
        ipd_conditions += (
            "and ipd_rec.company = %(company)s and pa.company = %(company)s"
        )

    return ipd_conditions


# Cash transactions
# Appointments, labs, radiologies, procudures, drugs, therapies,
# ipd occupancy, ipd consultancies and other sales
def get_cash_transactions(filters):
    conditions = ""
    if filters.get("from_date"):
        conditions += "AND si.posting_date >= %(from_date)s"
    if filters.get("to_date"):
        conditions += "AND si.posting_date <= %(to_date)s"
    if filters.get("company"):
        conditions += "AND si.company = %(company)s"

    data = frappe.db.sql(
        """
		SELECT
			YEAR(si.posting_date) AS year,
			MONTHNAME(si.posting_date) AS month,
			sii.healthcare_practitioner AS healthcare_practitioner, 
			null AS practitioner_hsu,
			sii.healthcare_service_unit AS department_hsu,
			SUM(sii.amount) AS amount,
			sii.item_group AS department,
			"Cash" AS payment_mode,
			null AS speciality,
			null AS main_department,
			"Submitted" AS status
		FROM `tabSales Invoice Item` sii
		INNER JOIN `tabSales Invoice` si ON sii.parent = si.name
		WHERE si.is_pos = 1
		AND sii.docstatus = 1 {conditions}
		GROUP BY
			YEAR(si.posting_date),
			MONTHNAME(si.posting_date),
			sii.healthcare_practitioner,
			sii.healthcare_service_unit,
			sii.item_group

		UNION  ALL

		SELECT
			YEAR(si.posting_date) AS year,
			MONTHNAME(si.posting_date) AS month,
			sii.healthcare_practitioner AS healthcare_practitioner, 
			null AS practitioner_hsu,
			sii.healthcare_service_unit AS department_hsu,
			SUM(sii.amount) AS amount,
			sii.item_group AS department,
			"Cash" AS payment_mode,
			null AS speciality,
			null AS main_department,
			"Submitted" AS status
		FROM `tabSales Invoice Item` sii
		INNER JOIN `tabSales Invoice` si ON sii.parent = si.name
		WHERE si.is_pos = 0
		AND si.patient != ""
		AND sii.docstatus = 1 {conditions}
		GROUP BY
			YEAR(si.posting_date),
			MONTHNAME(si.posting_date),
			sii.healthcare_practitioner,
			sii.healthcare_service_unit,
			sii.item_group
	""".format(
            conditions=conditions
        ),
        filters,
        as_dict=1,
    )
    return data