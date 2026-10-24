# Copyright (c) 2026, xball and contributors
# For license information, please see license.txt

import os

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime

from ablum.album.exif import read_exif
from ablum.album.geo import point_from_geojson, point_geojson


class Photo(Document):
	def validate(self):
		if self.is_new() and not self.location:
			self._apply_exif()
		if self.location:
			pin = point_from_geojson(self.location)
			if pin:
				self.latitude, self.longitude = pin
		elif not self.is_new():
			self.latitude = None
			self.longitude = None
		if not self.taken_on:
			self.taken_on = now_datetime()

	def _apply_exif(self):
		path = _image_path(self.image)
		if not path:
			return
		meta = read_exif(path)
		if meta.get("taken_on") and not self.taken_on:
			self.taken_on = meta["taken_on"]
		if meta.get("latitude") is None or meta.get("longitude") is None:
			return
		self.latitude = meta["latitude"]
		self.longitude = meta["longitude"]
		self.location = point_geojson(self.latitude, self.longitude)


def _image_path(file_url: str | None) -> str | None:
	if not file_url:
		return None
	file_name = frappe.db.get_value("File", {"file_url": file_url}, "name")
	if not file_name:
		return None
	path = frappe.get_doc("File", file_name).get_full_path()
	if path and os.path.isfile(path):
		return path
	return None
