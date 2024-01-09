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
"""Provides functionality to create asset groups."""

from enums.new_asset_groups_column_map import newAssetGroupsColumnMap


class AssetGroupService:
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
    self.asset_group_temp_id = -1000

  def create_asset_group(self, asset_group_details, campaign_id, customer_id):
    """Creates a list of MutateOperations that create a new asset_group.

    A temporary ID will be assigned to this asset group so that it can
    be referenced by other objects being created in the same Mutate request.

    Args:
      asset_group_details: A list of values required to setup an asset group
        in Google ads.
      campaign_id: a pmax campaign ID.
      customer_id: a client customer ID.

    Returns:
      MutateOperation that create a new asset group.
    """
    asset_group_id = self.asset_group_temp_id
    self.asset_group_temp_id -= 1

    if len(asset_group_details) <= newAssetGroupsColumnMap.MOBILE_URL:
      return None, None

    asset_group_service = self._google_ads_client.get_service(
        "AssetGroupService"
    )
    campaign_service = self._google_ads_client.get_service(
        "CampaignService")

    # Create the AssetGroup
    mutate_operation = self._google_ads_client.get_type("MutateOperation")
    asset_group = mutate_operation.asset_group_operation.create
    asset_group.name = asset_group_details[
        newAssetGroupsColumnMap.ASSET_GROUP_NAME
    ]
    asset_group.campaign = campaign_service.campaign_path(
        customer_id, campaign_id
    )
    asset_group.final_urls.append(
        asset_group_details[newAssetGroupsColumnMap.FINAL_URL]
    )
    asset_group.final_mobile_urls.append(
        asset_group_details[newAssetGroupsColumnMap.MOBILE_URL]
    )
    asset_group.status = self._google_ads_client.enums.AssetGroupStatusEnum[
        asset_group_details[newAssetGroupsColumnMap.ASSET_GROUP_STATUS]
    ]
    if len(asset_group_details) > newAssetGroupsColumnMap.PATH1:
      asset_group.path1 = asset_group_details[newAssetGroupsColumnMap.PATH1]

    if len(asset_group_details) > newAssetGroupsColumnMap.PATH2:
      asset_group.path2 = asset_group_details[newAssetGroupsColumnMap.PATH2]

    asset_group.resource_name = asset_group_service.asset_group_path(
        customer_id,
        asset_group_id,
    )

    return mutate_operation, asset_group_id
