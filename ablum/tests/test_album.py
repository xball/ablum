# Copyright (c) 2026, xball and contributors
# For license information, please see license.txt

from __future__ import annotations

import datetime
import unittest

from ablum.album.access import guest_can_view, person_to_reuse, photo_is_member, points_for_map
from ablum.album.exif import decimal_coordinate, gps_from_ifd, parse_exif_datetime
from ablum.album.geo import point_from_geojson, point_geojson


class TestExif(unittest.TestCase):
	def test_decimal_coordinate_uses_direction(self):
		latitude = decimal_coordinate(((40, 1), (26, 1), (46, 1)), "N")
		longitude = decimal_coordinate(((74, 1), (0, 1), (21, 1)), "W")
		self.assertAlmostEqual(latitude, 40 + 26 / 60 + 46 / 3600)
		self.assertAlmostEqual(longitude, -(74 + 21 / 3600))

	def test_gps_ifd_skips_a_missing_pair(self):
		self.assertEqual(gps_from_ifd({1: "N", 2: ((1, 1),)}), (None, None))
		latitude, longitude = gps_from_ifd(
			{1: "S", 2: ((10, 1), (0, 1), (0, 1)), 3: "E", 4: ((20, 1), (30, 1), (0, 1))}
		)
		self.assertAlmostEqual(latitude, -10)
		self.assertAlmostEqual(longitude, 20.5)

	def test_parse_exif_datetime(self):
		self.assertEqual(parse_exif_datetime("2026:10:23 14:30:00"), datetime.datetime(2026, 10, 23, 14, 30, 0))
		self.assertIsNone(parse_exif_datetime("not a date"))


class TestAccess(unittest.TestCase):
	def test_map_skips_photos_without_a_location(self):
		photos = [
			{"name": "a", "latitude": 1.0, "longitude": 2.0},
			{"name": "b", "latitude": None, "longitude": 2.0},
			{"name": "c", "latitude": 1.0, "longitude": None},
		]
		self.assertEqual([row["name"] for row in points_for_map(photos)], ["a"])

	def test_guest_cannot_open_a_private_album_or_a_wrong_token(self):
		self.assertFalse(guest_can_view("Private", "token", "token"))
		self.assertFalse(guest_can_view("Public", "token", "other"))
		self.assertFalse(guest_can_view("Public", "token", ""))
		self.assertTrue(guest_can_view("Public", "token", "token"))

	def test_a_photo_outside_the_album_is_not_a_member(self):
		self.assertFalse(photo_is_member(["photo-a"], "photo-b"))
		self.assertTrue(photo_is_member(["photo-a"], "photo-a"))

	def test_the_same_person_name_is_reused(self):
		existing = [{"name": "Ada", "person_name": "Ada"}]
		self.assertEqual(person_to_reuse(existing, " ada ")["name"], "Ada")
		self.assertIsNone(person_to_reuse(existing, "Bea"))

	def test_geojson_point_round_trip(self):
		self.assertEqual(point_from_geojson(point_geojson(22.3, 114.1)), (22.3, 114.1))
