# Copyright 2024 Google LLC

# Licensed under the Apache License, Version 2.0 (the "License")
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

# https: // www.apache.org / licenses / LICENSE - 2.0


# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for Asset Deletion."""

from typing import Final
import unittest
from unittest import mock
from asset_deletion import AssetDeletionService
import data_references


_CUSTOMER_ID: Final[str] = "customer_id_1"
_CAMPAIGN_ID: Final[str] = "campaign_id_1"
_VALID_SHEET_DATA: Final[list[list[str]]] = [
    [
        "UPLOADED",
        "TRUE",
        "Test Customer 1",
        "Test Campaign 1",
        "Test Asset Group 1",
        "HEADLINE",
        "Test Headline 1",
        "",
        "",
        "",
        "",
        "customers/1234567890/assetGroupAssets/1234567890~1234567890~HEADLINE",
    ],
    [
        "",
        "TRUE",
        "Test Customer 1",
        "Test Campaign 1",
        "Test Asset Group 1",
        "HEADLINE",
        "Test Headline 1",
        "",
        "",
        "",
        "",
        "",
    ],
    [
        "UPLOADED",
        "FALSE",
        "Test Customer 2",
        "Test Campaign 2",
        "Test Asset Group 1",
        "HEADLINE",
        "Test Headline 1",
        "",
        "",
        "",
        "",
        "customers/1234567890/assetGroupAssets/1234567890~1234567890~HEADLINE",
    ],
    [
        "UPLOADED",
        "TRUE",
        "Test Customer 2",
        "Test Campaign 2",
        "Test Asset Group 1",
        "HEADLINE",
        "Test Headline 1",
        "",
        "",
        "",
        "",
        "",
    ]
]


class TestAssetDeletionService(unittest.TestCase):
  """Test class for Asset deletion.

  Contains all methods to test delete assets in Google Ads pMax Asset Groups.
  """

  def setUp(self):
    self.google_ads_service = mock.Mock()
    self._google_ads_client = mock.Mock()
    self.sheet_service = mock.MagicMock()
    self.asset_service = AssetDeletionService(
        self._google_ads_client, self.google_ads_service, self.sheet_service
    )

  def test_create_delete_asset_object(self):
    """Test delete_asset method in AssetDeletionService.

    Verify if return object contains expected structure and values.
    """
    asset_resource = _VALID_SHEET_DATA[0][
        data_references.Assets.asset_group_asset]

    delete_asset_operation = self.asset_service.delete_asset(
        asset_resource)

    self.assertEqual(
        delete_asset_operation.asset_group_asset_operation.remove,
        asset_resource
    )

  def test_create_delete_asset_object_no_value(self):
    """Test delete_asset method in AssetDeletionService.

    Verify if return object contains expected structure and values.
    """
    asset_resource = _VALID_SHEET_DATA[3][
        data_references.Assets.asset_group_asset]

    delete_asset_operation = self.asset_service.delete_asset(
        asset_resource)

    self.assertIsNone(
        delete_asset_operation
    )
