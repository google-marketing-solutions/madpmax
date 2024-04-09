# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for Asset Creation"""

import unittest
from unittest import mock
from asset_creation import AssetService


class TestAssetService(unittest.TestCase):

  def setUp(self):
    self.google_ads_service = mock.Mock()
    self._google_ads_client = mock.Mock()
    self.sheet_service = mock.MagicMock()
    self.asset_service = AssetService(
        self._google_ads_client, self.google_ads_service, self.sheet_service
    )
    self._google_ads_client.enums.AssetFieldTypeEnum = {"LOGO": "LOGO"}
    self._google_ads_client.enums.CallToActionTypeEnum = {"BOOK": "BOOK"}

    self._google_ads_client.enums.AssetTypeEnum.IMAGE = (
        "IMAGE")

  def test_compile_asset_group_alias_return_alias_when_get_data(self):
    input_sheet_row = ["", "true", "customer1", "test_camapign", "AssetGroup1"]
    result = self.asset_service.compile_asset_group_alias(input_sheet_row)

    self.assertEqual(result, "customer1;test_camapign;AssetGroup1")

  def test_compile_asset_group_alias_return_none_when_no_data(self):
    input_sheet_row = ["", "true", "customer1", "test_camapign"]
    result = self.asset_service.compile_asset_group_alias(input_sheet_row)

    self.assertIsNone(result)

  def test_add_asset_to_asset_group_returns_object(self):
    result = self.asset_service.add_asset_to_asset_group("Test Name", "Asset_group_id_123", "LOGO", "customer10")
    self.assertIsNotNone(result)

  def test_create_imge_asset_returns_correct_object(self):
    result = self.asset_service.create_image_asset("https://example.co.uk", "Test Image Asset", "customer10")

    # Checking elements of the same result object
    self.assertEqual(result.asset_operation.create.type, "IMAGE")
    self.assertEqual(result.asset_operation.create.image_asset.full_size.url, "https://example.co.uk")
    self.assertEqual(result.asset_operation.create.name, "Test Image Asset")

  @mock.patch('requests.get')
  def test_create_image_asset_returns_correct_object(self, mock_requests_get):
    mock_response = mock.MagicMock()
    mock_response.content = "Test Content"
    mock_requests_get.return_value = mock_response
    result = self.asset_service.create_image_asset("https://example.co.uk", "Test Image Asset", "customer10")

    self.assertEqual(result.asset_operation.create.image_asset.data, "Test Content")

  def test_create_text_asset_returns_correct_object(self):
    result = self.asset_service.create_text_asset("Random text to test", "customer10")

    self.assertEqual(result.asset_operation.create.text_asset.text, "Random text to test")

  def test_create_video_asset_returns_correct_youtube_video_id(self):
    self.google_ads_service._retrieve_yt_id.return_value = "Test Content"
    result = self.asset_service.create_video_asset("https://example.co.uk", "customer10")

    self.assertEqual(result.asset_operation.create.youtube_video_asset.youtube_video_id, "Test Content")

  def test_create_video_asset_returns_correct_youtube_video_title(self):
    result = self.asset_service.create_video_asset("https://example.co.uk", "customer10")

    self.assertIn("Marketing Video #", result.asset_operation.create.youtube_video_asset.youtube_video_title)

if __name__ == "__main__":
  unittest.main()
