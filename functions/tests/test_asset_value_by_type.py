from unittest import mock
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
  google_ads_service = mock.MagicMock()
  google_ads_client = mock.Mock()
  sheet_service = mock.MagicMock()
  asset_service = AssetService(
      google_ads_client, google_ads_service, sheet_service
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


@pytest.mark.parametrize(
    "type_input",
    [
        "MARKETING_IMAGE",
        "SQUARE_MARKETING_IMAGE",
        "PORTRAIT_MARKETING_IMAGE",
        "LOGO",
        "LANDSCAPE_LOGO",
    ],
)
@mock.patch("asset_creation.AssetService.create_image_asset")
@mock.patch("validators.url")
def test_create_image_asset_for_images_types(
    mock_validators_url, mock_create_image_asset, type_input
):
  google_ads_service = mock.MagicMock()
  google_ads_client = mock.Mock()
  sheet_service = mock.MagicMock()
  asset_service = AssetService(
      google_ads_client, google_ads_service, sheet_service
  )
  mock_create_image_asset.return_value = "Image object let's say"
  mock_validators_url.return_value = True
  result = asset_service.create_asset(
      type_input, "Test Image Asset", "customer10"
  )

  assert result == "Image object let's say"


@pytest.mark.parametrize(
    "type_input",
    [
        "HEADLINE",
        "BUSINESS_NAME",
        "DESCRIPTION",
        "LONG_HEADLINE",
    ],
)
@mock.patch("asset_creation.AssetService.create_text_asset")
@mock.patch("validators.url")
def test_create_text_asset_for_text_types(
    mock_validators_url, mock_create_text_asset, type_input
):
  google_ads_service = mock.MagicMock()
  google_ads_client = mock.Mock()
  sheet_service = mock.MagicMock()
  asset_service = AssetService(
     google_ads_client, google_ads_service, sheet_service
  )
  mock_create_text_asset.return_value = "Now it is a text object"
  mock_validators_url.return_value = True
  result = asset_service.create_asset(type_input, "Test Asset", "customer10")

  assert result == "Now it is a text object"


@pytest.mark.parametrize(
    "type_input,error",
    [
        ("HEADLINE", "Asset text is required to create a HEADLINE Asset"),
        (
            "BUSINESS_NAME",
            "Asset text is required to create a BUSINESS_NAME Asset",
        ),
        ("DESCRIPTION", "Asset text is required to create a DESCRIPTION Asset"),
        (
            "LONG_HEADLINE",
            "Asset text is required to create a LONG_HEADLINE Asset",
        ),
        (
            "CALL_TO_ACTION_SELECTION",
            (
                "Call to action is required to create a"
                " CALL_TO_ACTION_SELECTION Asset"
            ),
        ),
        ("YOUTUBE_VIDEO", "Asset URL YOUTUBE_VIDEO is not a valid URL"),
        ("MARKETING_IMAGE", "Asset URL MARKETING_IMAGE is not a valid URL"),
        (
            "SQUARE_MARKETING_IMAGE",
            "Asset URL SQUARE_MARKETING_IMAGE is not a valid URL",
        ),
        (
            "PORTRAIT_MARKETING_IMAGE",
            "Asset URL PORTRAIT_MARKETING_IMAGE is not a valid URL",
        ),
        ("LOGO", "Asset URL LOGO' is not a valid URL"),
        ("LANDSCAPE_LOGO", "Asset URL LANDSCAPE_LOGO is not a valid URL"),
    ],
)
def test_rise_error_when_no_asset_value_for_create_asset(type_input, error):
  google_ads_service = mock.MagicMock()
  google_ads_client = mock.Mock()
  sheet_service = mock.MagicMock()
  asset_service = AssetService(
      google_ads_client, google_ads_service, sheet_service
  )
  with pytest.raises(ValueError, match=error):
    asset_service.create_asset(type_input, None, "customer10")
