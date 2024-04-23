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
"""Tests for Sitelink Creation."""

from typing import Final
import unittest
from unittest import mock
import data_references
import sitelink_creation


_CUSTOMER_ID: Final[str] = "customer_id_1"
_CAMPAIGN_ID: Final[str] = "campaign_id_1"
_VALID_SHEET_DATA: Final[list[list[str]]] = [
    [
        "",
        "",
        "Test Customer 1",
        "Test Campaign 1",
        "Test Site Link Text",
        "https://www.example.com",
        "Sitelink Description 1",
        "Sitelink Description 2",
    ],
    [
        "",
        "",
        "Test Customer 2",
        "Test Campaign 2",
        "Test Site Link Text",
        "https://www.example.com",
        "Sitelink Description 1",
        "Sitelink Description 2",
    ]
]

_CUSTOMER_ID_KEY: str = "customer_id"
_OPERATIONS_KEY: str = "operations"
_ERROR_LOG_KEY: str = "error_log"


class TestSitelinkCreation(unittest.TestCase):
  """Test Sitelink Creation."""

  def setUp(self):
    super().setUp()
    self.sheet_service = mock.MagicMock()
    self.google_ads_client = mock.Mock()
    self.google_ads_service = mock.Mock()
    self.sitelink_service = sitelink_creation.SitelinkService(
        self.sheet_service, self.google_ads_service, self.google_ads_client
    )
    self.google_ads_client.enums.AssetFieldTypeEnum.SITELINK = "SITELINK"

  @mock.patch.object(sitelink_creation.SitelinkService,
                     "process_sitelink_data_and_create_sitelink")
  @mock.patch("utils.process_operations_and_errors")
  def test_sheet_input_with_valid_data(
      self,
      mock_process_operations_and_errors,
      mock_process_sitelink_data_and_create_sitelink
    ):
    """Test process_sitelink_input_sheet method in SitelinkService.

    Verifying wheter the service calls the correct function.
    """
    expected_result = {
        _CUSTOMER_ID_KEY: "123456",
        _OPERATIONS_KEY: ("dummy_operation", "dummy_operation"),
        _ERROR_LOG_KEY: ""
    }
    mock_process_sitelink_data_and_create_sitelink.return_value = expected_result
    self.sitelink_service.process_sitelink_input_sheet(
        _VALID_SHEET_DATA
    )
    mock_process_operations_and_errors.assert_called()

  @mock.patch.object(sitelink_creation.SitelinkService,
                     "create_sitelink")
  @mock.patch.object(sitelink_creation.SitelinkService,
                     "link_sitelink_to_campaign")
  @mock.patch("utils.retrieve_campaign_id")
  def test_sitelink_data_row_with_valid_data(
      self,
      mock_retrieve_campaign_id,
      mock_create_sitelink,
      mock_link_sitelink_to_campaign
    ):
    """Test process_sitelink_data_and_create_sitelink in SitelinkService.

    Verify whether return object contains expected structure and values.
    """
    mock_retrieve_campaign_id.return_value = ("123456", "56789")
    mock_create_sitelink.return_value = "dummy_operation"
    mock_link_sitelink_to_campaign.return_value = "dummy_operation"
    expected_result = {
        _CUSTOMER_ID_KEY: "123456",
        _OPERATIONS_KEY: ("dummy_operation", "dummy_operation"),
        _ERROR_LOG_KEY: ""
    }
    result = self.sitelink_service.process_sitelink_data_and_create_sitelink(
        _VALID_SHEET_DATA[0]
    )
    self.assertEqual(result, expected_result)

  @mock.patch("utils.retrieve_campaign_id")
  def test_sitelink_data_with_faulty_data(self, mock_retrieve_campaign_id):
    """Test process_sitelink_data_and_create_sitelink in SitelinkService.

    Verify whether return object contains expected structure and values when
    input data is invalid.
    """
    mock_retrieve_campaign_id.return_value = ("123456", "56789")
    result = self.sitelink_service.process_sitelink_data_and_create_sitelink(
        [
            "",
            "",
            "Test Customer 2",
            "Test Campaign 2",
            "Test Site Link Text",
            "",
            "Sitelink Description 1",
            "Sitelink Description 2",
        ]
    )

    self.assertEqual(result[_ERROR_LOG_KEY], "Final URL can not be empty.")

  def test_create_sitelink_desciption1(self):
    """Test _create_sitelink method in SitelinkService.

    Verify if return tuple contains expected structure and values.
    """
    description1 = _VALID_SHEET_DATA[0][data_references.Sitelinks.description1]

    sitelink_operation = self.sitelink_service.create_sitelink(
        _CUSTOMER_ID, _VALID_SHEET_DATA[0]
    )
    self.assertEqual(
        sitelink_operation.asset_operation.create.sitelink_asset.description1,
        description1,
    )

  def test_create_sitelink_link_text(self):
    """Test _create_sitelink method in SitelinkService.

    Verify if return tuple contains expected structure and values.
    """
    link_text = _VALID_SHEET_DATA[0][data_references.Sitelinks.link_text]

    sitelink_operation = self.sitelink_service.create_sitelink(
        _CUSTOMER_ID, _VALID_SHEET_DATA[0]
    )
    self.assertEqual(
        sitelink_operation.asset_operation.create.sitelink_asset.link_text,
        link_text,
    )

  def test_throw_error_when_no_link_text(self):
    """Test create_pmax_campaign_operation method in CampaignService.

    Validate if missing CPA triggers the expected error.
    """
    invalid_data = _VALID_SHEET_DATA[0].copy()
    invalid_data[data_references.Sitelinks.link_text] = ""

    with self.assertRaisesRegex(
        ValueError,
        "Link Text can not be empty."
    ):
      self.sitelink_service.create_sitelink(
          _CUSTOMER_ID,
          invalid_data
      )

  @mock.patch("validators.url")
  def test_throw_error_when_invalid_url(self, mock_validators_url):
    """Test create_pmax_campaign_operation method in CampaignService.

    Validate if missing CPA triggers the expected error.
    """
    mock_validators_url.return_value = False
    invalid_data = _VALID_SHEET_DATA[0].copy()
    invalid_data[data_references.Sitelinks.final_urls] = "error"

    with self.assertRaisesRegex(
        ValueError,
        "Final URL is not a valid URL."
    ):
      self.sitelink_service.create_sitelink(
          _CUSTOMER_ID,
          invalid_data
      )

  def test_link_sitelink_to_campaign_field_type(self):
    """Test link_sitelink_to_campaign method in SitelinkService.

    Verify if method returns expected API operation structure and sitelink
    value.
    """
    link_sitelink_operation = self.sitelink_service.link_sitelink_to_campaign(
        _CUSTOMER_ID, _CAMPAIGN_ID
    )
    self.assertEqual(
        link_sitelink_operation.campaign_asset_operation.create.field_type,
        data_references.AssetTypes.sitelink,
    )

  def test_link_sitelink_to_campaign_campaign_resource(self):
    """Test link_sitelink_to_campaign method in SitelinkService.

    Verify if method returns expected API operation structure and campaign
    resource value.
    """
    campaign_resource = f"customers/{_CUSTOMER_ID}/campaigns/{_CAMPAIGN_ID}"
    self.google_ads_client.get_service(
        "CampaignService").campaign_path.return_value = campaign_resource

    link_sitelink_operation = self.sitelink_service.link_sitelink_to_campaign(
        _CUSTOMER_ID, _CAMPAIGN_ID
    )

    self.assertEqual(
        link_sitelink_operation.campaign_asset_operation.create.campaign,
        campaign_resource,
    )

  def test_link_sitelink_to_campaign_no_customer_id(self):
    """Test link_sitelink_to_campaign method in SitelinkService.

    Verify if method returns expected Value Error for missing customer id.
    """
    with self.assertRaisesRegex(
        ValueError,
        "Customer ID is required to link a sitelink to a campaign."
    ):
      self.sitelink_service.link_sitelink_to_campaign(
          None, _CAMPAIGN_ID
      )

  def test_link_sitelink_to_campaign_no_campaign_id(self):
    """Test link_sitelink_to_campaign method in SitelinkService.

    Verify if method returns expected Value Error for missing campaign id.
    """
    with self.assertRaisesRegex(
        ValueError,
        "Campaign ID is required to link a sitelink to a campaign."
    ):
      self.sitelink_service.link_sitelink_to_campaign(
          _CUSTOMER_ID, None
      )
