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

import datetime
from typing import Final
import unittest
from unittest import mock
from campaign_creation import CampaignService
import data_references

_CUSTOMER_ID: Final[str] = "customer_id_1"
_VALID_SHEET_DATA: Final[list[list[str]]] = [[
    "",
    "Test Customer 1",
    "Test Campaign 1",
    "200",
    "STANDARD",
    "ENABLED",
    "MaximizeConversions",
    "",
    "3",
    "2024-02-26",
    "2024-03-08",
], [
    "",
    "Test Customer 2",
    "Test Campaign 2",
    "500",
    "STANDARD",
    "PAUSED",
    "MaximizeConversionValue",
    "2",
    "",
    "2024-02-26",
    "2024-03-08",
]]

_CUSTOMER_ID_KEY: str = "customer_id"
_OPERATIONS_KEY: str = "operations"
_ERROR_LOG_KEY: str = "error_log"


class TestCampaignCreation(unittest.TestCase):
  """Test Campaign Creation."""

  def setUp(self):
    super().setUp()
    self.google_ads_service = mock.MagicMock()
    self.sheet_service = mock.MagicMock()
    self.google_ads_client = mock.Mock()
    self.google_ads_client.enums.BiddingStrategyTypeEnum.MAXIMIZE_CONVERSION_VALUE = (
        "MaximizeConversionValue")
    self.google_ads_client.enums.BiddingStrategyTypeEnum.MAXIMIZE_CONVERSIONS = (
        "MaximizeConversions")
    self.campaign_service = CampaignService(
        self.google_ads_service, self.sheet_service, self.google_ads_client
    )

  @mock.patch("utils.process_operations_and_errors")
  def test_sheet_input_with_valid_data(
      self, mock_process_operations_and_errors
  ):
    """Test process_campaign_input_sheet method in CampaignService.

    Verifying wheter the service calls the correct function.
    """
    self.campaign_service.process_campaign_input_sheet(
        _VALID_SHEET_DATA
    )
    mock_process_operations_and_errors.assert_called()

  @mock.patch.object(CampaignService, "create_campaign_budget_operation")
  @mock.patch.object(CampaignService, "create_pmax_campaign_operation")
  @mock.patch("utils.retrieve_customer_id")
  def test_campaign_data_row_with_valid_data(
      self,
      mock_retrieve_customer_id,
      mock_create_pmax_campaign_operation,
      mock_create_campaign_budget_operation
    ):
    """Test process_campaign_data_and_create_campaigns in CampaignService.

    Verify whether return object contains expected structure and values.
    """
    mock_retrieve_customer_id.return_value = "123456"
    mock_create_pmax_campaign_operation.return_value = "dummy_operation"
    mock_create_campaign_budget_operation.return_value = "dummy_operation"
    expected_result = {
        _CUSTOMER_ID_KEY: "123456",
        _OPERATIONS_KEY: ("dummy_operation", "dummy_operation"),
        _ERROR_LOG_KEY: ""
    }
    result = self.campaign_service.process_campaign_data_and_create_campaigns(
        _VALID_SHEET_DATA[0]
    )
    self.assertEqual(result, expected_result)

  def test_campaign_data_with_faulty_data(self):
    """Test process_campaign_data_and_create_campaigns in CampaignService.

    Verify whether return object contains expected structure and values when
    input data is invalid.
    """
    result = self.campaign_service.process_campaign_data_and_create_campaigns([
        "",
        "Test Customer",
        "Test Campaign",
        "200",
        "STANDARD",
        "",
        "",
        "",
        "",
        "2024-02-26",
        "2024-03-08",
    ])

    self.assertIsNone(result[_OPERATIONS_KEY])
    self.assertIsNotNone(result[_ERROR_LOG_KEY])

  def test_create_pmax_campaign_bidding_strategy(self):
    """Test create_pmax_campaign_operation method in CampaignService.

    Verify if return tuple contains expected structure and values.
    """
    mutate_operation = self.campaign_service.create_pmax_campaign_operation(
        _CUSTOMER_ID,
        _VALID_SHEET_DATA[0][data_references.NewCampaigns.campaign_name],
        _VALID_SHEET_DATA[0][data_references.NewCampaigns.campaign_status],
        _VALID_SHEET_DATA[0][data_references.NewCampaigns.campaign_target_roas],
        _VALID_SHEET_DATA[0][data_references.NewCampaigns.campaign_target_cpa],
        _VALID_SHEET_DATA[0][data_references.NewCampaigns.bidding_strategy],
        _VALID_SHEET_DATA[0][data_references.NewCampaigns.campaign_start_date],
        _VALID_SHEET_DATA[0][data_references.NewCampaigns.campaign_end_date],
    )
    self.assertEqual(
        mutate_operation.campaign_operation.create.bidding_strategy_type,
        _VALID_SHEET_DATA[0][data_references.NewCampaigns.bidding_strategy],
    )

  def test_create_pmax_campaign_target_cpa(self):
    """Test create_pmax_campaign_operation method in CampaignService.

    Verify if return tuple contains expected structure and values.
    """
    mutate_operation = self.campaign_service.create_pmax_campaign_operation(
        _CUSTOMER_ID,
        _VALID_SHEET_DATA[0][data_references.NewCampaigns.campaign_name],
        _VALID_SHEET_DATA[0][data_references.NewCampaigns.campaign_status],
        _VALID_SHEET_DATA[0][data_references.NewCampaigns.campaign_target_roas],
        _VALID_SHEET_DATA[0][data_references.NewCampaigns.campaign_target_cpa],
        _VALID_SHEET_DATA[0][data_references.NewCampaigns.bidding_strategy],
        _VALID_SHEET_DATA[0][data_references.NewCampaigns.campaign_start_date],
        _VALID_SHEET_DATA[0][data_references.NewCampaigns.campaign_end_date],
    )
    self.assertEqual(
        mutate_operation.campaign_operation.create.maximize_conversions.target_cpa_micros,
        int(_VALID_SHEET_DATA[0][
            data_references.NewCampaigns.campaign_target_cpa]) * 1000000,
    )

  def test_create_pmax_campaign_start_date(self):
    """Test create_pmax_campaign_operation method in CampaignService.

    Verify if return tuple contains expected structure and values.
    """
    start_date = datetime.datetime.strptime(
        _VALID_SHEET_DATA[0]
        [data_references.NewCampaigns.campaign_start_date],
        "%Y-%m-%d").strftime("%Y%m%d")
    mutate_operation = self.campaign_service.create_pmax_campaign_operation(
        _CUSTOMER_ID,
        _VALID_SHEET_DATA[0][data_references.NewCampaigns.campaign_name],
        _VALID_SHEET_DATA[0][data_references.NewCampaigns.campaign_status],
        _VALID_SHEET_DATA[0][data_references.NewCampaigns.campaign_target_roas],
        _VALID_SHEET_DATA[0][data_references.NewCampaigns.campaign_target_cpa],
        _VALID_SHEET_DATA[0][data_references.NewCampaigns.bidding_strategy],
        _VALID_SHEET_DATA[0][data_references.NewCampaigns.campaign_start_date],
        _VALID_SHEET_DATA[0][data_references.NewCampaigns.campaign_end_date],
    )
    self.assertEqual(
        mutate_operation.campaign_operation.create.start_date,
        start_date,
    )

  def test_throw_error_when_no_target_cpa_for_maximize_conversions(self):
    """Test create_pmax_campaign_operation method in CampaignService.

    Validate if missing CPA triggers the expected error.
    """
    target_cpa = ""
    with self.assertRaisesRegex(
        ValueError,
        "Target CPA can't be empty for MaximizeConversions bidding strategy."
    ):
      self.campaign_service.create_pmax_campaign_operation(
          _CUSTOMER_ID,
          _VALID_SHEET_DATA[0][data_references.NewCampaigns.campaign_name],
          _VALID_SHEET_DATA[0][data_references.NewCampaigns.campaign_status],
          _VALID_SHEET_DATA[0][
              data_references.NewCampaigns.campaign_target_roas],
          target_cpa,
          _VALID_SHEET_DATA[0][data_references.NewCampaigns.bidding_strategy],
          _VALID_SHEET_DATA[0][
              data_references.NewCampaigns.campaign_start_date],
          _VALID_SHEET_DATA[0][data_references.NewCampaigns.campaign_end_date]
      )

  def test_throw_error_when_no_target_roas_for_maximize_conversion_value(self):
    """Test create_pmax_campaign_operation method in CampaignService.

    Validate if missing TRoas triggers the expected error message.
    """
    target_roas = ""
    with self.assertRaisesRegex(
        ValueError,
        "Target ROAS can't be empty for MaximizeConversionValue bidding"
        " strategy."
    ):
      self.campaign_service.create_pmax_campaign_operation(
          _CUSTOMER_ID,
          _VALID_SHEET_DATA[1][data_references.NewCampaigns.campaign_name],
          _VALID_SHEET_DATA[1][data_references.NewCampaigns.campaign_status],
          target_roas,
          _VALID_SHEET_DATA[1][
              data_references.NewCampaigns.campaign_target_cpa],
          _VALID_SHEET_DATA[1][data_references.NewCampaigns.bidding_strategy],
          _VALID_SHEET_DATA[1][
              data_references.NewCampaigns.campaign_start_date],
          _VALID_SHEET_DATA[1][data_references.NewCampaigns.campaign_end_date],
      )

  def test_throw_error_when_no_target_roas_in_string(self):
    """Test create_pmax_campaign_operation method in CampaignService.

    Validate if incorrect data type for TRoas triggers the expected error.
    """
    target_roas = "abc"

    with self.assertRaisesRegex(
        ValueError,
        "Target ROAS can't be empty for MaximizeConversionValue bidding"
        " strategy."
    ):
      self.campaign_service.create_pmax_campaign_operation(
          _CUSTOMER_ID,
          _VALID_SHEET_DATA[1][data_references.NewCampaigns.campaign_name],
          _VALID_SHEET_DATA[1][data_references.NewCampaigns.campaign_status],
          target_roas,
          _VALID_SHEET_DATA[1][
              data_references.NewCampaigns.campaign_target_cpa],
          _VALID_SHEET_DATA[1][data_references.NewCampaigns.bidding_strategy],
          _VALID_SHEET_DATA[1][
              data_references.NewCampaigns.campaign_start_date],
          _VALID_SHEET_DATA[1][data_references.NewCampaigns.campaign_end_date],
      )

  def test_create_campaign_budget_operation_budget_delivery(self):
    """Test create_campaign_budget_operation method in CampaignService.

    Validate if return tuple has the expected data structure and values.
    """
    mutate_operation = self.campaign_service.create_campaign_budget_operation(
        _CUSTOMER_ID,
        _VALID_SHEET_DATA[0][data_references.NewCampaigns.campaign_budget],
        _VALID_SHEET_DATA[0][
            data_references.NewCampaigns.budget_delivery_method]
    )
    self.assertEqual(
        mutate_operation.campaign_budget_operation.create.delivery_method,
        _VALID_SHEET_DATA[0][
            data_references.NewCampaigns.budget_delivery_method]
    )

  def test_create_campaign_budget_operation_budget_amount(self):
    """Test create_campaign_budget_operation method in CampaignService.

    Validate if return tuple has the expected data structure and values.
    """
    mutate_operation = self.campaign_service.create_campaign_budget_operation(
        _CUSTOMER_ID,
        _VALID_SHEET_DATA[0][data_references.NewCampaigns.campaign_budget],
        _VALID_SHEET_DATA[0][
            data_references.NewCampaigns.budget_delivery_method]
    )
    self.assertEqual(
        mutate_operation.campaign_budget_operation.create.amount_micros,
        int(_VALID_SHEET_DATA[0][
            data_references.NewCampaigns.campaign_budget]) * 1000000,
    )

  def test_throw_error_when_no_budget(self):
    """Test create_campaign_budget_operation method in CampaignService.

    Validate the expected error message for missing budget.
    """
    budget = ""

    with self.assertRaisesRegex(
        ValueError, "Campaign Budget should be a number."):
      self.campaign_service.create_campaign_budget_operation(
          _CUSTOMER_ID,
          budget,
          _VALID_SHEET_DATA[0][
              data_references.NewCampaigns.budget_delivery_method
          ]
      )

  def test_throw_error_when_budget_not_a_number(self):
    """Test create_campaign_budget_operation method in CampaignService.

    Validate if incorrect data type for budget triggers expected error message.
    """
    budget = "Zero"

    with self.assertRaisesRegex(
        ValueError, "Campaign Budget should be a number."):
      self.campaign_service.create_campaign_budget_operation(
          _CUSTOMER_ID,
          budget,
          _VALID_SHEET_DATA[0][
              data_references.NewCampaigns.budget_delivery_method
          ]
      )

  def test_throw_error_when_budget_delivery_method_faulty(self):
    """Test create_campaign_budget_operation method in CampaignService.

    Validate if a non-existing budget methods triggers the expected error.
    """
    budget_delivery_method = "NOT_A_DELIVERY_METHOD"

    with self.assertRaisesRegex(
        ValueError,
        "Budget delivery method should be either STANDARD or ACCELERATED."
    ):
      self.campaign_service.create_campaign_budget_operation(
          _CUSTOMER_ID,
          _VALID_SHEET_DATA[0][
              data_references.NewCampaigns.campaign_budget],
          budget_delivery_method
      )


if __name__ == "__main__":
  unittest.main()
