"""Provides functionality to create campaigns."""

from datetime import datetime
from datetime import datetime
from enums.new_campaigns_column_map import newCampaignsColumnMap


class CampaignService:

  def __init__(self, google_ads_service, sheet_service, google_ads_client):
    """Constructs the CampaignService instance.

    Args:
      ads_account_file: Path to Google Ads API account file.
      google_ads_service: instance of the google_ads_service for dependancy
        injection.
      sheet_service: instance of sheet_service for dependancy injection.
    """
    self._google_ads_client = google_ads_client
    self._cache_ad_group_ad = {}
    self.prev_image_asset_list = None
    self.prev_customer_id = None
    self.budget_temporary_id = -2000
    self.performance_max_campaign_temporary_id = -100
    self.google_ads_service = google_ads_service
    self.sheet_service = sheet_service

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
      end_time
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
    """
    mutate_operations = []
    mutate_operation_budget = self._google_ads_client.get_type(
        "MutateOperation"
    )
    campaign_budget_operation = (
        mutate_operation_budget.campaign_budget_operation
    )
    campaign_budget = campaign_budget_operation.create
    campaign_budget.name = f"Performance Max campaign budget {campaign_name}"

    budget = float(budget) * 1000000
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

    if campaign_status == "PAUSED":
      campaign.status = self._google_ads_client.enums.CampaignStatusEnum.PAUSED
    elif campaign_status == "ENABLED":
      campaign.status = self._google_ads_client.enums.CampaignStatusEnum.ENABLED

    campaign.advertising_channel_type = (
        self._google_ads_client.enums.AdvertisingChannelTypeEnum.PERFORMANCE_MAX
    )

    if bidding_strategy_type == "MaximizeConversions":
      campaign.bidding_strategy_type = (
          self._google_ads_client.enums.BiddingStrategyTypeEnum.MAXIMIZE_CONVERSIONS
      )
      campaign.maximize_conversions.target_cpa_micros = (
          float(target_cpa) * 1000000
      )
    elif bidding_strategy_type == "MaximizeConversionValue":
      campaign.bidding_strategy_type = (
          self._google_ads_client.enums.BiddingStrategyTypeEnum.MAXIMIZE_CONVERSION_VALUE
      )
      campaign.maximize_conversion_value.target_roas = float(target_roas)

    campaign.url_expansion_opt_out = False
    self.performance_max_campaign_temporary_id -= 1

    campaign_service = self._google_ads_client.get_service("CampaignService")
    campaign.resource_name = campaign_service.campaign_path(
        customer_id, self.performance_max_campaign_temporary_id
    )

    campaign.campaign_budget = campaign_service.campaign_budget_path(
        customer_id, self.budget_temporary_id
    )

    campaign.start_date = datetime.strptime(start_time, "%Y-%m-%d").strftime(
        "%Y%m%d"
    )
    campaign.end_date = datetime.strptime(end_time, "%Y-%m-%d").strftime(
        "%Y%m%d"
    )
    mutate_operations.append(mutate_operation)

    return mutate_operations

  def process_campaign_data_and_create_campaigns(
      self, campaign_data, google_spread_sheet_id, google_customer_id
  ):
    """Creates campaigns via google API based on data provided and update the spreadsheet with the result or an error.

    Args:
      campaign_data: Actual data for creating new campaigns in array form.
      google_spread_sheet_id: Id of the sheet for updating the status.
      google_customer_id: Google ads customer id.
    """
    for campaign in campaign_data:
      mutate_campaign_operation = None
      campaign_name = campaign[newCampaignsColumnMap.CAMPAIGN_NAME]
      campaign_status = campaign[newCampaignsColumnMap.CAMPAIGN_STATUS]
      bidding_strategy = campaign[newCampaignsColumnMap.BIDDING_STRATEGY]
      campaign_target_roas = campaign[
          newCampaignsColumnMap.CAMPAIGN_TARGET_ROAS
      ]
      campaign_target_cpa = campaign[
          newCampaignsColumnMap.CAMPAIGN_TARGET_CPA
      ]
      campaign_budget = campaign[newCampaignsColumnMap.CAMPAIGN_BUDGET]
      campaign_customer_id = campaign[newCampaignsColumnMap.CUSTOMER_ID]
      campaign_start_date = campaign[
          newCampaignsColumnMap.CUSTOMER_START_DATE
      ]
      campaign_end_date = campaign[newCampaignsColumnMap.CUSTOMER_END_DATE]
      budget_delivery_method = campaign[
          newCampaignsColumnMap.BUDGET_DELIVERY_METHOD
      ]

      if campaign_status != "UPLOADED":
        mutate_campaign_operation = self._create_campaign(
            campaign_customer_id,
            campaign_budget,
            budget_delivery_method,
            campaign_name,
            campaign_status,
            campaign_target_roas,
            campaign_target_cpa,
            bidding_strategy,
            campaign_start_date,
            campaign_end_date
        )

        campaigns_response, campaigns_error_message = (
            self.google_ads_service._bulk_mutate(
                "Campaigns", mutate_campaign_operation, google_customer_id
            )
        )
        row_number = self.sheet_service.get_row_number_by_value(
            campaign_name,
            campaign_data,
            newCampaignsColumnMap.CAMPAIGN_NAME
        )

        sheet_id = self.sheet_service.get_sheet_id(
            "NewCampaigns", google_spread_sheet_id
        )

        if campaigns_response:
          self.sheet_service.variable_update_sheet_status(
              row_number,
              sheet_id,
              google_spread_sheet_id,
              newCampaignsColumnMap.CAMPAIGN_UPLOAD_STATUS,
              "UPLOADED"
          )

        if campaigns_error_message:
          self.sheet_service.variable_update_sheet_status(
              row_number,
              sheet_id,
              google_spread_sheet_id,
              newCampaignsColumnMap.CAMPAIGN_UPLOAD_STATUS,
              "ERROR",
              campaigns_error_message,
              newCampaignsColumnMap.ERROR_MESSAGE
          )