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
"""Tests for Utils Module."""

import unittest
from unittest import mock
import data_references
import utils


class TestUtils(unittest.TestCase):
  """Test utils."""

  def setUp(self):
    super().setUp()
    self.google_ads_service = mock.MagicMock()
    self.sheet_service = mock.MagicMock()

  @mock.patch("sheet_api.SheetsService")
  def test_retrieve_customer_id(self, mock_sheets_service):
    """Test Retrieve Customer ID when match in sheet."""
    customer_name = "customer_name_1"
    customer_id = "customer_id_1"
    mock_sheets_service.get_sheet_values.return_value = [
        [customer_name, customer_id]]

    self.assertEqual(utils.retrieve_customer_id(
        customer_name, mock_sheets_service), customer_id)

  @mock.patch("sheet_api.SheetsService")
  def test_retrieve_customer_id_not_in_sheet(self, mock_sheets_service):
    """Test Retrieve Customer ID when no match in sheet."""
    mock_sheets_service.get_sheet_values.return_value = [
        ["Other_Customer", "Other_Customer_Id"]]

    self.assertIsNone(utils.retrieve_customer_id(
        "customer_name_1", mock_sheets_service))

  @mock.patch("utils.process_api_response_and_errors")
  def test_process_operations(self, mock_process_api_response_and_errors):
    """Test processing of API operations.

    Validates if the relevant function calls are made, based on input.
    """
    mock_process_api_response_and_errors.return_value = True
    self.sheet_service.get_sheet_id.return_value = "1234abd"
    self.google_ads_service.bulk_mutate.return_value = ("dummy_response", "")

    utils.process_operations_and_errors(
        "customer_id_1",
        ("dummy_budget_operation", "dummy_campaign_operation"),
        "",
        1,
        self.sheet_service,
        self.google_ads_service,
        "Sitelinks"
    )

    self.google_ads_service.bulk_mutate.assert_called_once_with(
        ("dummy_budget_operation", "dummy_campaign_operation"),
        "customer_id_1"
    )

  def test_process_operations_errors(self):
    """Test processing of API operation errors.

    Validates if the relevant function calls are made, based on input.
    """
    self.sheet_service.get_sheet_id.return_value = "1234abd"
    self.google_ads_service.bulk_mutate.return_value = (None, "dummy_response")

    utils.process_operations_and_errors(
        "customer_id_1",
        ("dummy_budget_operation", "dummy_campaign_operation"),
        "",
        1,
        self.sheet_service,
        self.google_ads_service,
        "NewCampaigns"
    )

    self.sheet_service.variable_update_sheet_status.assert_called_once_with(
        1,
        "1234abd",
        data_references.NewCampaigns.campaign_upload_status,
        data_references.RowStatus.error,
        "dummy_response",
        data_references.NewCampaigns.error_message,
    )

  def test_process_api_response_and_errors_no_errors(self):
    """Test processing of API response.

    Validates if the relevant function calls are made, based on input.
    """
    mock_response = mock.MagicMock()
    mock_response.mutate_operation_responses[
        1].campaign_asset_result.resource_name = "Test Resource Name"

    self.sheet_service.get_sheet_id.return_value = "1234abd"

    utils.process_api_response_and_errors(
        mock_response,
        "",
        1,
        "sheetid_1234",
        "Sitelinks",
        self.sheet_service,
    )

    self.sheet_service.variable_update_sheet_status.assert_called_once_with(
        1,
        "sheetid_1234",
        data_references.Sitelinks.upload_status,
        data_references.RowStatus.uploaded,
        "Test Resource Name",
        data_references.Sitelinks.sitelink_resource,
    )
    self.sheet_service.refresh_campaign_list.assert_called_once()

  def test_process_api_response_and_errors_with_errors(self):
    """Test processing of API Errors.

    Validates if the relevant function calls are made, based on input.
    """
    self.sheet_service.get_sheet_id.return_value = "1234abd"

    utils.process_api_response_and_errors(
        None,
        "dummy_response",
        1,
        "sheetid_1234",
        "Sitelinks",
        self.sheet_service,
    )

    self.sheet_service.variable_update_sheet_status.assert_called_once_with(
        1,
        "sheetid_1234",
        data_references.Sitelinks.upload_status,
        data_references.RowStatus.error,
        "dummy_response",
        data_references.Sitelinks.error_message,
    )

  @mock.patch("sheet_api.SheetsService")
  def test_retrieve_campaign_id(self, mock_sheets_service):
    """Test Retrieve campaign ID when match in sheet."""
    customer_name = "customer_name_1"
    customer_id = "customer_id_1"
    campaign_name = "campaign_name_1"
    campaign_id = "campaign_id_1"
    mock_sheets_service.get_sheet_values.return_value = [
        [customer_name, customer_id, campaign_name, campaign_id]
    ]

    self.assertEqual(
        utils.retrieve_campaign_id(
            customer_name, campaign_name, mock_sheets_service),
        (customer_id, campaign_id))

  @mock.patch("sheet_api.SheetsService")
  def test_retrieve_campaign_id_not_in_sheet(self, mock_sheets_service):
    """Test Retrieve campaign ID when no match in sheet."""
    mock_sheets_service.get_sheet_values.return_value = [
        ["Other_campaign", "Other_campaign_Id"]]

    self.assertIsNone(utils.retrieve_campaign_id(
        "customer_name_1", "campaign_name_1", mock_sheets_service))
