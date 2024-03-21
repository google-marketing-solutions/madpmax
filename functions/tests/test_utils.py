import reference_enums
import unittest
from unittest import mock
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

  def test_process_operations(self):
    """Test processing of API operations.

    Validates if the relevant function calls are made, based on input.
    """
    self.sheet_service.get_sheet_id.return_value = "1234abd"
    self.google_ads_service.bulk_mutate.return_value = ("dummy_response", "")

    utils.process_operations_and_errors(
        "customer_id_1",
        ("dummy_budget_operation", "dummy_campaign_operation"),
        "",
        1,
        self.sheet_service,
        self.google_ads_service
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
        self.google_ads_service
    )

    self.sheet_service.variable_update_sheet_status.assert_called_once_with(
        1,
        "1234abd",
        reference_enums.NewCampaigns.campaign_upload_status,
        reference_enums.RowStatus.error,
        "dummy_response",
        reference_enums.NewCampaigns.error_message,
    )

  def test_process_api_response_and_errors_no_errors(self):
    """Test processing of API response.

    Validates if the relevant function calls are made, based on input.
    """
    self.sheet_service.get_sheet_id.return_value = "1234abd"

    utils.process_api_response_and_errors(
        "dummy_response",
        "",
        1,
        "sheetid_1234",
        self.sheet_service,
    )

    self.sheet_service.variable_update_sheet_status.assert_called_once_with(
        1,
        "sheetid_1234",
        reference_enums.NewCampaigns.campaign_upload_status,
        reference_enums.RowStatus.uploaded
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
        self.sheet_service,
    )

    self.sheet_service.variable_update_sheet_status.assert_called_once_with(
        1,
        "sheetid_1234",
        reference_enums.NewCampaigns.campaign_upload_status,
        reference_enums.RowStatus.error,
        "dummy_response",
        reference_enums.NewCampaigns.error_message,
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
