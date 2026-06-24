import frappe
from frappe.model.document import Document


class WAHRAPISettings(Document):
	def validate(self):
		if self.enabled and not self.get_password("api_secret_key", raise_exception=False):
			frappe.throw("API Secret Key is required when WA HR API is enabled")
