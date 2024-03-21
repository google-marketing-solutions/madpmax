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

from typing import Mapping, TypeAlias
from ads_api import AdService
import reference_enums
from sheet_api import SheetsService

_BudgetOperation: TypeAlias = Mapping[str, str | int]
_CampaignOperation: TypeAlias = Mapping[
    str,
    str | bool | Mapping[str, int]
]
_CampaignResponse: TypeAlias = Mapping[
    str,
    bool | Mapping[
        str, str
    ]
]


def process_operations_and_errors(
    customer_id: str,
    operations: tuple[_BudgetOperation, _CampaignOperation] | None,
    error_log: str,
    row_number: int,
    sheet_service: SheetsService,
    google_ads_service: AdService
) -> None:
  """Processing Mutate Operations and Error Log from campaign service.

  Creative campaigns in Google Ads based on mutate operations input, and / or
  writing the status / error message to the spreadsheet for further action.

  Args:
    customer_id: Google ads customer id.
    operations: Typle containing to dicts, (_BudgetOperation,
        _CampaignOperation)
    error_log: String representation of the error message.
    row_number: Corresponding sheetrow number to the sheet entry.
    sheet_service: instance of sheet_service for dependancy injection.
    google_ads_service: instance of google_ads_service.

  Returns:
    None. Output written to Google Ads API and status written to logs and
    sheet.
  """
  sheet_id = sheet_service.get_sheet_id(
      reference_enums.SheetNames.new_campaigns)

  if error_log:
    sheet_service.variable_update_sheet_status(
        row_number,
        sheet_id,
        reference_enums.NewCampaigns.campaign_upload_status,
        reference_enums.RowStatus.error,
        error_log,
        reference_enums.NewCampaigns.error_message,
    )
  elif operations:
    campaigns_response, campaigns_error_message = (
        google_ads_service.bulk_mutate(
            operations,
            customer_id,
        )
    )
    process_api_response_and_errors(
        campaigns_response,
        campaigns_error_message,
        row_number,
        sheet_id,
        sheet_service
    )


def process_api_response_and_errors(
    campaigns_response: _CampaignResponse,
    campaigns_error_message: str,
    row_number: int,
    sheet_id: str,
    sheet_service: SheetsService
) -> None:
  """Processing the API responce and write to spreadsheet.

  Args:
    campaigns_response: Google Ads API reponse dict.
    campaigns_error_message: String representation of the error message.
    row_number: Corresponding sheetrow number to the sheet entry.
    sheet_id: Google Sheets id for the spreadsheet.
    sheet_service: instance of sheet_service for dependancy injection.

  Returns:
    None. Status written to logs and sheet.
  """
  if campaigns_response:
    sheet_service.variable_update_sheet_status(
        row_number,
        sheet_id,
        reference_enums.NewCampaigns.campaign_upload_status,
        reference_enums.RowStatus.uploaded,
    )

    sheet_service.refresh_campaign_list()
  elif campaigns_error_message:
    sheet_service.variable_update_sheet_status(
        row_number,
        sheet_id,
        reference_enums.NewCampaigns.campaign_upload_status,
        reference_enums.RowStatus.error,
        campaigns_error_message,
        reference_enums.NewCampaigns.error_message,
    )


def retrieve_customer_id(
    customer_name: str,
    sheet_service: SheetsService
) -> str | None:
  """Retrieves Customer ID for input customer name.

  Args:
    customer_name: String value containing Google Ads Customer name.
    sheet_service: instance of sheet_service for dependancy injection.

  Returns:
    Str or None. String value containing the Google Ads customer id.
  """
  customer_data: list[list[str]] = sheet_service.get_sheet_values(
      reference_enums.SheetNames.customers +
      reference_enums.SheetRanges.customers
  )

  for row in customer_data:
    if customer_name in row:
      return row[reference_enums.CustomerList.customer_id]

  return None


def retrieve_campaign_id(
    customer_name: str,
    campaign_name: str,
    sheet_service: SheetsService
) -> tuple[str, str] | None:
  """Retrieves Campaign ID for input campaign name.

  Args:
    customer_name: String value containing Google Ads Customer name.
    campaign_name: String value containing Google Ads Campaign name.
    sheet_service: instance of sheet_service for dependancy injection.

  Returns:
    Tuple or None. Tuple containing the Google Ads customer id and campaign id.
    (customer_id, campaign_id)
  """
  campaign_data: list[list[str]] = sheet_service.get_sheet_values(
      reference_enums.SheetNames.campaigns +
      reference_enums.SheetRanges.campaigns
  )

  for row in campaign_data:
    if campaign_name in row and customer_name in row:
      return (
          row[reference_enums.CampaignList.customer_id],
          row[reference_enums.CampaignList.campaign_id]
      )

  return None
