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
"""Provides functionality to interact with Google Ads platform."""

from google.ads import googleads
from google.api_core import protobuf_helpers
from PIL import Image
import requests
from io import BytesIO

_ASSET_TEMP_ID = -100


class AdService():
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

    def _create_image_asset(self, image_url, name, type, customer_id):
        """Generates the image asset and returns the resource name.

        Args:
        image_url: full url of the image file.
        name: the name of the image asset.
        type: The asset type for the image asset.
        customer_id: customer id.

        Returns:
        Asset operation, resource name or None.
        """
        global _ASSET_TEMP_ID

        # Download image from URL and determine the ratio.
        image_content = requests.get(image_url).content
        img = Image.open(BytesIO(image_content))
        img_ratio = img.width / img.height

        if img_ratio == 1 and type == "IMAGE":
            field_type = "SQUARE_MARKETING_IMAGE"
        elif img_ratio < 1 and type == "IMAGE":
            field_type = "PORTRAIT_MARKETING_IMAGE"
        elif img_ratio > 1 and type == "IMAGE":
            field_type = "MARKETING_IMAGE"
        elif img_ratio == 1 and type == "LOGO":
            field_type = "LOGO"
        elif img_ratio > 1 and type == "LOGO":
            field_type = "LANDSCAPE_LOGO"
        else:
            #TODO: Add return for error message (not supported image size / field_type.)
            field_type = None

        asset_service = self._google_ads_client.get_service("AssetService")
        resource_name = asset_service.asset_path(customer_id, _ASSET_TEMP_ID)

        _ASSET_TEMP_ID -= 1

        if image_content:
            # Create and link the Marketing Image Asset.
            asset_operation = self._google_ads_client.get_type(
                "MutateOperation")
            asset = asset_operation.asset_operation.create
            asset.name = name
            asset.type = self._google_ads_client.enums.AssetTypeEnum.IMAGE
            asset.resource_name = resource_name
            asset.image_asset.full_size.url = image_url
            asset.image_asset.data = image_content

            return asset_operation, resource_name, field_type

        return None

    def _create_video_asset(self, video_url, field_type, customer_id):
        """Generates the image asset and returns the resource name.

        Args:
        video_url: full url of the image file.
        field_type: Google Ads field type, required for assigning asset to asset group.
        customer_id: customer id.

        Returns:
        Asset operation, resource name or None.
        """
        global _ASSET_TEMP_ID

        youtube_id = _retrieve_yt_id(video_url)

        asset_service = self._google_ads_client.get_service("AssetService")
        resource_name = asset_service.asset_path(customer_id, _ASSET_TEMP_ID)

        _ASSET_TEMP_ID -= 1

        if youtube_id:
            # Create and link the Marketing Image Asset.
            asset_operation = self._google_ads_client.get_type(
                "MutateOperation")
            asset = asset_operation.asset_operation.create
            asset.resource_name = resource_name
            asset.youtube_video_asset.youtube_video_title = "Marketing Video #{uuid4()}"
            asset.youtube_video_asset.youtube_video_id = youtube_id

            return asset_operation, resource_name, field_type

        return None

    def _retrieve_yt_id(self, video_url):
        """Retrieves the YouTube video id from the URL.

        Args:
        video_url: full url of the video on YT.

        Returns:
        String value containing the id, or None.
        """
        regex = "^.*(youtu\.be\/|v\/|u\/\w\/|embed\/|shorts\/|watch\?v=|\&v=)([^#\&\?]*).*"
        result = re.search(regex, video_url)
        if result:
            return result.group(2)

        return None

    def _create_text_asset(self, text, field_type, customer_id):
        """Generates the image asset and returns the resource name.

        Args:
        video_url: full url of the image file.
        field_type: Google Ads field type, required for assigning asset to asset group.
        customer_id: customer id.

        Returns:
        Asset operation, resource name or None.
        """
        global _ASSET_TEMP_ID

        asset_service = self._google_ads_client.get_service("AssetService")
        resource_name = asset_service.asset_path(customer_id, _ASSET_TEMP_ID)

        _ASSET_TEMP_ID -= 1

        # Create and link the Marketing Image Asset.
        asset_operation = self._google_ads_client.get_type("MutateOperation")
        asset = asset_operation.asset_operation.create
        asset.resource_name = resource_name
        asset.text_asset.text = text
        asset.field_type = field_type

        return asset_operation, resource_name, field_type
    
    def _create_call_to_action_asset(self, action_selection, customer_id):
        """Generates the image asset and returns the resource name.

        Args:
        action_selection: selection from call to action ENUM
        customer_id: customer id.

        Returns:
        Asset operation, resource name or None.
        """
        global _ASSET_TEMP_ID

        asset_service = self._google_ads_client.get_service("AssetService")
        resource_name = asset_service.asset_path(customer_id, _ASSET_TEMP_ID)
        field_type = "CALL_TO_ACTION_SELECTION"

        _ASSET_TEMP_ID -= 1

        asset_operation = self._google_ads_client.get_type("MutateOperation")
        asset = asset_operation.asset_operation.create
        asset.resource_name = resource_name
        asset.call_to_action_type = action_selection
        asset.field_type = field_type

        return asset_operation, resource_name, field_type

    def _add_asset_to_asset_group(self, asset_resource, asset_group_id, field_type, customer_id):
        """Adds the asset resource to an asset group.

        Args:
        asset_resource: resource name of the asset group.
        image_url: full url of the image file.
        field_type: Google Ads field type, required for assigning asset to asset group.
        customer_id: customer id.
        """
        asset_group_service = self._google_ads_client.get_service("AssetGroupService")
        
        asset_group_asset_operation = self._google_ads_client.get_type("MutateOperation")
        asset_group_asset = asset_group_asset_operation.asset_group_asset_operation.create

        asset_group_asset.field_type = field_type
        asset_group_asset.asset_group = asset_group_service.asset_group_path(
            customer_id, asset_group_id,
        )
        asset_group_asset.asset = asset_resource

        return asset_group_asset_operation

    def _bulk_mutate(self, mutate_operations, customer_id):
        """Process Bulk Mutate operation via Google Ads API.
        
        Args:
        mutate_operations: Array of mutate operations.
        customer_id: customer id.

        Returns:
        Response API object.
        """
        googleads_service = self._google_ads_client.get_service("GoogleAdsService")
        response = googleads_service.mutate(
            customer_id=customer_id, mutate_operations=mutate_operations
        )

        return response

    def print_response_details(self, response):
        """Prints the details of a MutateGoogleAdsResponse.
        Parses the "response" oneof field name and uses it to extract the new
        entity's name and resource name.
        Args:
            response: a MutateGoogleAdsResponse object.
        """
        # Parse the Mutate response to print details about the entities that
        # were created by the request.
        suffix = "_result"
        for result in response.mutate_operation_responses:
            for field_descriptor, value in result._pb.ListFields():
                if field_descriptor.name.endswith(suffix):
                    name = field_descriptor.name[: -len(suffix)]
                else:
                    name = field_descriptor.name
                print(
                    f"Created a(n) {name} with "
                    f"{str(value).strip()}."
                )