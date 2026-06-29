import json
from datetime import datetime
from typing import Any, Dict

import frappe
import requests
from frappe import _
from frappe.utils import now_datetime

OCR_SERVICE_URL = "https://ocr-service.aluesagd.com/upload-cv"


def auto_process_cv_with_ocr(doc, method=None) -> None:
	"""
	Hook: after_insert pada Job Applicant.
	Kalau resume sudah terlampir saat record dibuat, jalankan OCR otomatis
	di background job supaya proses insert tidak menunggu OCR service eksternal.
	"""
	if not doc.resume_attachment or doc.is_ocr_processed:
		return

	frappe.enqueue(
		"wa_hr_api.recruitment.process_cv_with_ocr",
		queue="short",
		applicant=doc.name,
		enqueue_after_commit=True,
	)


@frappe.whitelist()
def process_cv_with_ocr(applicant: str) -> Dict[str, Any]:
	"""
	Kirim resume yang terlampir di Job Applicant ke OCR service eksternal,
	lalu simpan data hasil ekstraksi (nama, email, skills, dll) ke doc.

	Dipanggil dari tombol "Process CV with OCR" di form Job Applicant.
	"""
	doc = frappe.get_doc("Job Applicant", applicant)
	doc.check_permission("write")

	if not doc.resume_attachment:
		frappe.throw(_("No CV file attached. Please upload a CV first."))

	file_doc = _get_resume_file(doc)
	if not file_doc.file_name.lower().endswith(".pdf"):
		frappe.throw(_("No PDF file found. Please upload a CV in PDF format."))

	file_binary = file_doc.get_content()

	try:
		response = requests.post(
			OCR_SERVICE_URL,
			files={"file": (file_doc.file_name, file_binary, "application/pdf")},
			timeout=30,
		)
		response.raise_for_status()
		ocr_data = response.json()
	except requests.exceptions.ConnectionError:
		frappe.throw(_("Cannot connect to OCR service. Please check the service URL and try again."))
	except requests.exceptions.Timeout:
		frappe.throw(_("OCR service request timed out. Please try again."))
	except requests.exceptions.RequestException as e:
		frappe.throw(_("Error processing CV: {0}").format(str(e)))
	except (ValueError, json.JSONDecodeError):
		frappe.throw(_("Invalid response from OCR service. Please try again."))

	_update_applicant_with_ocr_data(doc, ocr_data)

	return {"status": "success", "data": ocr_data}


def _get_resume_file(doc):
	file_name = frappe.db.get_value(
		"File",
		{"file_url": doc.resume_attachment, "attached_to_name": doc.name},
		"name",
	)
	if not file_name:
		frappe.throw(_("Could not find the attached resume file."))
	return frappe.get_doc("File", file_name)


def _update_applicant_with_ocr_data(doc, ocr_data: Dict[str, Any]) -> None:
	data_section = ocr_data.get("data", {})

	ocr_timestamp = now_datetime()
	timestamp_str = ocr_data.get("timestamp")
	if timestamp_str:
		try:
			ocr_timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
		except ValueError:
			pass

	doc.cv_id = ocr_data.get("cv_id", "")
	doc.ocr_filename = ocr_data.get("filename", "")
	doc.extracted_name = data_section.get("nama", "")
	doc.extracted_email = data_section.get("email", "")
	doc.extracted_phone = data_section.get("phone", "")
	doc.extracted_skills = "\n".join(data_section.get("skills", []))
	doc.extracted_education = "\n".join(data_section.get("education", []))
	doc.extracted_job_titles = "\n".join(data_section.get("job_titles", []))
	doc.years_experience = data_section.get("years_experience", 0)
	doc.raw_preview = data_section.get("raw_preview", "")
	doc.ocr_status = ocr_data.get("status", "")
	doc.ocr_timestamp = ocr_timestamp
	doc.is_ocr_processed = 1

	if not doc.applicant_name and doc.extracted_name:
		doc.applicant_name = doc.extracted_name

	if not doc.email_id and doc.extracted_email:
		doc.email_id = doc.extracted_email

	doc.save()
