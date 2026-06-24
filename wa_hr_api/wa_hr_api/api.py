from datetime import datetime
from typing import Any, Dict, Optional

import frappe
from frappe.utils import getdate, now_datetime, today


def _get_settings():
	return frappe.get_single("WA HR API Settings")


def _unauthorized(message: str = "Unauthorized") -> Dict[str, Any]:
	frappe.response["http_status_code"] = 401
	return {"status": "error", "message": message}


def _check_api_key() -> bool:
	settings = _get_settings()
	if not settings.enabled:
		return False

	secret = settings.get_password("api_secret_key", raise_exception=False)
	if not secret:
		return False

	# Note: "Authorization" header is intentionally not supported here — Frappe's own
	# auth middleware intercepts "Authorization: Bearer ..." before whitelisted methods
	# run (even with allow_guest=True), so a custom header is required.
	header_key = frappe.get_request_header("X-Api-Key")
	return bool(header_key) and header_key == secret


def _get_employee_by_phone(phone_number: str) -> Optional[Dict[str, Any]]:
	employees = frappe.get_all(
		"Employee",
		filters={"cell_number": phone_number, "status": "Active"},
		fields=["name", "employee_name", "department", "company", "cell_number"],
		limit=1,
	)
	print("e", employees)
	return employees[0] if employees else None


def _determine_log_type(employee_id: str) -> str:
	cur_date = today()
	logs = frappe.get_all(
		"Employee Checkin",
		filters={
			"employee": employee_id,
			"time": ["between", [f"{cur_date} 00:00:00", f"{cur_date} 23:59:59"]],
		},
		fields=["log_type"],
		order_by="creation asc",
	)
	if not logs:
		return "IN"

	has_in = any(log.log_type == "IN" for log in logs)
	has_out = any(log.log_type == "OUT" for log in logs)
	if has_in and has_out:
		frappe.throw("Sudah melakukan Clock In dan Clock Out hari ini.", frappe.ValidationError)

	return "OUT" if logs[-1].log_type == "IN" else "IN"

@frappe.whitelist(allow_guest=True)
def create_checkin() -> Dict[str, Any]:
	"""
	API POST untuk membuat Employee Checkin (clock in / clock out otomatis terdeteksi).
	Dipanggil oleh WhatsApp gateway/bot.

	POST /api/method/wa_hr_api.api.create_checkin
	Header: X-Api-Key: <api_secret_key>
	Body:
	{
		"phone_number": "string",
		"latitude": float,    # optional
		"longitude": float    # optional
	}
	"""
	if not _check_api_key():
		return _unauthorized()

	data = frappe.request.get_json() or {}
	phone_number = data.get("phone_number")
	latitude = data.get("latitude")
	longitude = data.get("longitude")

	if not phone_number:
		frappe.response["http_status_code"] = 400
		return {"status": "error", "message": "Field 'phone_number' diperlukan"}

	original_user = frappe.session.user
	try:
		frappe.set_user("Administrator")

		employee = _get_employee_by_phone(phone_number)
		if not employee:
			frappe.response["http_status_code"] = 404
			return {
				"status": "error",
				"message": f"Employee dengan nomor HP {phone_number} tidak ditemukan",
			}

		log_type = _determine_log_type(employee["name"])
		checkin_time = now_datetime()

		checkin_data = {
			"doctype": "Employee Checkin",
			"employee": employee["name"],
			"log_type": log_type,
			"time": checkin_time,
			"device_id": "whatsapp-bot",
		}
		if latitude is not None and longitude is not None:
			checkin_data["latitude"] = latitude
			checkin_data["longitude"] = longitude

		checkin = frappe.get_doc(checkin_data)
		checkin.insert(ignore_permissions=True)
		frappe.db.commit()

		frappe.response["http_status_code"] = 201
		return {
			"status": "success",
			"message": "Clock In berhasil" if log_type == "IN" else "Clock Out berhasil",
			"data": {
				"employee": employee["name"],
				"employee_name": employee["employee_name"],
				"log_type": log_type,
				"checkin_time": str(checkin_time),
				"checkin_name": checkin.name,
			},
		}
	except frappe.ValidationError as e:
		frappe.response["http_status_code"] = 400
		return {"status": "error", "message": str(e)}
	except Exception as e:
		frappe.log_error(title="wa_hr_api.create_checkin failed")
		frappe.response["http_status_code"] = 500
		return {"status": "error", "message": f"Error: {str(e)}"}
	finally:
		frappe.set_user(original_user)


