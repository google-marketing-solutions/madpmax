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
"""Tests for Sheet Service."""

from collections import namedtuple
import unittest
from unittest import mock
import data_references
from sheet_api import SheetsService


class TestSheetService(unittest.TestCase):

  def setUp(self):
    super().setUp()
    self.credentials = mock.Mock()
    self._google_ads_client = mock.Mock()
    self.google_ads_service = mock.MagicMock()
    self.sheet_service = SheetsService(
        self.credentials, self._google_ads_client, self.google_ads_service
    )

  @mock.patch("sheet_api.SheetsService.update_asset_sheet_output")
  @mock.patch("sheet_api.SheetsService.update_sheet_lists")
  def test_refresh_assets_list(
      self, mock_update_sheet_lists, mock_update_asset_sheet_output
  ):
    Customer = namedtuple("Customer", ["id"])
    ResultRow = namedtuple("ResultRow", ["customer_client"])
    retrieve_all_customers = [
        ResultRow(customer_client=Customer(id="customer1")),
        ResultRow(customer_client=Customer(id="customer2")),
    ]
    mock_update_asset_sheet_output.return_value = None

    self.google_ads_service.retrieve_all_customers.return_value = (
        retrieve_all_customers
    )
    mock_update_sheet_lists.return_value = {
        "customer1": {"Campaign1", "Campaign2"},
        "customer2": {"Test Campaign1"},
    }

    self.sheet_service.refresh_assets_list()
    self.google_ads_service.retrieve_all_assets.assert_has_calls(
        [mock.call("customer1"), mock.call("customer2")]
    )

  @mock.patch("sheet_api.SheetsService.update_asset_sheet_output")
  @mock.patch("sheet_api.SheetsService.update_sheet_lists")
  def test_update_asset_sheet_output(
      self, mock_update_sheet_lists, mock_update_asset_sheet_output
  ):
    Customer = namedtuple("Customer", ["id"])
    ResultRow = namedtuple("ResultRow", ["customer_client"])
    retrieve_all_customers = [
        ResultRow(customer_client=Customer(id="customer1")),
        ResultRow(customer_client=Customer(id="customer2")),
    ]

    AssetGroupAsset = namedtuple("AssetGroupAsset", ["resource_name"])
    AssetGroupRow = namedtuple("AssetGroupRow", ["asset_group_asset"])

    refresh_results = [
        AssetGroupRow(
            asset_group_asset=AssetGroupAsset(resource_name="resource_name1")
        ),
        AssetGroupRow(
            asset_group_asset=AssetGroupAsset(resource_name="resource_name2")
        ),
    ]
    self.google_ads_service.retrieve_all_customers.return_value = (
        retrieve_all_customers
    )
    account_map = {
        "customer1": {"Campaign1", "Campaign2"},
        "customer2": {"Test Campaign1"},
    }
    mock_update_sheet_lists.return_value = account_map
    self.google_ads_service.retrieve_all_assets.return_value = refresh_results

    self.sheet_service.refresh_assets_list()

    mock_update_asset_sheet_output.assert_has_calls([
        mock.call(refresh_results, account_map),
        mock.call(refresh_results, account_map),
    ])

  @mock.patch("sheet_api.SheetsService.update_sitelink_sheet_output")
  @mock.patch("sheet_api.SheetsService.update_asset_sheet_output")
  @mock.patch("sheet_api.SheetsService._set_cell_value")
  @mock.patch("sheet_api.SheetsService.update_sheet_lists")
  def test_update_asset_sheet_output_with_empty_campaign_for_first_customer(
      self,
      mock_update_sheet_lists,
      mock_set_cell_value,
      mock_update_asset_sheet_output,
      mock_update_sitelink_sheet_output,
  ):
    Customer = namedtuple("Customer", ["id"])
    ResultRow = namedtuple("ResultRow", ["customer_client"])
    retrieve_all_customers = [
        ResultRow(customer_client=Customer(id="customer1")),
        ResultRow(customer_client=Customer(id="customer2")),
    ]

    self.google_ads_service.retrieve_all_customers.return_value = (
        retrieve_all_customers
    )
    account_map = {
        "customer1": {},
        "customer2": {"Test Campaign1"},
    }
    mock_update_sheet_lists.return_value = account_map
    self.google_ads_service.retrieve_all_campaigns.side_effect = [
        {},
        {"Test Campaign1"},
    ]
    self.google_ads_service.retrieve_all_asset_groups.return_value = {}
    self.sheet_service.refresh_spreadsheet()

    mock_update_sheet_lists.assert_has_calls([
        mock.call(
            retrieve_all_customers,
            data_references.SheetNames.customers,
            "!B:B",
            {},
        ),
        mock.call(
            {"Test Campaign1"},
            data_references.SheetNames.campaigns,
            "!D:D",
            account_map,
        ),
    ])

  @mock.patch("sheet_api.SheetsService.update_sitelink_sheet_output")
  @mock.patch("sheet_api.SheetsService.update_asset_sheet_output")
  @mock.patch("sheet_api.SheetsService._set_cell_value")
  @mock.patch("sheet_api.SheetsService.update_sheet_lists")
  def test_update_asset_sheet_output_with_empty_asset_group_for_first_customer(
      self,
      mock_update_sheet_lists,
      mock_set_cell_value,
      mock_update_asset_sheet_output,
      mock_update_sitelink_sheet_output,
  ):
    Customer = namedtuple("Customer", ["id"])
    ResultRow = namedtuple("ResultRow", ["customer_client"])
    retrieve_all_customers = [
        ResultRow(customer_client=Customer(id="customer1")),
        ResultRow(customer_client=Customer(id="customer2")),
    ]

    self.google_ads_service.retrieve_all_customers.return_value = (
        retrieve_all_customers
    )
    account_map = {
        "customer1": {"Campaign1"},
        "customer2": {"Test Campaign1"},
    }
    mock_update_sheet_lists.return_value = account_map
    self.google_ads_service.retrieve_all_campaigns.side_effect = [
        {"Campaign1"},
        {"Test Campaign1"},
    ]
    self.google_ads_service.retrieve_all_asset_groups.side_effect = [
        {},
        {"AssertGroup1"},
    ]

    self.sheet_service.refresh_spreadsheet()

    mock_update_sheet_lists.assert_has_calls([
        mock.call(
            retrieve_all_customers,
            data_references.SheetNames.customers,
            "!B:B",
            {},
        ),
        mock.call(
            {"Campaign1"},
            data_references.SheetNames.campaigns,
            "!D:D",
            account_map,
        ),
        mock.call(
            {"Test Campaign1"},
            data_references.SheetNames.campaigns,
            "!D:D",
            account_map,
        ),
        mock.call(
            {"AssertGroup1"},
            data_references.SheetNames.asset_groups,
            "!F:F",
            account_map,
        ),
    ])
