# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Final
import unittest
from unittest.mock import call
from unittest.mock import Mock
from unittest.mock import patch
from pubsub import PubSub

_SHEET_RANGE_ARGS: Final[dict] = dict(
    new_campaigns_arg="NewCampaigns!A6:L",
    campaigns_arg="CampaignList!A6:D",
    new_asset_groups_arg="NewAssetGroups!A6:T",
    asset_group_arg="AssetGroupList!A6:F",
    sitelinks_arg="Sitelinks!A6:J",
    assets_arg="Assets!A6:L",
)


def _mock_get_sheet_values_callback(input_value):
  """Mock SheetsService.get_sheet_values function based on the input.

  Args:
  input_value: Expected input value for SheetsService.get_sheet_values function.
  """
  if input_value == _SHEET_RANGE_ARGS["new_campaigns_arg"]:
    return [["New Campaigns Test Data"]]
  if input_value == _SHEET_RANGE_ARGS["campaigns_arg"]:
    return [["Campaigns Test Data"]]
  if input_value == _SHEET_RANGE_ARGS["new_asset_groups_arg"]:
    return [["New Asset Groups Test Data"]]
  if input_value == _SHEET_RANGE_ARGS["asset_group_arg"]:
    return [["New Asset Groups Test Data"]]
  if input_value == _SHEET_RANGE_ARGS["sitelinks_arg"]:
    return [["Sitelinks Test Data"]]
  if input_value == _SHEET_RANGE_ARGS["assets_arg"]:
    return [["Assets Test Data"]]