@frappe.whitelist(allow_guest=True)
def create_leave_application() -> Dict[str, Any]:
	"""
	API POST untuk membuat Leave Application, dengan validasi saldo cuti.
	Dipanggil oleh WhatsApp gateway/bot.

	POST /api/method/wa_hr_api.api.create_leave_application
	Header: X-Api-Key: <api_secret_key>
	Body:
	{
		"phone_number": "string",
		"leave_type": "string",
		"start_date": "YYYY-MM-DD",
		"end_date": "YYYY-MM-DD",
		"description": "string"   # optional
	}
	"""
	if not _check_api_key():
		return _unauthorized()

	data = frappe.request.get_json() or {}
	phone_number = data.get("phone_number")
	leave_type = data.get("leave_type")
	start_date = data.get("start_date")
	end_date = data.get("end_date")
	description = data.get("description", "")

	if not all([phone_number, leave_type, start_date, end_date]):
		frappe.response["http_status_code"] = 400
		return {
			"status": "error",
			"message": "Field required: phone_number, leave_type, start_date, end_date",
		}

	original_user = frappe.session.user
	try:
		frappe.set_user("Administrator")

		employee = _get_employee_by_phone(phone_number)
		if not employee:
			frappe.response["http_status_code"] = 404
			return {
				"status": "error",
				"message": f"Employee dengan nomor HP {phone_number} tidak ditemukan",
			}

		employee_id = employee["name"]

		if not frappe.db.exists("Leave Type", leave_type):
			frappe.response["http_status_code"] = 400
			return {"status": "error", "message": f"Leave Type '{leave_type}' tidak ditemukan"}

		leave_allocation = frappe.get_all(
			"Leave Allocation",
			filters={
				"employee": employee_id,
				"leave_type": leave_type,
				"docstatus": 1,
				"from_date": ["<=", start_date],
				"to_date": [">=", end_date],
			},
			fields=["name", "total_leaves_allocated"],
			limit=1,
		)
		if not leave_allocation:
			frappe.response["http_status_code"] = 400
			return {
				"status": "error",
				"message": f"Leave Allocation tidak ditemukan untuk Leave Type '{leave_type}' pada tanggal yang diminta",
			}

		allocated = leave_allocation[0]["total_leaves_allocated"]

		net_balance = frappe.db.sql(
			"""
			SELECT SUM(leaves) as net_balance FROM `tabLeave Ledger Entry`
			WHERE employee = %s AND leave_type = %s AND docstatus = 1
			""",
			(employee_id, leave_type),
			as_dict=True,
		)
		remaining = net_balance[0].get("net_balance") or 0

		days_needed = (getdate(end_date) - getdate(start_date)).days + 1

		if remaining < days_needed:
			frappe.response["http_status_code"] = 400
			return {
				"status": "error",
				"message": f"Sisa cuti tidak cukup. Dibutuhkan {days_needed} hari, tersedia {remaining} hari",
				"data": {
					"allocated": allocated,
					"remaining": remaining,
					"days_needed": days_needed,
				},
			}

		leave_app = frappe.get_doc(
			{
				"doctype": "Leave Application",
				"employee": employee_id,
				"leave_type": leave_type,
				"from_date": start_date,
				"to_date": end_date,
				"description": description,
				"status": "Open",
			}
		)
		leave_app.insert(ignore_permissions=True)
		frappe.db.commit()

		frappe.response["http_status_code"] = 201
		return {
			"status": "success",
			"message": "Leave Application berhasil dibuat",
			"data": {
				"leave_application_id": leave_app.name,
				"employee": employee_id,
				"employee_name": employee["employee_name"],
				"leave_type": leave_type,
				"from_date": start_date,
				"to_date": end_date,
				"status": "Open",
				"leave_balance": {
					"allocated": allocated,
					"remaining": remaining - days_needed,
					"days_applied": days_needed,
				},
			},
		}
	except frappe.ValidationError as e:
		frappe.response["http_status_code"] = 400
		return {"status": "error", "message": f"Validation Error: {str(e)}"}
	except Exception as e:
		frappe.log_error(title="wa_hr_api.create_leave_application failed")
		frappe.response["http_status_code"] = 500
		return {"status": "error", "message": f"Error: {str(e)}"}
	finally:
		frappe.set_user(original_user)


@frappe.whitelist(allow_guest=True)
def check_leave_balance() -> Dict[str, Any]:
	"""
	API POST untuk mengecek sisa cuti employee berdasarkan nomor HP.
	Dipanggil oleh WhatsApp gateway/bot.

	POST /api/method/wa_hr_api.api.check_leave_balance
	Header: X-Api-Key: <api_secret_key>
	Body:
	{
		"phone_number": "string"
	}
	"""
	if not _check_api_key():
		return _unauthorized()

	data = frappe.request.get_json() or {}
	phone_number = data.get("phone_number")

	if not phone_number:
		frappe.response["http_status_code"] = 400
		return {"status": "error", "message": "Field 'phone_number' diperlukan"}

	original_user = frappe.session.user
	try:
		frappe.set_user("Administrator")

		employee = _get_employee_by_phone(phone_number)
		if not employee:
			frappe.response["http_status_code"] = 404
			return {
				"status": "error",
				"message": f"Employee dengan nomor HP {phone_number} tidak ditemukan",
			}

		employee_id = employee["name"]
		current_date = datetime.now().date()

		leave_allocations = frappe.get_all(
			"Leave Allocation",
			filters={"employee": employee_id, "docstatus": 1},
			fields=["leave_type", "total_leaves_allocated", "from_date", "to_date"],
		)

		leave_balance = {}
		for allocation in leave_allocations:
			if not (allocation["from_date"] <= current_date <= allocation["to_date"]):
				continue

			leave_type = allocation["leave_type"]
			net_balance = frappe.db.sql(
				"""
				SELECT SUM(leaves) as net_balance FROM `tabLeave Ledger Entry`
				WHERE employee = %s AND leave_type = %s AND docstatus = 1
				""",
				(employee_id, leave_type),
				as_dict=True,
			)
			remaining = net_balance[0].get("net_balance") or 0
			allocated = allocation["total_leaves_allocated"]

			leave_balance[leave_type] = {
				"allocated": allocated,
				"taken": allocated - remaining,
				"remaining": remaining,
			}

		frappe.response["http_status_code"] = 200
		return {
			"status": "success",
			"message": "Data sisa cuti berhasil diambil",
			"data": {
				"employee_id": employee_id,
				"employee_name": employee["employee_name"],
				"department": employee["department"],
				"leave_balance": leave_balance,
			},
		}
	except Exception as e:
		frappe.log_error(title="wa_hr_api.check_leave_balance failed")
		frappe.response["http_status_code"] = 500
		return {"status": "error", "message": f"Error: {str(e)}"}
	finally:
		frappe.set_user(original_user)
