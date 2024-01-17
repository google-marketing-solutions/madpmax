from datetime import datetime, timedelta
import pprint
import unittest
import re
from unittest.mock import MagicMock
from unittest.mock import Mock
from asset_creation import AssetService


class TestAssetService(unittest.TestCase):

  def setUp(self):
    # Set up mock dependencies
    self.google_ads_service = MagicMock()
    self._google_ads_client = Mock()
    # Mocking the return value for BiddingStrategyTypeEnum
    self._google_ads_client.enums.AssetTypeEnum.IMAGE = "IMAGE"
    self._google_ads_client.enums.AssetFieldTypeEnum = {
        "HEADLINE": "HEADLINE",
        "SQUARE_MARKETING_IMAGE": "SQUARE_MARKETING_IMAGE",
        "YOUTUBE_VIDEO": "YOUTUBE_VIDEO",
        "CALL_TO_ACTION_SELECTION": "CALL_TO_ACTION_SELECTION"
    }
    # Initialize CampaignService with mocked dependencies
    self.asset_service = AssetService(self._google_ads_client, self.google_ads_service)

  def test_create_text_asset_when_data_is_valid(self):
    customer_id = 456789
    asset_group_id = 123456
    row = [
      "",
      "FALSE",
      "Test Customer",
      "Test Campaign",
      "Test Asset Group",
      "HEADLINE",
      "Test Headline"
    ]
    new_asset_group = False
    operations, asset_resource = self.asset_service.create_asset_mutation(
        row,
        customer_id,
        asset_group_id,
        new_asset_group,
    )
    self.assertIsNotNone(operations)
    self.assertIsNotNone(asset_resource)
    self.assertEqual(len(operations), 2)
    self.assertEqual(
        operations[0].asset_operation.create.text_asset.text, "Test Headline"
    )
    self.assertEqual(
        operations[
            1].asset_group_asset_operation.create.field_type, "HEADLINE"
    )
    self.assertEqual(
        operations[
            1].asset_group_asset_operation.create.asset, asset_resource
    )
    self.assertEqual(
        operations[0].asset_operation.create.resource_name, asset_resource
    )

  def test_create_video_asset_when_data_is_valid(self):
    self.google_ads_service._retrieve_yt_id.return_value = "qqiqlJEvTvg"
    customer_id = 456789
    asset_group_id = 123456
    row = [
      "",
      "FALSE",
      "Test Customer",
      "Test Campaign",
      "Test Asset Group",
      "YOUTUBE_VIDEO",
      "",
      "",
      "https://www.youtube.com/watch?v=qqiqlJEvTvg"
    ]
    new_asset_group = False
    operations, asset_resource = self.asset_service.create_asset_mutation(
        row,
        customer_id,
        asset_group_id,
        new_asset_group,
    )
    self.assertIsNotNone(operations)
    self.assertEqual(len(operations), 2)
    self.assertIsNotNone(asset_resource)
    self.assertEqual(
        operations[
            1].asset_group_asset_operation.create.field_type, "YOUTUBE_VIDEO"
    )
    self.assertEqual(
        operations[0].asset_operation.create.youtube_video_asset.youtube_video_id,
        "qqiqlJEvTvg"
    )
    self.assertEqual(
        operations[
            1].asset_group_asset_operation.create.asset, asset_resource
    )
    self.assertEqual(
        operations[0].asset_operation.create.resource_name, asset_resource
    )

  def test_create_image_asset_when_data_is_valid(self):
    customer_id = 456789
    asset_group_id = 123456
    row = [
      "",
      "FALSE",
      "Test Customer",
      "Test Campaign",
      "Test Asset Group",
      "SQUARE_MARKETING_IMAGE",
      "",
      "",
      "https://tpc.googlesyndication.com/simgad/17627663494327917134"
    ]
    new_asset_group = False
    operations, asset_resource = self.asset_service.create_asset_mutation(
        row,
        customer_id,
        asset_group_id,
        new_asset_group,
    )
    self.assertIsNotNone(operations)
    self.assertEqual(len(operations), 2)
    self.assertIsNotNone(asset_resource)
    self.assertEqual(
        operations[
            1].asset_group_asset_operation.create.field_type, "SQUARE_MARKETING_IMAGE"
    )
    self.assertEqual(
        operations[0].asset_operation.create.type,
        "IMAGE"
    )
    self.assertEqual(
        operations[0].asset_operation.create.image_asset.full_size.url,
        "https://tpc.googlesyndication.com/simgad/17627663494327917134"
    )
    self.assertEqual(
        operations[
            1].asset_group_asset_operation.create.asset, asset_resource
    )
    self.assertEqual(
        operations[0].asset_operation.create.resource_name, asset_resource
    )

if __name__ == '__main__':
    unittest.main()