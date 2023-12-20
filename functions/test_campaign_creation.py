from datetime import datetime, timedelta
import unittest
from unittest.mock import MagicMock
from unittest.mock import Mock
from campaign_creation import CampaignService


class TestCampaignCreation(unittest.TestCase):

  def setUp(self):
    # Set up mock dependencies
    self.google_ads_service = MagicMock()
    self.sheet_service = MagicMock()
    self.google_ads_client = Mock()
    # Mocking the return value for BiddingStrategyTypeEnum
    self.google_ads_client.enums.BiddingStrategyTypeEnum.MAXIMIZE_CONVERSION_VALUE = (
        "MaximizeConversionValue"
    )
    self.google_ads_client.enums.BiddingStrategyTypeEnum.MAXIMIZE_CONVERSIONS = (
        "MaximizeConversions"
    )
    # Initialize CampaignService with mocked dependencies
    self.campaign_service = CampaignService(
        self.google_ads_service, self.sheet_service, self.google_ads_client
    )

  def test_create_campaign_when_data_is_valid(self):
    customer_id = "customer_id_1"
    budget = 10
    budget_delivery_method = "STANDARD"
    campaign_name = "Test Campaign"
    campaign_status = "ENABLED"
    target_roas = 2.5
    target_cpa = 50
    bidding_strategy_type = "MaximizeConversions"
    today = datetime.today()
    in_a_week = today + timedelta(days=7)
    start_time = today.strftime("%Y-%m-%d")
    end_time = in_a_week.strftime("%Y-%m-%d")
    mutate_operations, error_message = self.campaign_service._create_campaign(
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
    )
    self.assertIsNotNone(mutate_operations)
    self.assertIsNone(error_message)
    self.assertEqual(len(mutate_operations), 2)
    self.assertEqual(
        mutate_operations[0].campaign_budget_operation.create.delivery_method,
        budget_delivery_method,
    )
    self.assertEqual(
        mutate_operations[0].campaign_budget_operation.create.amount_micros,
        10000000,
    )
    self.assertEqual(
        mutate_operations[1].campaign_operation.create.bidding_strategy_type,
        "MaximizeConversions",
    )
    self.assertEqual(
        mutate_operations[
            1
        ].campaign_operation.create.maximize_conversions.target_cpa_micros,
        50000000,
    )

  def test_throw_error_when_no_target_cpa_for_maximize_conversions(self):
    customer_id = "customer_id_2"
    budget = 10
    budget_delivery_method = "STANDARD"
    campaign_name = "Test Campaign With Error"
    campaign_status = "ENABLED"
    target_roas = 3.5
    target_cpa = None
    bidding_strategy_type = "MaximizeConversions"
    today = datetime.today()
    in_a_week = today + timedelta(days=7)
    start_time = today.strftime("%Y-%m-%d")
    end_time = in_a_week.strftime("%Y-%m-%d")
    mutate_operations, error_message = self.campaign_service._create_campaign(
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
    )
    self.assertEqual(
        error_message,
        "Target CPA can't be empty for MaximizeConversions bidding strategy.",
    )
    self.assertIsNone(mutate_operations)

  def test_throw_error_when_no_target_roas_for_maximize_conversion_value(self):
    customer_id = "customer_id_1"
    budget = 10
    budget_delivery_method = "STANDARD"
    campaign_name = "Test Campaign With Error"
    campaign_status = "ENABLED"
    target_roas = None
    target_cpa = 2
    bidding_strategy_type = "MaximizeConversionValue"
    today = datetime.today()
    in_a_week = today + timedelta(days=7)
    start_time = today.strftime("%Y-%m-%d")
    end_time = in_a_week.strftime("%Y-%m-%d")
    mutate_operations, error_message = self.campaign_service._create_campaign(
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
    )
    self.assertEqual(
        error_message,
        "Target ROAS can't be empty for MaximizeConversionValue bidding"
        " strategy.",
    )
    self.assertIsNone(mutate_operations)

  def test_throw_error_when_no_target_roas_in_string(self):
    customer_id = "customer_id_1"
    budget = 10
    budget_delivery_method = "STANDARD"
    campaign_name = "Test Campaign With Error"
    campaign_status = "ENABLED"
    target_roas = "abc"
    target_cpa = 9
    bidding_strategy_type = "MaximizeConversionValue"
    today = datetime.today()
    in_a_week = today + timedelta(days=7)
    start_time = today.strftime("%Y-%m-%d")
    end_time = in_a_week.strftime("%Y-%m-%d")
    mutate_operations, error_message = self.campaign_service._create_campaign(
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
    )
    self.assertEqual(
        error_message,
        "Target ROAS and CPA should be a number.",
    )
    self.assertIsNone(mutate_operations)
