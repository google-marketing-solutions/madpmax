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
from enums.new_campaigns_column_map import newCampaignsColumnMap


class CampaignService:
  """Class for Campaign Creation.

  Contains all methods to create pMax Campaings in Google Ads.
  """

  def __init__(self, google_ads_service, sheet_service, google_ads_client):
    """Constructs the CampaignService instance.

    Args:
      google_ads_service: instance of the google_ads_service for dependancy
        injection.
      sheet_service: instance of sheet_service for dependancy injection.
      google_ads_client: Instance of Google Ads API client.
    """
    self._google_ads_client = google_ads_client
    self.google_ads_service = google_ads_service
    self.sheet_service = sheet_service
    self._cache_ad_group_ad = {}
    self.prev_image_asset_list = None
    self.prev_customer_id = None
    self.budget_temporary_id = -2000
    self.performance_max_campaign_temporary_id = -100

  def _create_campaign(
      self,
      customer_id,
      budget,
      budget_delivery_method,
      campaign_name,
      campaign_status,
      target_roas,
      target_cpa,
      bidding_strategy_type,
      start_time,
      end_time,
  ):
    """Set up mutate object for creating campaign and budget for the campaign.

    Args:
      customer_id: Google ads customer id.
      budget: Budget for the campaign.
      budget_delivery_method: The delivery method that determines the rate at
        which the campaign budget is spent. STANDARD or ACCELERATED
      campaign_name: Name for the campaign.
      campaign_status: ENABLED or PAUSED
      target_roas: The chosen revenue (based on conversion data) per unit of
        spend. Value must be between 0.01 and 1000.0, inclusive.
      target_cpa: Average CPA target. This target should be greater than or
        equal to minimum billable unit based on the currency for the account.
      bidding_strategy_type: MaximizeConversions or MaximizeConversionValue
        bidding strategy.
      start_time: Start time for the campaign in format 'YYYY-MM-DD'.
      end_time: End time for the campaign in format 'YYYY-MM-DD'.

    Returns:
      mutate_operations, error_message
    """
    error_message = None
    mutate_operations = []

    mutate_operation_budget = self._google_ads_client.get_type(
        "MutateOperation"
    )
    campaign_budget_operation = (
        mutate_operation_budget.campaign_budget_operation
    )
    campaign_budget = campaign_budget_operation.create
    campaign_budget.name = f"Performance Max campaign budget {campaign_name}"

    if not budget:
      return None, "Budget can't be empty."

    try:
      budget = float(budget)
    except ValueError:
      return None, "Budget should be a number."

    budget = budget * 1000000
    campaign_budget.amount_micros = budget

    campaign_budget.delivery_method = budget_delivery_method
    # A Performance Max campaign cannot use a shared campaign budget.
    campaign_budget.explicitly_shared = False

    self.budget_temporary_id -= 1
    # Set a temporary ID in the budget's resource name so it can be referenced
    # by the campaign in later steps.
    campaign_budget.resource_name = self._google_ads_client.get_service(
        "CampaignBudgetService"
    ).campaign_budget_path(customer_id, self.budget_temporary_id)
    mutate_operations.append(mutate_operation_budget)

    mutate_operation = self._google_ads_client.get_type("MutateOperation")
    campaign = mutate_operation.campaign_operation.create
    campaign.name = campaign_name

    match campaign_status:
      case "PAUSED":
        campaign.status = (
            self._google_ads_client.enums.CampaignStatusEnum.PAUSED
        )
      case "ENABLED":
        campaign.status = (
            self._google_ads_client.enums.CampaignStatusEnum.ENABLED
        )

    campaign.advertising_channel_type = (
        self._google_ads_client.enums.AdvertisingChannelTypeEnum.PERFORMANCE_MAX
    )

    try:
      match bidding_strategy_type:
        case "MaximizeConversions":
          if not target_cpa:
            return (
                None,
                """Target CPA can't be empty for MaximizeConversions bidding strategy.""",
            )

          campaign.bidding_strategy_type = (
              self._google_ads_client.enums.BiddingStrategyTypeEnum.MAXIMIZE_CONVERSIONS
          )
          campaign.maximize_conversions.target_cpa_micros = (
              float(target_cpa) * 1000000
          )

        case "MaximizeConversionValue":
          if not target_roas:
            return (
                None,
                """Target ROAS can't be empty for MaximizeConversionValue bidding strategy.""",
            )

          campaign.bidding_strategy_type = (
              self._google_ads_client.enums.BiddingStrategyTypeEnum.MAXIMIZE_CONVERSION_VALUE
          )
          campaign.maximize_conversion_value.target_roas = float(target_roas)
        case _:
          return None, """Not valid bidding strategy."""
    except ValueError:
      return None, """Target ROAS and CPA should be a number."""

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
        start_time, "%Y-%m-%d"
    ).strftime("%Y%m%d")
    campaign.end_date = datetime.datetime.strptime(
        end_time, "%Y-%m-%d"
    ).strftime("%Y%m%d")
    mutate_operations.append(mutate_operation)

    return mutate_operations, error_message

  def process_campaign_data_and_create_campaigns(
      self, campaign_data, login_customer_id
  ):
    """Creates campaigns via google API based.

    Args:
      campaign_data: Actual data for creating new campaigns in array form.
      login_customer_id: Google ads customer id.
    """
    results = self.google_ads_service.retrieve_all_customers(login_customer_id)

    customer_mapping = {}
    for row in results:
      customer_mapping[row.customer_client.descriptive_name] = str(
          row.customer_client.id
      )

    if len(customer_mapping) > 0:
      for campaign in campaign_data:
        # Check if required columns are included in row.
        if len(campaign) > newCampaignsColumnMap.CUSTOMER_START_DATE:
          mutate_campaign_operation = None
          campaign_name = campaign[newCampaignsColumnMap.CAMPAIGN_NAME]
          campaign_status = campaign[newCampaignsColumnMap.CAMPAIGN_STATUS]
          campaign_upload_status = campaign[
              newCampaignsColumnMap.CAMPAIGN_UPLOAD_STATUS
          ]
          bidding_strategy = campaign[newCampaignsColumnMap.BIDDING_STRATEGY]
          campaign_target_roas = campaign[
              newCampaignsColumnMap.CAMPAIGN_TARGET_ROAS
          ]
          campaign_target_cpa = campaign[
              newCampaignsColumnMap.CAMPAIGN_TARGET_CPA
          ]
          campaign_budget = campaign[newCampaignsColumnMap.CAMPAIGN_BUDGET]
          campaign_customer_name = campaign[newCampaignsColumnMap.CUSTOMER_NAME]
          campaign_customer_id = customer_mapping[campaign_customer_name]
          campaign_start_date = campaign[
              newCampaignsColumnMap.CUSTOMER_START_DATE
          ]
          campaign_end_date = campaign[newCampaignsColumnMap.CUSTOMER_END_DATE]
          budget_delivery_method = campaign[
              newCampaignsColumnMap.BUDGET_DELIVERY_METHOD
          ]
          row_number = self.sheet_service.get_row_number_by_value(
              [campaign[newCampaignsColumnMap.CUSTOMER_NAME], campaign_name],
              campaign_data,
              newCampaignsColumnMap.CUSTOMER_NAME,
          )

          campaign_sheetlist = [
              campaign_customer_name,
              campaign_customer_id,
              campaign_name,
          ]

          sheet_id = self.sheet_service.get_sheet_id("NewCampaigns")

          if campaign_upload_status != "UPLOADED":
            mutate_campaign_operation, error_message = self._create_campaign(
                campaign_customer_id,
                campaign_budget,
                budget_delivery_method,
                campaign_name,
                campaign_status,
                campaign_target_roas,
                campaign_target_cpa,
                bidding_strategy,
                campaign_start_date,
                campaign_end_date,
            )

            if error_message:
              self.sheet_service.variable_update_sheet_status(
                  row_number,
                  sheet_id,
                  newCampaignsColumnMap.CAMPAIGN_UPLOAD_STATUS,
                  "ERROR",
                  error_message,
                  newCampaignsColumnMap.ERROR_MESSAGE,
              )
            else:
              campaigns_response, campaigns_error_message = (
                  self.google_ads_service.bulk_mutate(
                      "Campaigns",
                      mutate_campaign_operation,
                      campaign_customer_id,
                  )
              )

              if campaigns_response:
                self.sheet_service.variable_update_sheet_status(
                    row_number,
                    sheet_id,
                    newCampaignsColumnMap.CAMPAIGN_UPLOAD_STATUS,
                    "UPLOADED",
                )

                campaign_sheetlist.append(
                    campaigns_response.mutate_operation_responses[
                        1
                    ].campaign_result.resource_name.split("/")[-1]
                )
                self.sheet_service.add_new_campaign_to_list_sheet(
                    campaign_sheetlist
                )

              if campaigns_error_message:
                print(campaigns_error_message)
                self.sheet_service.variable_update_sheet_status(
                    row_number,
                    sheet_id,
                    newCampaignsColumnMap.CAMPAIGN_UPLOAD_STATUS,
                    "ERROR",
                    campaigns_error_message,
                    newCampaignsColumnMap.ERROR_MESSAGE,
                )
