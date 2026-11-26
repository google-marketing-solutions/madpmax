# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for campaign_creation.

The operations are built with a real Google Ads API client for the version the
Cloud Function uses, so a field that doesn't exist in that version fails here
instead of in production. No request is sent.
"""

import unittest
from unittest import mock

import campaign_creation
import data_references
from google.ads.googleads import client
from google.auth import credentials
import main

_CUSTOMER_ID = "1234567890"


def _make_ads_client() -> client.GoogleAdsClient:
  """Returns an offline Google Ads API client for the function's version."""
  return client.GoogleAdsClient(
      credentials=credentials.AnonymousCredentials(),
      version=main._API_VERSIONAPI_VERSION,  # pylint: disable=protected-access
      use_proto_plus=True,
  )


class CampaignServiceTest(unittest.TestCase):

  def setUp(self):
    super().setUp()
    self.campaign_service = campaign_creation.CampaignService(
        mock.Mock(), mock.Mock(), _make_ads_client()
    )

  def _create_campaign(self, **overrides):
    """Builds a campaign operation with valid defaults and returns the campaign.

    Args:
      **overrides: Arguments to override in create_pmax_campaign_operation.
    """
    arguments = {
        "customer_id": _CUSTOMER_ID,
        "campaign_name": "Test campaign",
        "campaign_status": data_references.ApiStatus.paused,
        "target_roas": "",
        "target_cpa": "5",
        "bidding_strategy": "MaximizeConversions",
        "start_date": "2026-12-01",
        "end_date": "2026-12-31",
        "eu_political_ads": data_references.EuPoliticalAds.no,
    }
    arguments.update(overrides)
    operation = self.campaign_service.create_pmax_campaign_operation(
        **arguments
    )
    return operation.campaign_operation.create

  def test_sets_start_and_end_date_time_for_whole_days(self):
    campaign = self._create_campaign()

    self.assertEqual(campaign.start_date_time, "2026-12-01 00:00:00")
    self.assertEqual(campaign.end_date_time, "2026-12-31 23:59:59")

  def test_keeps_the_default_final_url_expansion(self):
    campaign = self._create_campaign()

    self.assertFalse(campaign.asset_automation_settings)

  def test_sets_target_cpa_for_maximize_conversions(self):
    campaign = self._create_campaign(target_cpa="5")

    self.assertEqual(campaign.maximize_conversions.target_cpa_micros, 5_000_000)

  def test_sets_target_roas_for_maximize_conversion_value(self):
    campaign = self._create_campaign(
        bidding_strategy="MaximizeConversionValue",
        target_roas="3",
        target_cpa="",
    )

    self.assertEqual(campaign.maximize_conversion_value.target_roas, 3.0)

  def test_rejects_empty_target_cpa_for_maximize_conversions(self):
    with self.assertRaisesRegex(ValueError, "Target CPA can't be empty"):
      self._create_campaign(target_cpa="")

  def test_creates_a_paused_performance_max_campaign(self):
    campaign = self._create_campaign()

    self.assertEqual(campaign.status.name, data_references.ApiStatus.paused)
    self.assertEqual(campaign.advertising_channel_type.name, "PERFORMANCE_MAX")

  def test_budget_operation_sets_amount_in_micros(self):
    operation = self.campaign_service.create_campaign_budget_operation(
        _CUSTOMER_ID, "10", "STANDARD"
    )

    budget = operation.campaign_budget_operation.create
    self.assertEqual(budget.amount_micros, 10_000_000)
    self.assertEqual(budget.delivery_method.name, "STANDARD")

  def test_budget_operation_rejects_a_non_numeric_budget(self):
    with self.assertRaisesRegex(ValueError, "should be a number"):
      self.campaign_service.create_campaign_budget_operation(
          _CUSTOMER_ID, "ten", "STANDARD"
      )


if __name__ == "__main__":
  unittest.main()
