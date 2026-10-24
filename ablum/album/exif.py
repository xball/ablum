# Copyright (c) 2026, xball and contributors
# For license information, please see license.txt

"""Read a photo's taken time and GPS from EXIF. No Frappe import, so tests stay plain."""

from __future__ import annotations

import datetime


def ratio(value) -> float:
	if hasattr(value, "numerator"):
		denominator = float(value.denominator or 0)
		if not denominator:
			return 0.0
		return float(value.numerator) / denominator
	if isinstance(value, tuple) and len(value) == 2:
		denominator = float(value[1] or 0)
		if not denominator:
			return 0.0
		return float(value[0]) / denominator
	return float(value)


def decimal_coordinate(values, ref: str | None) -> float | None:
	"""Degrees, minutes, and seconds, plus N/S/E/W, become a signed decimal."""
	if not values:
		return None
	parts = list(values)
	degrees = ratio(parts[0])
	minutes = ratio(parts[1]) if len(parts) > 1 else 0.0
	seconds = ratio(parts[2]) if len(parts) > 2 else 0.0
	decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
	if (ref or "").upper() in {"S", "W"}:
		decimal = -decimal
	return decimal


def gps_from_ifd(gps: dict | None) -> tuple[float | None, float | None]:
	if not gps:
		return None, None
	latitude = decimal_coordinate(gps.get(2), gps.get(1))
	longitude = decimal_coordinate(gps.get(4), gps.get(3))
	if latitude is None or longitude is None:
		return None, None
	return latitude, longitude


def parse_exif_datetime(raw) -> datetime.datetime | None:
	if not raw:
		return None
	text = raw.decode() if isinstance(raw, bytes) else str(raw)
	text = text.strip().split("\x00", 1)[0]
	for pattern in ("%Y:%m:%d %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
		try:
			return datetime.datetime.strptime(text, pattern)
		except ValueError:
			continue
	return None


def read_exif(path: str) -> dict:
	"""Return taken_on, latitude, and longitude. Missing pieces stay None."""
	try:
		from PIL import Image
	except Exception:
		return {"taken_on": None, "latitude": None, "longitude": None}
	try:
		with Image.open(path) as image:
			return read_image_exif(image)
	except Exception:
		return {"taken_on": None, "latitude": None, "longitude": None}


def read_exif_bytes(content: bytes) -> dict:
	"""Read EXIF from the original upload before Frappe rewrites the image."""
	import io

	try:
		from PIL import Image
	except Exception:
		return {"taken_on": None, "latitude": None, "longitude": None}
	try:
		with Image.open(io.BytesIO(content)) as image:
			return read_image_exif(image)
	except Exception:
		return {"taken_on": None, "latitude": None, "longitude": None}


def read_image_exif(image) -> dict:
	empty = {"taken_on": None, "latitude": None, "longitude": None}
	try:
		from PIL.ExifTags import IFD

		exif = image.getexif()
		if not exif:
			return empty
		try:
			exif_ifd = exif.get_ifd(IFD.Exif)
			taken = parse_exif_datetime(exif_ifd.get(36867) or exif_ifd.get(306))
		except Exception:
			taken = parse_exif_datetime(exif.get(36867) or exif.get(306))
		try:
			gps = exif.get_ifd(IFD.GPSInfo)
		except Exception:
			gps = {}
		latitude, longitude = gps_from_ifd(gps)
	except Exception:
		return empty
	return {"taken_on": taken, "latitude": latitude, "longitude": longitude}
