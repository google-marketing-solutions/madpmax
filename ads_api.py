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

    def _get_campaign_resource_name(self, customer_id, campaign_id):
        """Gets a campaign by customer id and campaign id.

        Args:
        customer_id: customer id.
        campaign_id: id of the campaign

        Returns:
        Campaign resource.
        """
        campaign_service = self._google_ads_client.get_service(
            "CampaignService")

        # Create campaign operation.
        return campaign_service.campaign_path(
            customer_id, campaign_id
        )

    def _get_asset_group_resource_name(self, customer_id, asset_group_id):
        """Generates the Ad group resource name based on input.

        Args:
        customer_id: customer id.
        asset_group_id: id of the ad group

        Returns:
        Asset group resource.
        """
        asset_group_service = self._google_ads_client.get_service(
            "AssetGroupService")

        # Create ad group operation.
        return asset_group_service.asset_group_path(
            customer_id, asset_group_id
        )
    # Creates image asset without linking
    def _create_image_asset(self, image_url, type, name):
        """Generates the image asset and returns the resource name.

        Args:
        image_url: full url of the image file.
        customer_id: customer id.

        Returns:
        Asset resource.
        """
        # Download image from URL
        image_content = requests.get(image_url).content

        #TODO analyse type of the image

        # Create and link the Marketing Image Asset.
        asset_operation = self._google_ads_client.get_type("AssetOperation")
        asset = asset_operation.create
        asset.name = name
        asset.type = type 
        asset.image_asset.full_size.url = image_url
        asset.image_asset.data = image_content

        return asset_operation
    
    # previous version of image creation includes using API
    # def _create_image_asset(self, image_url, customer_id, type, ):
    #     """Generates the image asset and returns the resource name.

    #     Args:
    #     image_url: full url of the image file.
    #     customer_id: customer id.

    #     Returns:
    #     Asset resource.
    #     """
    #     # Download image from URL
    #     image_content = requests.get(image_url).content

    #     #TODO analyse type of the image

    #     # Create and link the Marketing Image Asset.
    #     asset_service = self._google_ads_client.get_service("AssetService")
    #     asset_operation = self._google_ads_client.get_type("AssetOperation")
    #     asset = asset_operation.create
    #     asset.name = "Marketing Image #{uuid4()}"
    #     asset.type = self._google_ads_client.enums.AssetTypeEnum.IMAGE
    #     asset.image_asset.full_size.url = image_url
    #     asset.image_asset.data = image_content

    #     mutate_asset_response = asset_service.mutate_assets(
    #         customer_id=customer_id, operations=[asset_operation]
    #     )

    #     return mutate_asset_response.results[0].resource_name
    
    def _create_video_asset(self, image_url, customer_id):
        """Generates the video asset and returns the resource name.

        Args:
        image_url: full url of the image file.
        customer_id: customer id.

        Returns:
        Asset resource.
        """
        # Download image from URL
        image_content = requests.get(image_url).content

        # Create and link the Marketing Image Asset.
        asset_service = self._google_ads_client.get_service("AssetService")
        asset_operation = self._google_ads_client.get_type("AssetOperation")
        asset = asset_operation.create
        asset.name = "Marketing Image #{uuid4()}"
        asset.type = self._google_ads_client.enums.AssetTypeEnum.IMAGE
        asset.image_asset.full_size.url = image_url
        asset.image_asset.data = image_content

        mutate_asset_response = asset_service.mutate_assets(
            customer_id=customer_id, operations=[asset_operation]
        )

        return mutate_asset_response.results[0].resource_name

    def _add_asset_to_asset_group(self, asset_group, customer_id, operations):
        """Adds the asset resource to an asset group.

        Args:
        asset_group_resource: resource name of the asset group.
        image_url: full url of the image file.
        customer_id: customer id.
        """
        asset_group_asset_service = self._google_ads_client.get_service("AssetGroupAssetService")
        #asset_group_asset_operation = self._google_ads_client.get_type("AssetGroupAssetOperation")

        # asset_resource = self._create_image_asset(image_url, customer_id)
        asset_group_asset = operations

        asset_group_asset.asset_group = asset_group
        #asset_group_asset.asset = asset_resource
        #asset_group_asset.field_type = self._google_ads_client.enums.AssetFieldTypeEnum.MARKETING_IMAGE

        mutate_asset_group_response = asset_group_asset_service.mutate_asset_group_assets(
            customer_id=customer_id, operations=[operations]
        )
        
        return mutate_asset_group_response.results


  