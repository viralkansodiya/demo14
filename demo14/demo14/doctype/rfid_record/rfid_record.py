# Copyright (c) 2024, Viral Patel and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document

class RFIDRecord(Document):
	def validate(self):
		if not self.last_scanned_time:
			self.is_scanned = 0
		if self.is_new():
			rfid_tag = self.rfid_tagging_id_asci

			hex_value = rfid_tag.encode("utf-8").hex()

			self.rfid_tagging_id = hex_value.replace(" ","")