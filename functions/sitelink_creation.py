# Copyright 2023 Google LLC
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
"""Provides functionality to create sitelinks."""

from typing import TypeAlias, Mapping
from absl import logging
import ads_api
import data_references
from google.ads.googleads.client import GoogleAdsClient
import sheet_api
import utils
import validators


_SitelinkOperation: TypeAlias = Mapping[
    str,
    str | list | Mapping[str, str]
]
_LinkSitelinkOperation: TypeAlias = Mapping[
    str, str
]

_CUSTOMER_ID: str = "customer_id"
_OPERATIONS: str = "operations"
_ERROR_LOG: str = "error_log"


class SitelinkService:
  """Class for Sitelink Creation.

  Contains all methods to create Sitelinks in Google Ads.
  """

  def __init__(
      self,
      sheet_service: sheet_api.SheetsService,
      google_ads_service: ads_api.AdService,
      google_ads_client: GoogleAdsClient
  ) -> None:
    """Constructs the SitelinksService instance.

    Args:
      sheet_service: Instance of sheet_service for dependency injection.
      google_ads_service: Instance of the google_ads_service for dependency
        injection.
      google_ads_client: Instance of Google Ads API client.
    """

    self._google_ads_client = google_ads_client
    self._google_ads_service = google_ads_service
    self._sheet_service = sheet_service
    self._sitelinks_temporary_id = -1

  def process_sitelink_input_sheet(
      self,
      sitelink_data: list[list[str]]
  ) -> None:
    """Loops through input Lists, and decides on next action.

    Verifies if input list meets the minimum length requirement and if the row
    has not been uploaded to Google Ads. If conditions are met, the function
    triggers the Sitelink Creation flow. Results of sitelink creation are
    processed and output is logged and written to the spreadsheet.

    Args:
      sitelink_data: Input data for creating new sitelinks in array form.
    """

    for row_num, row in enumerate(sitelink_data):
      result = None
      if (len(row) > data_references.Sitelinks.description2
          and row[data_references.Sitelinks.upload_status] !=
          data_references.RowStatus.uploaded):
        if result := self.process_sitelink_data_and_create_sitelink(
            row):
          utils.process_operations_and_errors(
              result[_CUSTOMER_ID],
              result[_OPERATIONS],
              result[_ERROR_LOG],
              row_num,
              self._sheet_service,
              self._google_ads_service,
              data_references.SheetNames.sitelinks
          )

  def process_sitelink_data_and_create_sitelink(
      self,
      sitelink_data: list[str]
  ) -> Mapping[str, tuple[_SitelinkOperation, _LinkSitelinkOperation] | str]:
    """Creates campaigns via google API based.

    Args:
      sitelink_data: Array for creating new sitelinks.

    Returns:
      Values for Customer Id, Google Ads API Mutate operations or an Error
      Message to write to the sheet. For example:

        {'customer_id': '123456',
         'operations': (_SitelinkOperation, _LinkSitelinkOperation)
         'error_log': 'Sitelink Data not Complete.'}

    """
    customer_id, campaign_id = utils.retrieve_campaign_id(
        sitelink_data[data_references.Sitelinks.customer_name],
        sitelink_data[data_references.Sitelinks.campaign_name],
        self._sheet_service
    )

    logging.info("Creating Sitelink API Operation")
    sitelink_error = None
    sitelink_operation = None
    try:
      sitelink_operation = self.create_sitelink(
          customer_id, sitelink_data
      )
    except ValueError as e:
      sitelink_error = str(e)

    logging.info("Creating Campaign Asset API Operation")
    campaign_asset_error = None
    campaign_asset_operation = None
    try:
      campaign_asset_operation = self.link_sitelink_to_campaign(
          customer_id,
          campaign_id
      )
    except ValueError as e:
      campaign_asset_error = str(e)

    error_message = "\n".join(
        x for x in [sitelink_error, campaign_asset_error] if x)

    result = {
        _CUSTOMER_ID: customer_id,
        _OPERATIONS: (sitelink_operation, campaign_asset_operation),
        _ERROR_LOG: error_message
    }

    if error_message:
      result[_OPERATIONS] = None

    return result

  def create_sitelink(
      self,
      customer_id: str,
      sitelink_data: list[str]
  ) -> tuple[_SitelinkOperation, str]:
    """Sets mutate object for creating campaign and budget for the campaign.

    Args:
      customer_id: Google ads customer id.
      sitelink_data: Array of string values to create sitelink.

    Returns:
      The Google Ads sitelink asset mutate api operation.

    Raises:
      ValueError: In case required input fields are missing from sitelink_data.
    """
    asset_service = self._google_ads_client.get_service("AssetService")
    self._sitelinks_temporary_id -= 1
    resource_name = asset_service.asset_path(
        customer_id, self._sitelinks_temporary_id)

    sitelink_operation = self._google_ads_client.get_type("MutateOperation")

    sitelink_asset = sitelink_operation.asset_operation.create
    if sitelink_data[data_references.Sitelinks.final_urls]:
      if validators.url(sitelink_data[data_references.Sitelinks.final_urls]):
        sitelink_asset.final_urls.append(
            sitelink_data[data_references.Sitelinks.final_urls])
      else:
        raise ValueError("Final URL is not a valid URL.")
    else:
      raise ValueError("Final URL can not be empty.")

    sitelink_asset.resource_name = resource_name
    if sitelink_data[data_references.Sitelinks.description1]:
      sitelink_asset.sitelink_asset.description1 = sitelink_data[
          data_references.Sitelinks.description1]
    else:
      raise ValueError("Description1 can not be empty.")
    if sitelink_data[data_references.Sitelinks.description2]:
      sitelink_asset.sitelink_asset.description2 = sitelink_data[
          data_references.Sitelinks.description2]
    else:
      raise ValueError("Description2 can not be empty.")
    if sitelink_data[data_references.Sitelinks.link_text]:
      sitelink_asset.sitelink_asset.link_text = sitelink_data[
          data_references.Sitelinks.link_text]
    else:
      raise ValueError("Link Text can not be empty.")

    return sitelink_operation

  def link_sitelink_to_campaign(
      self,
      customer_id: str,
      campaign_id: str
  ) -> _LinkSitelinkOperation:
    """Creates sitelink assets, which can be added to campaigns.

    Args:
      customer_id: The customer ID for which to add the keyword.
      campaign_id: The campaign to which sitelinks will be added.

    Returns:
      The Google Ads mutate api operation.

    Raises:
      ValueError: In case campaign or customer id are missing.
    """
    if not customer_id:
      raise ValueError(
          "Customer ID is required to link a sitelink to a campaign.")
    if not campaign_id:
      raise ValueError(
          "Campaign ID is required to link a sitelink to a campaign.")

    asset_service = self._google_ads_client.get_service("AssetService")
    resource_name = asset_service.asset_path(
        customer_id, self._sitelinks_temporary_id
    )

    campaign_service = self._google_ads_client.get_service("CampaignService")
    campaign_operation = self._google_ads_client.get_type(
        "MutateOperation")
    campaign_asset = campaign_operation.campaign_asset_operation.create
    campaign_asset.asset = resource_name
    campaign_asset.campaign = campaign_service.campaign_path(
        customer_id, campaign_id
    )
    campaign_asset.field_type = (
        self._google_ads_client.enums.AssetFieldTypeEnum.SITELINK
    )

    return campaign_operation
