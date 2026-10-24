# Copyright (c) 2026, xball and contributors
# For license information, please see license.txt

"""GeoJSON point used by the Frappe Geolocation field. Coordinates are longitude, latitude."""

from __future__ import annotations

import json


def point_geojson(latitude: float, longitude: float) -> str:
	return json.dumps(
		{
			"type": "FeatureCollection",
			"features": [
				{
					"type": "Feature",
					"properties": {},
					"geometry": {
						"type": "Point",
						"coordinates": [longitude, latitude],
					},
				}
			],
		}
	)


def point_from_geojson(raw) -> tuple[float, float] | None:
	if not raw:
		return None
	try:
		data = json.loads(raw) if isinstance(raw, str) else raw
	except (TypeError, ValueError):
		return None
	for feature in data.get("features") or []:
		geometry = feature.get("geometry") or {}
		if geometry.get("type") != "Point":
			continue
		coordinates = geometry.get("coordinates") or []
		if len(coordinates) < 2:
			continue
		return float(coordinates[1]), float(coordinates[0])
	return None
