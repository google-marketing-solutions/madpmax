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
"""Provides functionality to create assets in Google Ads."""

import uuid
import requests
import validators


class AssetService:
  """Class for Asset Creation.

  Contains all methods to create assets in Google Ads pMax campaings.
  """

  def __init__(self, google_ads_client, google_ads_service):
    """Constructs the AssetService instance.

    Args:
      google_ads_client: Google Ads API client, dependency injection.
      google_ads_service: Ads Service Class dependency injection.
    """
    self._google_ads_client = google_ads_client
    self._google_ads_service = google_ads_service
    self.image_asset_types = {
        "MARKETING_IMAGE",
        "SQUARE_MARKETING_IMAGE",
        "PORTRAIT_MARKETING_IMAGE",
        "LOGO",
        "LANDSCAPE_LOGO",
    }
    self.text_asset_types = {
        "HEADLINE",
        "DESCRIPTION",
        "LONG_HEADLINE",
        "BUSINESS_NAME",
    }
    self.asset_temp_id = -10000

  def create_asset(self, asset_type, asset_value, customer_id):
    """Set up mutate object for creating asset.

    Args:
      asset_type: Type of Asset.
      asset_value: Input value used to create asset (string).
      customer_id: Google Ads Customer id.

    Returns:
      asset operation Array
    """
    mutate_operation = None

    match asset_type:
      case "YOUTUBE_VIDEO":
        if not asset_value:
          raise ValueError(f"Asset URL is required to create a {asset_type} "
                           "Asset")
        if not validators.url(asset_value):
          raise ValueError(f"Asset URL '{asset_value}' is not a valid URL")
        mutate_operation = (
            self.create_video_asset(
                asset_value, customer_id
            )
        )
      case asset_type if asset_type in self.image_asset_types:
        if not asset_value:
          raise ValueError(f"Asset URL is required to create a {asset_type} "
                           "Asset")
        if not validators.url(asset_value):
          raise ValueError(f"Asset URL '{asset_value}' is not a valid URL")
        mutate_operation = (
            self.create_image_asset(
                asset_value,
                f"#{uuid.uuid4()}",
                customer_id,
            )
        )
      case asset_type if asset_type in self.text_asset_types:
        if not asset_value:
          raise ValueError(f"Asset Text is required to create a {asset_type} "
                           "Asset")
        mutate_operation = (
            self.create_text_asset(
                asset_value, customer_id
            )
        )
      case "CALL_TO_ACTION_SELECTION":
        if not asset_value:
          raise ValueError(f"Call To Action required to create a {asset_type} "
                           "Asset")
        mutate_operation = (
            self.create_call_to_action_asset(
                asset_value, customer_id
            )
        )

    return mutate_operation

  def create_text_asset(self, text, customer_id):
    """Generates the image asset and returns the resource name.

    Args:
      text: full url of the image file.
      customer_id: customer id.

    Returns:
      Asset operation or None.
    """
    asset_service = self._google_ads_client.get_service("AssetService")
    resource_name = asset_service.asset_path(customer_id, self.asset_temp_id)

    self.asset_temp_id -= 1

    # Create and link the Marketing Image Asset.
    asset_operation = self._google_ads_client.get_type("MutateOperation")
    asset = asset_operation.asset_operation.create
    asset.resource_name = resource_name
    asset.text_asset.text = text

    return asset_operation

  def create_image_asset(self, image_url, name, customer_id):
    """Generates the image asset and returns the resource name.

    Args:
      image_url: full url of the image file.
      name: the name of the image asset.
      customer_id: customer id.

    Returns:
      Asset operation or None.
    """
    # Download image from URL and determine the ratio.
    image_content = requests.get(image_url).content

    asset_service = self._google_ads_client.get_service("AssetService")
    resource_name = asset_service.asset_path(customer_id, self.asset_temp_id)

    self.asset_temp_id -= 1

    # Create and link the Marketing Image Asset.
    asset_operation = self._google_ads_client.get_type("MutateOperation")
    asset = asset_operation.asset_operation.create
    asset.name = name
    asset.type = self._google_ads_client.enums.AssetTypeEnum.IMAGE
    asset.resource_name = resource_name
    asset.image_asset.full_size.url = image_url
    asset.image_asset.data = image_content

    return asset_operation

  def create_video_asset(self, video_url, customer_id):
    """Generates the image asset and returns the resource name.

    Args:
      video_url: full url of the image file.
      customer_id: customer id.

    Returns:
      Asset operation or None.
    """
    youtube_id = self._google_ads_service._retrieve_yt_id(video_url)

    asset_service = self._google_ads_client.get_service("AssetService")
    resource_name = asset_service.asset_path(customer_id, self.asset_temp_id)

    self.asset_temp_id -= 1

    # Create and link the Marketing Image Asset.
    asset_operation = self._google_ads_client.get_type(
        "MutateOperation")
    asset = asset_operation.asset_operation.create
    asset.resource_name = resource_name
    unique_id = uuid.uuid4()
    asset.youtube_video_asset.youtube_video_title = (
        f"Marketing Video #{unique_id}"
    )
    asset.youtube_video_asset.youtube_video_id = youtube_id

    return asset_operation

  def create_call_to_action_asset(self, action_selection, customer_id):
    """Generates the image asset and returns the resource name.

    Args:
      action_selection: selection from call to action ENUM
      customer_id: customer id.

    Returns:
      Asset operation or None.
    """
    asset_service = self._google_ads_client.get_service("AssetService")
    resource_name = asset_service.asset_path(customer_id, self.asset_temp_id)
    call_to_action_type = action_selection.upper().replace(" ", "_")

    self.asset_temp_id -= 1

    asset_operation = self._google_ads_client.get_type("MutateOperation")
    asset = asset_operation.asset_operation.create
    asset.resource_name = resource_name
    asset.call_to_action_asset.call_to_action = (
        self._google_ads_client.enums.CallToActionTypeEnum[call_to_action_type]
    )

    return asset_operation

  def add_asset_to_asset_group(self, resource_name, asset_group_id, asset_type,
                               customer_id):
    """Adds the asset resource to an asset group.

    Args:
      resource_name: resource name of the asset group.
      asset_group_id: Google Ads asset group id.
      asset_type: Asset type.
      customer_id: customer id.

    Returns:
      asset_group_asset_operation
    """
    asset_group_service = self._google_ads_client.get_service(
        "AssetGroupService"
    )

    asset_group_asset_operation = self._google_ads_client.get_type(
        "MutateOperation"
    )
    asset_group_asset = (
        asset_group_asset_operation.asset_group_asset_operation.create
    )

    field_type = self._google_ads_client.enums.AssetFieldTypeEnum[asset_type]

    asset_group_asset.field_type = field_type
    asset_group_asset.asset_group = asset_group_service.asset_group_path(
        customer_id,
        asset_group_id,
    )
    asset_group_asset.asset = resource_name

    return asset_group_asset_operation
