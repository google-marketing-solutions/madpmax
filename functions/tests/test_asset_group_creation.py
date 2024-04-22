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
from asset_group_creation import AssetGroupService
import pytest

# Run this test from funtions folder with: python -m pytest tests/test_asset_group_creation.py
@pytest.mark.parametrize(
    "asset_group_name,asset_group_status,asset_group_final_url,asset_group_mobile_url,error",
    [
        (
            "",
            "SUCCESS",
            "http://example",
            "http://mobile_example",
            "Asset Group Name is required to create an Asset Group",
        ),
        (
            "AGN",
            "",
            "http://example",
            "http://mobile_example",
            "Status is required to create an Asset Group",
        ),
        (
            "AGN",
            "SUCCESS",
            "",
            "http://mobile_example",
            "Final URL is required to create an Asset Group",
        ),
        (
            "AGN",
            "SUCCESS",
            "http://example",
            "",
            "Mobile URL is required to create an Asset Group",
        ),
    ],
)
@mock.patch("validators.url")
def test_create_asset_group_return_error_on_invalid_input(
    mock_validators_url,
    asset_group_name,
    asset_group_status,
    asset_group_final_url,
    asset_group_mobile_url,
    error,
):
  mock_validators_url.return_value = True
  google_ads_service = mock.MagicMock()
  _google_ads_client = mock.Mock()
  sheet_service = mock.MagicMock()
  asset_service = mock.MagicMock()
  asset_group_service = AssetGroupService(
      google_ads_service, sheet_service, asset_service, _google_ads_client
  )

  with pytest.raises(ValueError, match=error):
    asset_group_service.create_asset_group(
        asset_group_name,
        asset_group_status,
        asset_group_final_url,
        asset_group_mobile_url,
        "asset_group_path1",
        "asset_group_path2",
        "asset_group_id",
        "campaign_id",
        "customer_id",
    )

# Run this part with: python -m unittest tests/test_asset_group_creation.py
class TestAssetGroupService(unittest.TestCase):

  def setUp(self):
    self.google_ads_service = mock.Mock()
    self._google_ads_client = mock.Mock()
    self.sheet_service = mock.MagicMock()
    self.asset_service = mock.Mock()
    self._google_ads_client.enums.AssetGroupStatusEnum = {"SUCCESS": "SUCCESS"}
    self.asset_group_service = AssetGroupService(
        self.google_ads_service,
        self.sheet_service,
        self.asset_service,
        self._google_ads_client,
    )
    self.campaign_path = "Fantastic campaign path"
    self.asset_group_path = "What an asset group path!"
    self._google_ads_client.get_service(
        "CampaignService"
    ).campaign_path.return_value = self.campaign_path
    self._google_ads_client.get_service(
        "AssetGroupService"
    ).asset_group_path.return_value = self.asset_group_path

  def test_compile_campaign_alias_return_alias_when_get_data(self):
    input_sheet_row = [
        "",
        "SUCCESS",
        "customer1",
        "test_camapign",
        "AssetGroup1",
        "ENABLED",
        "http://example",
    ]
    result = self.asset_group_service.compile_campaign_alias(input_sheet_row)

    self.assertEqual(result, "customer1;test_camapign")

  @mock.patch("validators.url")
  def test_create_asset_group_return_error_on_invalid_url(
      self, mock_validators_url
  ):
    asset_group_final_url = "Final.com"
    mock_validators_url.return_value = False

    with self.assertRaisesRegex(
        ValueError, f"Final URL '{asset_group_final_url}' is not a valid URL"
    ):
      self.asset_group_service.create_asset_group(
          "asset_group_name",
          "SUCCESS",
          asset_group_final_url,
          "asset_group_mobile_url",
          "asset_group_path1",
          "asset_group_path2",
          "asset_group_id",
          "campaign_id",
          "customer_id",
      )

  @mock.patch("validators.url")
  def test_create_asset_group_creates_correct_name(self, mock_validators_url):
    mock_validators_url.return_value = True
    
    result = self.asset_group_service.create_asset_group(
        "AGN",
        "SUCCESS",
        "final.com",
        "mobile_url.com",
        "asset_group_path1",
        "asset_group_path2",
        "123456Id",
        "Campaign1",
        "customer_number_1",
    )

    self.assertEqual(result.asset_group_operation.create.name, "AGN")

  @mock.patch("validators.url")
  def test_create_asset_group_creates_correct_status(self, mock_validators_url):
    mock_validators_url.return_value = True
    result = self.asset_group_service.create_asset_group(
        "AGN",
        "SUCCESS",
        "final.com",
        "mobile_url.com",
        "asset_group_path1",
        "asset_group_path2",
        "123456Id",
        "Campaign1",
        "customer_number_1",
    )
    self.assertEqual(result.asset_group_operation.create.status, "SUCCESS")

  @mock.patch("validators.url")
  def test_create_asset_group_creates_correct_group_path1(self, mock_validators_url):
    mock_validators_url.return_value = True
    
    result = self.asset_group_service.create_asset_group(
        "AGN",
        "SUCCESS",
        "final.com",
        "mobile_url.com",
        "asset_group_path1",
        "asset_group_path2",
        "123456Id",
        "Campaign1",
        "customer_number_1",
    )
    self.assertEqual(
        result.asset_group_operation.create.path1, "asset_group_path1"
    )

  @mock.patch("validators.url")
  def test_create_asset_group_creates_correct_group_path2(self, mock_validators_url):
    mock_validators_url.return_value = True

    result = self.asset_group_service.create_asset_group(
        "AGN",
        "SUCCESS",
        "final.com",
        "mobile_url.com",
        "asset_group_path1",
        "asset_group_path2",
        "123456Id",
        "Campaign1",
        "customer_number_1",
    )
    self.assertEqual(
        result.asset_group_operation.create.path2, "asset_group_path2"
    )

  @mock.patch("validators.url")
  def test_create_asset_group_creates_correct_resource_name(self, mock_validators_url):
    mock_validators_url.return_value = True

    result = self.asset_group_service.create_asset_group(
        "AGN",
        "SUCCESS",
        "final.com",
        "mobile_url.com",
        "asset_group_path1",
        "asset_group_path2",
        "123456Id",
        "Campaign1",
        "customer_number_1",
    )
    self.assertEqual(
        result.asset_group_operation.create.resource_name, self.asset_group_path
    )

  @mock.patch("validators.url")
  def test_create_asset_group_creates_correct_campaign_for_asset_group(self, mock_validators_url):
    mock_validators_url.return_value = True

    result = self.asset_group_service.create_asset_group(
        "AGN",
        "SUCCESS",
        "final.com",
        "mobile_url.com",
        "asset_group_path1",
        "asset_group_path2",
        "123456Id",
        "Campaign1",
        "customer_number_1",
    )
    self.assertEqual(
        result.asset_group_operation.create.campaign, self.campaign_path
    )
