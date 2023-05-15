# Copyright 2019 Google LLC
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
"""Provides functionality to interact with Google Ads platform."""

from google.ads import googleads
from google.api_core import protobuf_helpers
import requests

class AdService():
  """Provides Google ads API service to interact with Ads platform."""

  def __init__(self, ads_account_file):
    """Constructs the AdService instance.

    Args:
      ads_account_file: Path to Google Ads API account file.
    """
    self._google_ads_client = googleads.client.GoogleAdsClient.load_from_storage(
        ads_account_file, version='v13')
    self._cache_ad_group_ad = {}
    self.prev_image_asset_list = None
    self.prev_customer_id = None

  def _get_campaign_by_name(self, campaign_name, customer_id):
      """Gets a campaign by customer id and campaign name.

      Args:
      customer_id: customer id.
      campaign_name: name of the campaign

      Returns:
      Campaign
      """
      query = (
          'SELECT campaign.name, campaign.id, campaign.resource_name '
          'FROM campaign WHERE campaign.name = "' + campaign_name + '"')

      return self._google_ads_client.get_service('GoogleAdsService').search(
          customer_id=customer_id, query=query)

  def _get_campaign_by_id(self, campaign_id, customer_id):
      """Gets a campaign by customer id and campaign name.

      Args:
      customer_id: customer id.
      campaign_id: id of the campaign

      Returns:
      Campaign
      """
      query = (
          'SELECT campaign.name, campaign.id, campaign.resource_name '
          'FROM campaign WHERE campaign.id = "' + campaign_id + '"')

      return self._google_ads_client.get_service('GoogleAdsService').search(
          customer_id=customer_id, query=query)