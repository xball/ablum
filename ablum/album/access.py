# Copyright (c) 2026, xball and contributors
# For license information, please see license.txt

"""Decisions that do not need the database."""

from __future__ import annotations


def guest_can_view(privacy: str | None, share_token: str | None, given_token: str | None) -> bool:
	"""A guest sees an album only when it is Public and the token matches."""
	if privacy != "Public":
		return False
	if not share_token or not given_token:
		return False
	return share_token == given_token


def points_for_map(photos: list[dict]) -> list[dict]:
	"""Photos with no location stay off the map."""
	points = []
	for photo in photos:
		if photo.get("latitude") is None or photo.get("longitude") is None:
			continue
		points.append(photo)
	return points


def person_to_reuse(existing: list[dict], typed_name: str) -> dict | None:
	"""The same name, in any letter case, is the same person."""
	wanted = (typed_name or "").strip().casefold()
	if not wanted:
		return None
	for row in existing:
		if (row.get("person_name") or "").strip().casefold() == wanted:
			return row
	return None


def photo_is_member(member_names: list[str], photo: str | None) -> bool:
	if not photo:
		return False
	return photo in set(member_names)
