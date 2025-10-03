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
"""Provides functionality to create campaigns."""

import datetime
from typing import Mapping
import uuid
from absl import logging
import ads_api
import data_references
from google.ads.googleads import client
from sheet_api import SheetsService
import utils


_CUSTOMER_ID: str = "customer_id"
_OPERATIONS: str = "operations"
_ERROR_LOG: str = "error_log"


class CampaignService:
  """Class for Campaign Creation.

  Contains all methods to create pMax Campaings in Google Ads.

  Attributes:
    google_ads_service: instance of google_ads_service.
    sheet_service: Instance of Google Ads API client.
    _google_ads_client: instance of sheet_service for dependancy injection.
    budget_temporary_id: Temp ID used to identify and assign Budgets operations
      to campaign operations, prior to API upload.
    performance_max_campaign_temporary_id: Temp ID used to identify and assign
      link API operations to a campaign operation, prior to API upload.
  """

  def __init__(
      self,
      google_ads_service: ads_api.AdService,
      sheet_service: SheetsService,
      google_ads_client: client.GoogleAdsClient,
  ) -> None:
    """Constructs the CampaignService instance.

    Args:
      google_ads_service: instance of google_ads_service.
      sheet_service: instance of sheet_service for dependancy injection.
      google_ads_client: Instance of Google Ads API client.
    """
    self.google_ads_service = google_ads_service
    self.sheet_service = sheet_service
    self._google_ads_client = google_ads_client
    self.budget_temporary_id = -2000
    self.performance_max_campaign_temporary_id = -100

  def process_campaign_input_sheet(
      self, new_campaign_data: list[list[str]]
  ) -> None:
    """Loops through input Lists, and decides on next action.

    Verifies if input list meets the minimum length requirement and if the row
    has not been uploaded to Google Ads. If conditions are met, the function
    trigger the Campaign Creation flow. Results of campaign creation are
    processed and output is logged and written to the spreadsheet.

    Args:
      new_campaign_data: Actual data for creating new campaigns in array form.

    Returns:
      None.
    """

    for row_num, row in enumerate(new_campaign_data):
      result = None
      if (
          len(row) > data_references.NewCampaigns.campaign_start_date
          and row[data_references.NewCampaigns.campaign_upload_status]
          != data_references.RowStatus.uploaded
      ):
        result = self.process_campaign_data_and_create_campaigns(row)
        if result:
          utils.process_operations_and_errors(
              result[_CUSTOMER_ID],
              result[_OPERATIONS],
              result[_ERROR_LOG],
              row_num,
              self.sheet_service,
              self.google_ads_service,
              data_references.SheetNames.new_campaigns,
          )

  def process_campaign_data_and_create_campaigns(
      self, campaign_data: list[str]
  ) -> Mapping[str, tuple[ads_api.BudgetOperation, ads_api.CampaignOperation]]:
    """Creates campaigns via google API based.

    Args:
      campaign_data: List of strings, needed for creating new campaigns.

    Returns:
      Values for Customer Id, Google Ads API Mutate operations or an Error
      Message to write to the sheet. For example:

        {'customer_id': '123456',
         'operations': (ads_api.BudgetOperation, ads_api.CampaignOperation),
         'error_log': 'Target ROAS and CPA should be a number.'}
    """
    customer_id = utils.retrieve_customer_id(
        campaign_data[data_references.NewCampaigns.customer_name],
        self.sheet_service,
    )

    logging.info("Creating Budget API Operation")
    budget_error = None
    budget_operation = None
    try:
      budget_operation = self.create_campaign_budget_operation(
          customer_id,
          campaign_data[data_references.NewCampaigns.campaign_budget],
          campaign_data[data_references.NewCampaigns.budget_delivery_method],
      )
    except ValueError as e:
      budget_error = str(e)

    logging.info("Creating pMax Campaign API Operation")
    campaign_error = None
    campaign_operation = None
    try:
      campaign_operation = self.create_pmax_campaign_operation(
          customer_id,
          campaign_data[data_references.NewCampaigns.campaign_name],
          campaign_data[data_references.NewCampaigns.campaign_status],
          campaign_data[data_references.NewCampaigns.campaign_target_roas],
          campaign_data[data_references.NewCampaigns.campaign_target_cpa],
          campaign_data[data_references.NewCampaigns.bidding_strategy],
          campaign_data[data_references.NewCampaigns.campaign_start_date],
          campaign_data[data_references.NewCampaigns.campaign_end_date],
          campaign_data[data_references.NewCampaigns.eu_political_ads],
      )
    except ValueError as e:
      campaign_error = str(e)

    error_message = "\n".join(x for x in [budget_error, campaign_error] if x)

    result = {
        _CUSTOMER_ID: customer_id,
        _OPERATIONS: (budget_operation, campaign_operation),
        _ERROR_LOG: error_message,
    }

    if error_message:
      result[_OPERATIONS] = None

    return result

  def create_campaign_budget_operation(
      self, customer_id: str, budget: str, budget_delivery_method: str
  ) -> tuple[ads_api.BudgetOperation | None, str]:
    """Set up mutate object for creating campaign and budget for the campaign.

    Args:
      customer_id: Google ads customer id.
      budget: Budget for the campaign.
      budget_delivery_method: The delivery method that determines the rate at
        which the campaign budget is spent. STANDARD or ACCELERATED

    Returns:
       A tuple (ads_api.BudgetOperation, error_message), where
       ads_api.BudgetOperation is a
       Google Ads API MutateOperation for a campaign budget, and error_message
       is a string, containing the optional error message.

    Raises:
      ValueError: In case budget or budget_delivery_method are not in required
          format.
    """
    if not budget.isnumeric():
      raise ValueError("Campaign Budget should be a number.")

    budget = float(budget)

    if budget_delivery_method not in ("STANDARD", "ACCELERATED"):
      raise ValueError(
          "Budget delivery method should be either STANDARD or ACCELERATED."
      )

    mutate_operation = self._google_ads_client.get_type("MutateOperation")
    campaign_budget_operation = mutate_operation.campaign_budget_operation
    campaign_budget = campaign_budget_operation.create
    campaign_budget.name = f"Performance Max campaign budget #{uuid.uuid4()}"
    campaign_budget.amount_micros = budget * 1000000
    campaign_budget.delivery_method = budget_delivery_method
    campaign_budget.explicitly_shared = False

    self.budget_temporary_id -= 1
    campaign_budget.resource_name = self._google_ads_client.get_service(
        "CampaignBudgetService"
    ).campaign_budget_path(customer_id, self.budget_temporary_id)

    return mutate_operation

  def create_pmax_campaign_operation(
      self,
      customer_id: str,
      campaign_name: str,
      campaign_status: str,
      target_roas: str,
      target_cpa: str,
      bidding_strategy: str,
      start_date: str,
      end_date: str,
      eu_political_ads: str,
      brand_guidelines_enabled: bool = False,
  ) -> tuple[ads_api.CampaignOperation | None, str]:
    """Creates a MutateOperation that creates a new Performance Max campaign.

    A temporary ID will be assigned to this campaign so that it can
    be referenced by other objects being created in the same Mutate request.

    Args:
      customer_id: Google ads customer id.
      campaign_name: Name for the campaign.
      campaign_status: ENABLED or PAUSED
      target_roas: The chosen revenue (based on conversion data) per unit of
        spend. Value must be between 0.01 and 1000.0, inclusive.
      target_cpa: Average CPA target. This target should be greater than or
        equal to minimum billable unit based on the currency for the account.
      bidding_strategy: MaximizeConversions or MaximizeConversionValue bidding
        strategy.
      start_date: Start time for the campaign in format 'YYYY-MM-DD'.
      end_date: End time for the campaign in format 'YYYY-MM-DD'.
      eu_political_ads: String value containing self declaration on whether the
        campaign contains EU Political Ads.
      brand_guidelines_enabled: Set if the campaign is enabled for brand guidelines.

    Returns:
      A tuple (ads_api.CampaignOperation, error_message), where
      ads_api.CampaignOperation is a
      Google Ads API MutateOperation for a pmax campaign, and error_message
      is a string, containing the optional error message.

    Raises:
      ValueError: In case Target Roas or Target CPA is not a number.
    """
    mutate_operation = self._google_ads_client.get_type("MutateOperation")
    campaign = mutate_operation.campaign_operation.create
    campaign.name = campaign_name

    if bidding_strategy == "MaximizeConversions":
      if target_cpa.isnumeric():
        campaign.bidding_strategy_type = (
            self._google_ads_client.enums.BiddingStrategyTypeEnum.MAXIMIZE_CONVERSIONS
        )
        campaign.maximize_conversions.target_cpa_micros = (
            float(target_cpa) * 1000000
        )
      else:
        raise ValueError(
            "Target CPA can't be empty for MaximizeConversions bidding"
            " strategy."
        )
    elif bidding_strategy == "MaximizeConversionValue":
      if target_roas.isnumeric():
        campaign.bidding_strategy_type = (
            self._google_ads_client.enums.BiddingStrategyTypeEnum.MAXIMIZE_CONVERSION_VALUE
        )
        campaign.maximize_conversion_value.target_roas = float(target_roas)
      else:
        raise ValueError(
            "Target ROAS can't be empty for MaximizeConversionValue bidding"
            " strategy."
        )
    else:
      raise ValueError(
          "Bidding Stratedy should be either MaximizeConversions or"
          " MaximizeConversionValue."
      )

    match campaign_status:
      case data_references.ApiStatus.paused:
        campaign.status = (
            self._google_ads_client.enums.CampaignStatusEnum.PAUSED
        )
      case data_references.ApiStatus.enabled:
        campaign.status = (
            self._google_ads_client.enums.CampaignStatusEnum.ENABLED
        )

    campaign.advertising_channel_type = (
        self._google_ads_client.enums.AdvertisingChannelTypeEnum.PERFORMANCE_MAX
    )

    campaign.url_expansion_opt_out = False

    self.performance_max_campaign_temporary_id -= 1
    campaign_service = self._google_ads_client.get_service("CampaignService")
    campaign.resource_name = campaign_service.campaign_path(
        customer_id, self.performance_max_campaign_temporary_id
    )

    campaign.campaign_budget = campaign_service.campaign_budget_path(
        customer_id, self.budget_temporary_id
    )

    campaign.start_date = datetime.datetime.strptime(
        start_date, "%Y-%m-%d"
    ).strftime("%Y%m%d")
    campaign.end_date = datetime.datetime.strptime(
        end_date, "%Y-%m-%d"
    ).strftime("%Y%m%d")

    # Declare whether or not this campaign serves political ads targeting the
    # EU.
    match eu_political_ads:
      case data_references.EuPoliticalAds.no:
        campaign.contains_eu_political_advertising = (
            self._google_ads_client.enums.EuPoliticalAdvertisingStatusEnum.DOES_NOT_CONTAIN_EU_POLITICAL_ADVERTISING
        )
      case data_references.EuPoliticalAds.yes:
        campaign.contains_eu_political_advertising = (
            self._google_ads_client.enums.EuPoliticalAdvertisingStatusEnum.CONTAINS_EU_POLITICAL_ADVERTISING
        )

    campaign.brand_guidelines_enabled = brand_guidelines_enabled

    return mutate_operation
