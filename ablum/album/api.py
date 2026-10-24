# Copyright (c) 2026, xball and contributors
# For license information, please see license.txt

"""Desk calls. Every method checks Album permissions before it reads or writes."""

from __future__ import annotations

import frappe
from frappe.utils import cint

from ablum.album.access import person_to_reuse, points_for_map
from ablum.album.exif import read_exif_bytes
from ablum.album.geo import point_geojson


@frappe.whitelist()
def library():
	frappe.has_permission("Photo", "read", throw=True)
	return {"photos": _photo_rows(), "people": _people()}


@frappe.whitelist()
def albums():
	frappe.has_permission("Photo Album", "read", throw=True)
	rows = frappe.get_list(
		"Photo Album",
		fields=["name", "title", "description", "privacy", "cover", "share_token"],
		order_by="modified desc",
		limit_page_length=500,
	)
	counts = _album_counts([row.name for row in rows])
	for row in rows:
		row["photo_count"] = counts.get(row.name, 0)
		row["share_url"] = _share_url(row) if row.privacy == "Public" else ""
		row.pop("share_token", None)
	return {"albums": rows}


@frappe.whitelist()
def album_photos(album: str):
	frappe.has_permission("Photo Album", "read", doc=album, throw=True)
	doc = frappe.get_doc("Photo Album", album)
	names = [row.photo for row in doc.photos if row.photo]
	photos = [row for row in _photo_rows() if row["name"] in set(names)]
	photos.sort(key=lambda row: names.index(row["name"]) if row["name"] in names else 0)
	return {
		"album": {
			"name": doc.name,
			"title": doc.title,
			"description": doc.description,
			"privacy": doc.privacy,
			"share_url": _share_url(doc) if doc.privacy == "Public" else "",
		},
		"photos": photos,
	}


@frappe.whitelist()
def map_photos():
	frappe.has_permission("Photo", "read", throw=True)
	return {"photos": points_for_map(_photo_rows())}


@frappe.whitelist()
def upload_photo():
	"""Save one image from the original upload, then create its Photo."""
	frappe.has_permission("Photo", "create", throw=True)
	upload = (frappe.request.files or {}).get("file")
	if not upload:
		frappe.throw(frappe._("Choose an image."))
	content = upload.read()
	meta = read_exif_bytes(content)
	file_doc = frappe.get_doc(
		{
			"doctype": "File",
			"file_name": upload.filename or "photo.jpg",
			"is_private": 1,
			"content": content,
		}
	)
	file_doc.save()
	photo = frappe.new_doc("Photo")
	photo.image = file_doc.file_url
	if meta.get("taken_on"):
		photo.taken_on = meta["taken_on"]
	if meta.get("latitude") is not None and meta.get("longitude") is not None:
		photo.latitude = meta["latitude"]
		photo.longitude = meta["longitude"]
		photo.location = point_geojson(meta["latitude"], meta["longitude"])
	photo.insert()
	_attach_private(photo)
	return {"name": photo.name}


@frappe.whitelist()
def create_photo(file_url: str):
	frappe.has_permission("Photo", "create", throw=True)
	file_url = (file_url or "").strip()
	if not file_url:
		frappe.throw(frappe._("Choose an image."))
	photo = frappe.new_doc("Photo")
	photo.image = file_url
	photo.insert()
	_attach_private(photo)
	return {"name": photo.name}


@frappe.whitelist()
def update_caption(photo: str, caption: str = ""):
	frappe.has_permission("Photo", "write", doc=photo, throw=True)
	doc = frappe.get_doc("Photo", photo)
	doc.caption = caption or ""
	doc.save()
	return {"name": doc.name}


@frappe.whitelist()
def tag_person(photo: str, person_name: str):
	frappe.has_permission("Photo", "write", doc=photo, throw=True)
	person_name = (person_name or "").strip()
	if not person_name:
		frappe.throw(frappe._("Enter a name."))
	person = _find_or_create_person(person_name)
	doc = frappe.get_doc("Photo", photo)
	if not any(row.person == person for row in doc.people or []):
		doc.append("people", {"person": person})
		doc.save()
	return {"person": person}


@frappe.whitelist()
def untag_person(photo: str, person: str):
	frappe.has_permission("Photo", "write", doc=photo, throw=True)
	doc = frappe.get_doc("Photo", photo)
	doc.people = [row for row in (doc.people or []) if row.person != person]
	doc.save()
	return {"name": doc.name}


