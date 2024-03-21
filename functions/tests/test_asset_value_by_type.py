from unittest.mock import MagicMock
from unittest.mock import Mock
from asset_creation import AssetService
import pytest


# Run this test from funtions folder with: python -m pytest tests/test_asset_value_by_type.py
@pytest.mark.parametrize(
    "type_input,expected",
    [
        ("HEADLINE", "Let's test it"),
        ("BUSINESS_NAME", "Let's test it"),
        ("DESCRIPTION", "Let's test it"),
        ("LONG_HEADLINE", "Let's test it"),
        ("CALL_TO_ACTION_SELECTION", "BOOK NOW"),
        ("YOUTUBE_VIDEO", "https://www.exmaple_url.me"),
        ("MARKETING_IMAGE", "https://www.exmaple_url.me"),
        ("SQUARE_MARKETING_IMAGE", "https://www.exmaple_url.me"),
        ("PORTRAIT_MARKETING_IMAGE", "https://www.exmaple_url.me"),
        ("LOGO", "https://www.exmaple_url.me"),
        ("LANDSCAPE_LOGO", "https://www.exmaple_url.me"),
    ],
)
def test_get_asset_value_for_all_assets(type_input, expected):
  google_ads_service = MagicMock()
  _google_ads_client = Mock()
  sheet_service = MagicMock()
  asset_service = AssetService(
      _google_ads_client, google_ads_service, sheet_service
  )

  input_sheet_row = [
      "",
      "flase",
      "Test account",
      "Test Camapign",
      "Test Asset Gtoup Name",
      "HEADLINE",
      "Let's test it",
      "BOOK NOW",
      "https://www.exmaple_url.me",
      "abcd",
      "",
  ]
  result = asset_service.get_asset_value_by_type(input_sheet_row, type_input)

  assert result == expected
