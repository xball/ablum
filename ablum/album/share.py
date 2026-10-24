# Copyright (c) 2026, xball and contributors
# For license information, please see license.txt

"""Guest view of one public album. The file is opened only after the checks pass."""

from __future__ import annotations

import mimetypes
import os
from urllib.parse import quote

import frappe

from ablum.album.access import guest_can_view, photo_is_member, points_for_map


def public_album(token: str | None) -> dict | None:
	if not token:
		return None
	row = frappe.db.get_value(
		"Photo Album",
		{"share_token": token},
		["name", "title", "description", "privacy", "share_token"],
		as_dict=True,
	)
	if not row or not guest_can_view(row.privacy, row.share_token, token):
		return None
	members = frappe.db.get_all(
		"Photo Album Photo",
		filters={"parent": row.name},
		fields=["photo"],
		order_by="idx asc",
	)
	names = [member.photo for member in members if member.photo]
	photos = _public_photos(names, token)
	return {
		"title": row.title,
		"description": row.description or "",
		"photos": photos,
		"map": points_for_map(photos),
	}


def shared_file(token: str | None, photo: str | None) -> str | None:
	"""Return a file path only when the album is public and the photo is in it."""
	if not token or not photo:
		return None
	row = frappe.db.get_value(
		"Photo Album",
		{"share_token": token},
		["name", "privacy", "share_token"],
		as_dict=True,
	)
	if not row or not guest_can_view(row.privacy, row.share_token, token):
		return None
	members = frappe.db.get_all("Photo Album Photo", filters={"parent": row.name}, pluck="photo")
	if not photo_is_member(members, photo):
		return None
	file_url = frappe.db.get_value("Photo", photo, "image")
	return _safe_path(file_url)


@frappe.whitelist(allow_guest=True)
def image(token: str, photo: str):
	path = shared_file(token, photo)
	if not path:
		frappe.throw(frappe._("This album is not available."), frappe.PermissionError)
	with open(path, "rb") as handle:
		content = handle.read()
	frappe.local.response.filename = os.path.basename(path)
	frappe.local.response.filecontent = content
	frappe.local.response.type = "download"
	frappe.local.response.display_content_as = "inline"
	content_type = mimetypes.guess_type(path)[0]
	if content_type:
		frappe.local.response.content_type = content_type


def _public_photos(names: list[str], token: str) -> list[dict]:
	if not names:
		return []
	rows = frappe.db.get_all(
		"Photo",
		filters={"name": ["in", names]},
		fields=["name", "caption", "taken_on", "latitude", "longitude", "location"],
	)
	by_name = {row.name: row for row in rows}
	links = frappe.db.get_all(
		"Photo Person",
		filters={"parent": ["in", names], "parenttype": "Photo"},
		fields=["parent", "person"],
	)
	people: dict[str, list[str]] = {}
	for link in links:
		people.setdefault(link.parent, []).append(link.person)
	ordered = []
	for name in names:
		row = by_name.get(name)
		if not row:
			continue
		ordered.append(
			{
				"name": name,
				"caption": row.caption or "",
				"taken_on": str(row.taken_on or ""),
				"latitude": row.latitude if row.location else None,
				"longitude": row.longitude if row.location else None,
				"people": people.get(name, []),
				"image": f"/api/method/ablum.album.share.image?token={quote(token)}&photo={quote(name)}",
			}
		)
	return ordered


def _safe_path(file_url: str | None) -> str | None:
	if not file_url:
		return None
	file_name = frappe.db.get_value("File", {"file_url": file_url}, "name")
	if not file_name:
		return None
	path = frappe.get_doc("File", file_name).get_full_path()
	if path and os.path.isfile(path):
		return path
	return None
