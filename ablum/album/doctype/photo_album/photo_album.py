# Copyright (c) 2026, xball and contributors
# For license information, please see license.txt

import secrets

import frappe
from frappe.model.document import Document


class PhotoAlbum(Document):
	def validate(self):
		if not self.privacy:
			self.privacy = "Private"
		if not self.share_token:
			self.share_token = secrets.token_urlsafe(18)
		first = next((row.photo for row in (self.photos or []) if row.photo), None)
		self.cover = frappe.db.get_value("Photo", first, "image") if first else None
