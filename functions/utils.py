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
"""Util functions that help process sheet content for API operations.

Data is stored and modified in a Google Spreadsheet, this sheet data
serves as input for the API functions. In this file there are some generic
functions that help process the sheet data, and request the relevant API
operations.
"""

from collections.abc import Sequence
import ads_api
import data_references
from sheet_api import SheetsService


def process_operations_and_errors(
    customer_id: str,
    operations: (
        tuple[ads_api.BudgetOperation, ads_api.CampaignOperation]
        | tuple[ads_api.SitelinkOperation, ads_api.LinkSitelinkOperation]
        | None
    ),
    error_log: str,
    row_number: int,
    sheet_service: SheetsService,
    google_ads_service: ads_api.AdService,
    sheet_name: str,
) -> None:
  """Processing Mutate Operations and Error Log from campaign service.

  Creative campaigns in Google Ads based on mutate operations input, and / or
  writing the status / error message to the spreadsheet for further action.

  Args:
    customer_id: Google ads customer id.
    operations: Tuple containing two dicts (BudgetOperation,
      CampaignOperation)
    error_log: String representation of the error message.
    row_number: Corresponding sheetrow number to the sheet entry.
    sheet_service: instance of sheet_service for dependancy injection.
    google_ads_service: instance of google_ads_service.
    sheet_name: Name of the sheet in google spreadsheet.

  Returns:
    None. Output written to Google Ads API and status written to logs and
    sheet.
  """
  sheet_id = sheet_service.get_sheet_id(sheet_name)

  if error_log:
    sheet_service.variable_update_sheet_status(
        row_number,
        sheet_id,
        data_references.NewCampaigns.campaign_upload_status,
        data_references.RowStatus.error,
        error_log,
        data_references.NewCampaigns.error_message,
    )
  elif operations:
    response, error_message = (
        google_ads_service.bulk_mutate(
            operations,
            customer_id,
        )
    )
    process_api_response_and_errors(
        response, error_message, row_number, sheet_id, sheet_name, sheet_service
    )


def process_api_response_and_errors(
    response: ads_api.ApiResponse,
    error_message: str,
    row_number: int,
    sheet_id: str,
    sheet_name: str,
    sheet_service: SheetsService,
    campaign_details: Sequence[str | int] = None,
    asset_group_name: str = None,
) -> None:
  """Processing the API responce and write to spreadsheet.

  Args:
    response: Google Ads API reponse dict.
    error_message: String representation of the error message.
    row_number: Corresponding sheetrow number to the sheet entry.
    sheet_id: Google Sheets id for the spreadsheet.
    sheet_name: Google Sheets name for the spreadsheet.
    sheet_service: Instance of sheet_service for dependancy injection.
    campaign_details: Campaign data from spreadsheet in array form if updating
      Asset Group.
    asset_group_name: Name of the asset groupif updating Asset Group.

  Returns:
    None. Status written to logs and sheet.
  """
  sitelink_resource = None
  resource_name_col = None
  upload_status_col = None
  error_message_col = None
  if sheet_name == data_references.SheetNames.new_asset_groups:
    upload_status_col = data_references.newAssetGroupsColumnMap.STATUS.value
    error_message_col = data_references.newAssetGroupsColumnMap.MESSAGE
    resource_name_col = None
  if sheet_name == data_references.SheetNames.new_campaigns:
    upload_status_col = data_references.NewCampaigns.campaign_upload_status
    error_message_col = data_references.NewCampaigns.error_message
    resource_name_col = None
  if sheet_name == data_references.SheetNames.sitelinks:
    upload_status_col = data_references.Sitelinks.upload_status
    error_message_col = data_references.Sitelinks.error_message
    resource_name_col = data_references.Sitelinks.sitelink_resource
    if response:
      sitelink_resource = response.mutate_operation_responses[
          1
      ].campaign_asset_result.resource_name

  if response:
    sheet_service.variable_update_sheet_status(
        row_number,
        sheet_id,
        upload_status_col,
        data_references.RowStatus.uploaded,
        sitelink_resource,
        resource_name_col,
    )

    if sheet_name == data_references.SheetNames.new_asset_groups:
      add_asset_group_sheetlist_to_spreadsheet(
          response, campaign_details, asset_group_name, sheet_service
      )

  elif error_message:
    sheet_service.variable_update_sheet_status(
        row_number,
        sheet_id,
        upload_status_col,
        data_references.RowStatus.error,
        error_message,
        error_message_col,
    )


def add_asset_group_sheetlist_to_spreadsheet(
    response: ads_api.ApiResponse,
    campaign_details: Sequence[str | int],
    asset_group_name: str,
    sheet_service: SheetsService,
) -> None:
  """Adds Asset Group to spreadsheet.

  Args:
    response: Response object from creating asset group through the API.
    campaign_details: Details of the campaign that contains this Asset Group.
    asset_group_name: Name of the asset group that is being added to the
      spreadsheet.
    sheet_service: Instance of sheet_service for dependancy injection.

  Returns:
    Str or None. String value containing the Google Ads customer id.
  """
  asset_group_id = response.mutate_operation_responses[
      0
  ].asset_group_result.resource_name.split("/")[-1]

  # Add asset_group_sheetlist to the spreadsheet.
  sheet_service.add_new_asset_group_to_list_sheet([
      campaign_details[data_references.CampaignList.customer_name],
      campaign_details[data_references.CampaignList.customer_id],
      campaign_details[data_references.CampaignList.campaign_name],
      campaign_details[data_references.CampaignList.campaign_id],
      asset_group_name,
      asset_group_id,
  ])


def retrieve_customer_id(
    customer_name: str, sheet_service: SheetsService
) -> str | None:
  """Retrieves Customer ID for input customer name.

  Args:
    customer_name: String value containing Google Ads Customer name.
    sheet_service: instance of sheet_service for dependancy injection.

  Returns:
    Str or None. String value containing the Google Ads customer id.
  """
  customer_data: Sequence[Sequence[str]] = sheet_service.get_sheet_values(
      data_references.SheetNames.customers
      + "!"
      + data_references.SheetRanges.customers
  )

  for row in customer_data:
    if customer_name in row:
      return row[data_references.CustomerList.customer_id]

  return None


def retrieve_campaign_id(
    customer_name: str, campaign_name: str, sheet_service: SheetsService
) -> tuple[str, str] | None:
  """Retrieves Campaign ID for input campaign name.

  Args:
    customer_name: String value containing Google Ads Customer name.
    campaign_name: String value containing Google Ads Campaign name.
    sheet_service: Instance of sheet_service for dependancy injection.

  Returns:
    Tuple or None. Tuple containing the Google Ads customer id and campaign id.
    (customer_id, campaign_id)
  """
  campaign_data: Sequence[Sequence[str]] = sheet_service.get_sheet_values(
      f"{data_references.SheetNames.campaigns}!"
      f"{data_references.SheetRanges.campaigns}"
  )
  for row in campaign_data:
    if campaign_name in row and customer_name in row:
      return (
          row[data_references.CampaignList.customer_id],
          row[data_references.CampaignList.campaign_id],
      )

  return None
