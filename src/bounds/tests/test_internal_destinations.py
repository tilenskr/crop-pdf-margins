import unittest
from unittest.mock import MagicMock

import pymupdf

from src.crop.scale_cropper.internal_destinations import InternalDestinationResolver


class InternalDestinationResolverTests(unittest.TestCase):
    def test_resolve_point_stops_on_explicit_zero_point(self) -> None:
        resolver = InternalDestinationResolver(MagicMock(), page_count=1)
        expected = pymupdf.Point(0.0, 0.0)

        resolver._point_from_explicit_to = MagicMock(return_value=expected)
        resolver._parse_zoom_triplet_point = MagicMock()
        resolver._handle_fit_destination = MagicMock()
        resolver._point_from_outline_xref_dest = MagicMock()

        point = resolver._resolve_point({}, 0)

        self.assertEqual(point, expected)
        resolver._parse_zoom_triplet_point.assert_not_called()
        resolver._handle_fit_destination.assert_not_called()
        resolver._point_from_outline_xref_dest.assert_not_called()


if __name__ == "__main__":
    unittest.main()
