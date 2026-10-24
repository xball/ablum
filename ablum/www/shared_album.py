# Copyright (c) 2026, xball and contributors
# For license information, please see license.txt

import json

import frappe

from ablum.album.share import public_album

no_cache = 1


def get_context(context):
	token = frappe.form_dict.get("token")
	album = public_album(token)
	context.no_cache = 1
	context.title = album["title"] if album else "Album"
	context.album = album
	context.album_json = json.dumps(album or None).replace("<", "\\u003c")
	if not album:
		frappe.local.response["http_status_code"] = 404
