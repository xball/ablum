# Copyright (c) 2026, xball and contributors
# For license information, please see license.txt

import frappe


def ensure_role():
	"""Album User can use the library. System Manager already can."""
	if frappe.db.exists("Role", "Album User"):
		return
	role = frappe.new_doc("Role")
	role.role_name = "Album User"
	role.desk_access = 1
	role.insert(ignore_permissions=True)
