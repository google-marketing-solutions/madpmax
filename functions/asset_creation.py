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
from enums.asset_column_map import assetsColumnMap
from enums.asset_group_list import assetGroupList
from enums.asset_status import assetStatus
from enums.asset_types import assetTypes
from enums.sheets import sheets
from typing import List
import requests
import validators


class AssetService:
  """Class for Asset Creation.

  Contains all methods to create assets in Google Ads pMax campaings.
  """

  def __init__(self, google_ads_client, google_ads_service, sheet_service):
    """Constructs the AssetService instance.

    Args:
      google_ads_client: Google Ads API client, dependency injection.
      google_ads_service: Ads Service Class dependency injection.
    """
    self._google_ads_client = google_ads_client
    self._google_ads_service = google_ads_service
    self.sheet_service = sheet_service

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

  def process_asset_data_and_create(self, asset_data, asset_group_data):
    """Process data from the sheet to create assets.

    Args:
      asset_data: Array of Asset data from the sheeet.
      asset_group_data: Array of Asset Group data from the sheet.

    Returns:
      Void. Creates asset via API.
    """
    # operations map contains separated by customer id operations
    # for Asset creation and linking of Assets to Asset Groups.
    # API allows bulk mutation only on the same customer id.
    operations = {}
    message_mapping = {}
    status_to_row_mapping = {}
    for feedback_index, asset in enumerate(asset_data):
      if asset[assetsColumnMap.STATUS.value] != assetStatus.UPLOADED.value:
        asset_type = asset[assetsColumnMap.TYPE.value]
        asset_value = self.get_asset_value_by_type(asset, asset_type)
        asset_group_alias = self.compile_asset_group_alias(asset)
        asset_group_details = self.sheet_service.get_sheet_row(
            asset_group_alias, asset_group_data, sheets.ASSET_GROUP.value
        )
        customer_id = asset_group_details[assetGroupList.CUSTOMER_ID.value]
        asset_operation = None

        try:
          asset_operation = self.create_asset(
              asset_type, asset_value, customer_id
          )
        except ValueError as ex:
          status_to_row_mapping[feedback_index] = {}
          status_to_row_mapping[feedback_index][
              "status"
          ] = assetStatus.ERROR.value
          status_to_row_mapping[feedback_index]["message"] = str(ex)
          status_to_row_mapping[feedback_index]["asset_group_asset"] = ""

        if customer_id not in operations.keys() or not operations[customer_id]:
          operations[customer_id] = []

        if asset_operation:
          operations[customer_id].append(asset_operation)
          resource_name = asset_operation.asset_operation.create.resource_name

          operations[customer_id].append(
              self.add_asset_to_asset_group(
                  resource_name,
                  asset_group_details[assetGroupList.ASSET_GROUP_ID.value],
                  asset_type,
                  customer_id,
              )
          )

          # map the index of the row to the resource that is process for allocating errors from the API call later
          message_mapping[resource_name] = feedback_index

    for customer_id in operations:
      response, error_message = self._google_ads_service.bulk_mutate(
          operations[customer_id], customer_id, True
      )

      if response:
        status_to_row_mapping.update(
            self._google_ads_service.process_asset_results(
                response,
                operations[customer_id],
                message_mapping,
                sheets.ASSETS.value,
            )
        )

        self.sheet_service.bulk_update_sheet_status(
            sheets.ASSETS.value,
            assetsColumnMap.STATUS.value,
            assetsColumnMap.ERROR_MESSAGE.value,
            assetsColumnMap.ASSET_GROUP_ASSET.value,
            status_to_row_mapping,
        )

      if error_message:
        raise Exception(f"Couldn't update Assets \n {error_message}")

  def create_asset(self, asset_type, asset_value, customer_id):
    """Set up mutate object for creating asset.

    Args:
      asset_type: Type of Asset.
      asset_value: Input value used to create asset (string).
      customer_id: Google Ads Customer id.

    Returns:
      asset operation array
    """
    mutate_operation = None

    match asset_type:
      case "YOUTUBE_VIDEO":
        if not asset_value:
          raise ValueError(
              f"Asset URL is required to create a {asset_type} Asset"
          )
        if not validators.url(asset_value):
          raise ValueError(f"Asset URL '{asset_value}' is not a valid URL")
        mutate_operation = self.create_video_asset(asset_value, customer_id)
      case asset_type if asset_type in self.image_asset_types:
        if not asset_value:
          raise ValueError(
              f"Asset URL is required to create a {asset_type} Asset"
          )
        if not validators.url(asset_value):
          raise ValueError(f"Asset URL '{asset_value}' is not a valid URL")
        mutate_operation = self.create_image_asset(
            asset_value,
            f"#{uuid.uuid4()}",
            customer_id,
        )
      case asset_type if asset_type in self.text_asset_types:
        if not asset_value:
          raise ValueError(
              f"Asset Text is required to create a {asset_type} Asset"
          )
        mutate_operation = self.create_text_asset(asset_value, customer_id)
      case "CALL_TO_ACTION_SELECTION":
        if not asset_value:
          raise ValueError(
              f"Call To Action required to create a {asset_type} Asset"
          )
        mutate_operation = self.create_call_to_action_asset(
            asset_value, customer_id
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
    asset_operation = self._google_ads_client.get_type("MutateOperation")
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

  def add_asset_to_asset_group(
      self, resource_name, asset_group_id, asset_type, customer_id
  ):
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

  def get_asset_value_by_type(self, asset_data, assetType):
    """Generates asset data and returns assetvalue based on the asset type.

    Args:
      asset_data: Array of asset data.
      assetType: Type of the asset.

    Returns:
      Value of the asset.
    """
    asset_value = ""
    match assetType:
      case assetTypes.HEADLINE:
        asset_value = (
            asset_data[assetsColumnMap.ASSET_TEXT.value]
            if assetsColumnMap.ASSET_TEXT.value < len(asset_data)
            else ""
        )
      case assetTypes.DESCRIPTION:
        asset_value = (
            asset_data[assetsColumnMap.ASSET_TEXT.value]
            if assetsColumnMap.ASSET_TEXT.value < len(asset_data)
            else ""
        )
      case assetTypes.LONG_HEADLINE:
        asset_value = (
            asset_data[assetsColumnMap.ASSET_TEXT.value]
            if assetsColumnMap.ASSET_TEXT.value < len(asset_data)
            else ""
        )
      case assetTypes.BUSINESS_NAME:
        asset_value = (
            asset_data[assetsColumnMap.ASSET_TEXT.value]
            if assetsColumnMap.ASSET_TEXT.value < len(asset_data)
            else ""
        )
      case assetTypes.CALL_TO_ACTION:
        asset_value = (
            asset_data[assetsColumnMap.ASSET_CALL_TO_ACTION.value]
            if assetsColumnMap.ASSET_CALL_TO_ACTION.value < len(asset_data)
            else ""
        )
      case _:
        asset_value = (
            asset_data[assetsColumnMap.ASSET_URL.value]
            if assetsColumnMap.ASSET_URL.value < len(asset_data)
            else ""
        )

    return asset_value

  def compile_asset_group_alias(self, sheet_row: List[str | int]) -> str | None:
    """Helper method to compile asset group alias from row content.

    Args:
      sheet_row: List of strings representing one row input from the
        spreadsheet.

    Returns:
      String value of the asset group alias or None.
    """
    result = None

    if (
        len(sheet_row) >= assetsColumnMap.ASSET_GROUP_NAME.value + 1
        and sheet_row[assetsColumnMap.CUSTOMER_NAME.value].strip()
        and sheet_row[assetsColumnMap.CAMPAIGN_NAME.value].strip()
        and sheet_row[assetsColumnMap.ASSET_GROUP_NAME.value].strip()
    ):
      result = (
          sheet_row[assetsColumnMap.CUSTOMER_NAME.value]
          + ";"
          + sheet_row[assetsColumnMap.CAMPAIGN_NAME.value]
          + ";"
          + sheet_row[assetsColumnMap.ASSET_GROUP_NAME.value]
      )

    return result