@frappe.whitelist()
def create_album(title: str, privacy: str = "Private"):
	frappe.has_permission("Photo Album", "create", throw=True)
	title = (title or "").strip()
	if not title:
		frappe.throw(frappe._("Enter a title."))
	if privacy not in {"Private", "Public"}:
		privacy = "Private"
	doc = frappe.get_doc({"doctype": "Photo Album", "title": title, "privacy": privacy})
	doc.insert()
	return {"name": doc.name}


@frappe.whitelist()
def add_to_album(album: str, photos):
	frappe.has_permission("Photo Album", "write", doc=album, throw=True)
	doc = frappe.get_doc("Photo Album", album)
	chosen = _name_list(photos)
	have = {row.photo for row in doc.photos if row.photo}
	for name in chosen:
		if name in have:
			continue
		if not frappe.db.exists("Photo", name):
			continue
		doc.append("photos", {"photo": name})
	doc.save()
	return {"name": doc.name}


@frappe.whitelist()
def remove_from_album(album: str, photo: str):
	frappe.has_permission("Photo Album", "write", doc=album, throw=True)
	doc = frappe.get_doc("Photo Album", album)
	doc.photos = [row for row in (doc.photos or []) if row.photo != photo]
	doc.save()
	return {"name": doc.name}


def _photo_rows() -> list[dict]:
	rows = frappe.get_list(
		"Photo",
		fields=["name", "image", "caption", "taken_on", "latitude", "longitude", "location"],
		order_by="taken_on desc",
		limit_page_length=1000,
	)
	people = _people_by_photo([row.name for row in rows])
	payload = []
	for row in rows:
		payload.append(
			{
				"name": row.name,
				"image": row.image,
				"caption": row.caption or "",
				"taken_on": str(row.taken_on or ""),
				"latitude": row.latitude if row.location else None,
				"longitude": row.longitude if row.location else None,
				"people": people.get(row.name, []),
			}
		)
	return payload


def _people_by_photo(names: list[str]) -> dict[str, list[str]]:
	if not names:
		return {}
	links = frappe.db.get_all(
		"Photo Person",
		filters={"parent": ["in", names], "parenttype": "Photo"},
		fields=["parent", "person"],
	)
	grouped: dict[str, list[str]] = {}
	for link in links:
		grouped.setdefault(link.parent, []).append(link.person)
	return grouped


def _people() -> list[str]:
	return frappe.get_list("Album Person", pluck="name", order_by="person_name asc", limit_page_length=500)


def _album_counts(names: list[str]) -> dict[str, int]:
	if not names:
		return {}
	rows = frappe.db.get_all(
		"Photo Album Photo",
		filters={"parent": ["in", names]},
		fields=["parent"],
	)
	counts: dict[str, int] = {}
	for row in rows:
		counts[row.parent] = counts.get(row.parent, 0) + 1
	return counts


def _find_or_create_person(person_name: str) -> str:
	existing = frappe.get_all("Album Person", fields=["name", "person_name"], limit_page_length=500)
	match = person_to_reuse(existing, person_name)
	if match:
		return match["name"]
	doc = frappe.get_doc({"doctype": "Album Person", "person_name": person_name})
	doc.insert()
	return doc.name


def _attach_private(photo) -> None:
	file_name = frappe.db.get_value("File", {"file_url": photo.image}, "name")
	if not file_name:
		return
	file_doc = frappe.get_doc("File", file_name)
	file_doc.attached_to_doctype = "Photo"
	file_doc.attached_to_name = photo.name
	file_doc.attached_to_field = "image"
	if not cint(file_doc.is_private):
		file_doc.is_private = 1
	file_doc.save(ignore_permissions=True)
	if file_doc.file_url != photo.image:
		photo.db_set("image", file_doc.file_url)


def _share_url(album) -> str:
	token = album.share_token if not isinstance(album, dict) else album.get("share_token")
	if not token:
		return ""
	return frappe.utils.get_url(f"/album/{token}")


def _name_list(photos) -> list[str]:
	if not photos:
		return []
	if isinstance(photos, str):
		try:
			import json

			loaded = json.loads(photos)
			photos = loaded if isinstance(loaded, list) else [photos]
		except ValueError:
			photos = [photos]
	return [name for name in photos if name]