class TestPubSubCall(unittest.TestCase):

  @patch("data_references.ConfigFile")
  def setUp(self, config_file):
    config_file.login_customer_id = "1234"
    # Set up mock dependencies
    self._google_ads_client = Mock()
    # Initialize CampaignService with mocked dependencies
    self.pubsub = PubSub(config_file, self._google_ads_client)

  @patch("sheet_api.SheetsService.refresh_spreadsheet")
  def test_refresh_spreadsheet_calls_sheet_service_refresh_spreadsheet(
      self, mock_refresh_spreadsheet
  ):
    """Test refresh_spreadsheet method in PubSub.

    Confirms if service calls correct function.
    """
    self.pubsub.refresh_spreadsheet()
    mock_refresh_spreadsheet.assert_called()

  @patch("sheet_api.SheetsService.refresh_customer_id_list")
  def test_refresh_customer_id_list_calls_sheet_service_refresh_customer_id_list(
      self, mock_refresh_customer_id_list
  ):
    """Test refresh_customer_id_list method in PubSub.

    Confirms if service calls correct function.
    """
    self.pubsub.refresh_customer_id_list()
    mock_refresh_customer_id_list.assert_called()

  @patch("sheet_api.SheetsService.refresh_campaign_list")
  def test_refresh_campaign_list_calls_sheet_service_refresh_campaign_list(
      self, mock_refresh_campaign_list
  ):
    """Test refresh_campaign_list method in PubSub.

    Confirms if service calls correct function.
    """
    self.pubsub.refresh_campaign_list()
    mock_refresh_campaign_list.assert_called()

  @patch("sheet_api.SheetsService.refresh_asset_group_list")
  def test_refresh_asset_group_list_calls_sheet_service_refresh_asset_group_list(
      self, mock_refresh_asset_group_list
  ):
    """Test refresh_asset_group_list method in PubSub.

    Confirms if service calls correct function.
    """
    self.pubsub.refresh_asset_group_list()
    mock_refresh_asset_group_list.assert_called()

  @patch("sheet_api.SheetsService.refresh_assets_list")
  def test_refresh_assets_list_calls_sheet_service_refresh_assets_list(
      self, mock_refresh_assets_list
  ):
    """Test refresh_assets_list method in PubSub.

    Confirm if service calls correct function.
    """
    self.pubsub.refresh_assets_list()
    mock_refresh_assets_list.assert_called()

  @patch("sheet_api.SheetsService.refresh_sitelinks_list")
  def test_refresh_sitelinks_list_calls_sheet_service_refresh_sitelinks_list(
      self, mock_refresh_sitelinks_list
  ):
    """Test refresh_sitelinks_list method in PubSub.

    Confirms if service calls correctfunction.
    """
    self.pubsub.refresh_sitelinks_list()
    mock_refresh_sitelinks_list.assert_called()

  @patch("asset_creation.AssetService.process_asset_data_and_create")
  @patch("sheet_api.SheetsService.get_sheet_id")
  @patch("sheet_api.SheetsService.get_sheet_values")
  def test_create_api_operations_calls_value_retrieval_services_correctly(
      self,
      mock_get_sheet_values,
      mock_get_sheet_id,
      mock_process_asset_data_and_create,
  ):
    """Test create_api_operations method in PubSub.

    Confirms if service retrives correct amount of data.
    """
    mock_process_asset_data_and_create.return_value = True
    mock_get_sheet_id.return_value = "1234abcd"
    mock_get_sheet_values.side_effect = _mock_get_sheet_values_callback
    self.pubsub.create_api_operations()

    expected_calls = [
        call(_SHEET_RANGE_ARGS["new_campaigns_arg"]),
        call(_SHEET_RANGE_ARGS["sitelinks_arg"]),
        call(_SHEET_RANGE_ARGS["assets_arg"]),
        call(_SHEET_RANGE_ARGS["new_asset_groups_arg"]),
        call(_SHEET_RANGE_ARGS["asset_group_arg"]),
        call(_SHEET_RANGE_ARGS["campaigns_arg"]),
    ]

    mock_get_sheet_values.assert_has_calls(expected_calls)

    expected_call_count = 6
    self.assertTrue(mock_get_sheet_values.call_count >= expected_call_count)

  @patch("sheet_api.SheetsService.get_sheet_id")
  @patch("sitelink_creation.SitelinkService.process_sitelink_input_sheet")
  @patch("asset_creation.AssetService.process_asset_data_and_create")
  @patch(
      "asset_group_creation.AssetGroupService.process_asset_group_data_and_create"
  )
  @patch(
      "campaign_creation.CampaignService.process_campaign_input_sheet"
  )
  @patch("sheet_api.SheetsService.get_sheet_values")
  def test_create_api_operations_calls_services_correctly(
      self,
      mock_get_sheet_values,
      mock_process_campaign_input_sheet,
      mock_process_asset_group_data_and_create,
      mock_process_asset_data_and_create,
      mock_process_sitelink_input_sheet,
      mock_get_sheet_id,
  ):
    """Test if create_api_operations method in PubSub.

    Confirms if service calls correct functions with all data available.
    """
    mock_get_sheet_id.return_value = "1234abcd"
    mock_get_sheet_values.side_effect = _mock_get_sheet_values_callback
    self.pubsub.create_api_operations()

    mock_process_campaign_input_sheet.assert_called_with(
        [["New Campaigns Test Data"]]
    )
    mock_process_asset_group_data_and_create.assert_called_with(
        [["New Asset Groups Test Data"]], [["Campaigns Test Data"]]
    )
    mock_process_sitelink_input_sheet.assert_called_once_with(
        [["Sitelinks Test Data"]]
    )
    mock_process_asset_data_and_create.assert_called_with(
        [["Assets Test Data"]], [["New Asset Groups Test Data"]]
    )

  @patch("sitelink_creation.SitelinkService.process_sitelink_input_sheet")
  @patch("asset_creation.AssetService.process_asset_data_and_create")
  @patch(
      "asset_group_creation.AssetGroupService.process_asset_group_data_and_create"
  )
  @patch(
      "campaign_creation.CampaignService.process_campaign_input_sheet"
  )
  @patch("sheet_api.SheetsService.get_sheet_values")
  def test_create_api_operations_dont_call_asset_group_service(
      self,
      mock_get_sheet_values,
      mock_process_campaign_input_sheet,
      mock_process_asset_group_data_and_create,
      mock_process_asset_data_and_create,
      mock_process_sitelink_input_sheet,
  ):
    """Test create_api_operations method in PubSub.

    Confirms if service ignores assets creation when no data available.
    """
    mock_get_sheet_values.return_value = None
    self.pubsub.create_api_operations()

    mock_process_campaign_input_sheet.assert_not_called()
    mock_process_asset_group_data_and_create.assert_not_called()
    mock_process_sitelink_input_sheet.assert_not_called()
    mock_process_asset_data_and_create.assert_not_called()
