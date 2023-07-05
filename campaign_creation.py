"""Provides functionality to interact with Google Ads platform."""

from google.ads import googleads
from google.api_core import protobuf_helpers
from PIL import Image
import requests
from io import BytesIO
from datetime import datetime, timedelta
from google.ads.googleads.errors import GoogleAdsException
from datetime import datetime

_BUDGET_TEMPORARY_ID = -100
_PERFORMANCE_MAX_CAMPAIGN_TEMPORARY_ID = -100

class CampaignCreation():
    """Provides Google ads API service to interact with Ads platform."""

    def __init__(self, ads_account_file):
        """Constructs the AdService instance.

        Args:
          ads_account_file: Path to Google Ads API account file.
        """
        self._google_ads_client = googleads.client.GoogleAdsClient.load_from_storage(
            ads_account_file, version='v14')
        self._cache_ad_group_ad = {}
        self.prev_image_asset_list = None
        self.prev_customer_id = None

    # def _create_campaign_budget(self, customer_id):
        

    #     return mutate_operation    
    
    def _create_campaign(self, customer_id, budget, budget_delivery_method, campaign_name, campaign_status, target_roas, bidding_strategy_type, start_time, end_time):
        mutate_operations = []
        global _BUDGET_TEMPORARY_ID
        mutate_operation_budget = self._google_ads_client.get_type("MutateOperation")
        campaign_budget_operation = mutate_operation_budget.campaign_budget_operation
        campaign_budget = campaign_budget_operation.create
        campaign_budget.name = f"Performance Max campaign budget {campaign_name}"

        budget = float(budget)*1000000
        campaign_budget.amount_micros = budget

        
        campaign_budget.delivery_method = (budget_delivery_method)
        # A Performance Max campaign cannot use a shared campaign budget.
        campaign_budget.explicitly_shared = False

        _BUDGET_TEMPORARY_ID -= 1
        # Set a temporary ID in the budget's resource name so it can be referenced
        # by the campaign in later steps.
        campaign_budget.resource_name = self._google_ads_client.get_service("CampaignBudgetService").campaign_budget_path(customer_id, _BUDGET_TEMPORARY_ID)
        mutate_operations.append(mutate_operation_budget)


        global _PERFORMANCE_MAX_CAMPAIGN_TEMPORARY_ID
        mutate_operation = self._google_ads_client.get_type("MutateOperation")
        campaign = mutate_operation.campaign_operation.create
        campaign.name = campaign_name


        if campaign_status == "PAUSED":
            campaign.status = self._google_ads_client.enums.CampaignStatusEnum.PAUSED
        elif campaign_status == "ENABLED":
            campaign.status = self._google_ads_client.enums.CampaignStatusEnum.ENABLED
        #TODO add  to error column     
        
        campaign.advertising_channel_type = (self._google_ads_client.enums.AdvertisingChannelTypeEnum.PERFORMANCE_MAX)

        if bidding_strategy_type == "MaximizeConversions":
            bidding_strategy_type = self._google_ads_client.enums.BiddingStrategyTypeEnum.MAXIMIZE_CONVERSIONS
        elif bidding_strategy_type == "MaximizeConversionValue":
            bidding_strategy_type = self._google_ads_client.enums.BiddingStrategyTypeEnum.MAXIMIZE_CONVERSION_VALUE
        #TODO add  to error column   

        campaign.bidding_strategy_type = (self._google_ads_client.enums.BiddingStrategyTypeEnum.MAXIMIZE_CONVERSIONS)
        campaign.maximize_conversion_value.target_roas = float(target_roas)

        campaign.url_expansion_opt_out = False
        _PERFORMANCE_MAX_CAMPAIGN_TEMPORARY_ID= -1

        campaign_service = self._google_ads_client.get_service("CampaignService")
        campaign.resource_name = campaign_service.campaign_path(customer_id, _PERFORMANCE_MAX_CAMPAIGN_TEMPORARY_ID)

        campaign.campaign_budget = campaign_service.campaign_budget_path(customer_id, _BUDGET_TEMPORARY_ID)

        campaign.start_date = datetime.strptime(start_time, "%Y-%m-%d").strftime("%Y%m%d")
        campaign.end_date = datetime.strptime(end_time, "%Y-%m-%d").strftime("%Y%m%d")
        mutate_operations.append(mutate_operation)

        googleads_service = self._google_ads_client.get_service(
            "GoogleAdsService")
        request = self._google_ads_client.get_type("MutateGoogleAdsRequest")
        request.customer_id = customer_id
        request.mutate_operations = mutate_operations
        
        try:
            response = googleads_service.mutate(
                request=request
            )
        except GoogleAdsException as ex:
            error_message = f'Request with ID "{ex.request_id}" failed and includes the following errors:'
            for error in ex.failure.errors:
                if error.message != "Resource was not found.":
                    error_message = error_message + f'\n\tError message: "{error.message}".'
            print(error_message)

        