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


class AssetService:
  """Class for Asset Creation.

  Contains all methods to create assets in Google Ads pMax campaings.
  """

  def __init__(self, google_ads_service):
    """Constructs the AssetService instance.

    Args:
      google_ads_service: instance of the google_ads_service injection.
    """
    self.google_ads_service = google_ads_service

  def create_asset_mutation(
      self, row, customer_id, asset_group_id, new_asset_group
  ):
    """Set up mutate object for creating asset.

    Args:
      row: Sheet Row list.
      customer_id: Google Ads Customer id.
      asset_group_id: Google Ads Asset group id.
      new_asset_group: Boolean, indicating if asset group is new or already
        existing in Google Ads.

    Returns:
      operations, asset_resource
    """
    operations = []
    asset_resource = None

    asset_url = (
        row[assetsColumnMap.ASSET_URL.value]
        if assetsColumnMap.ASSET_URL.value < len(row)
        else ""
    )
    asset_type = row[assetsColumnMap.ASSET_TYPE.value]
    asset_name_or_text = (
        row[assetsColumnMap.ASSET_TEXT.value]
        if assetsColumnMap.ASSET_TEXT.value < len(row)
        else ""
    )
    asset_action_selection = (
        row[assetsColumnMap.ASSET_CALL_TO_ACTION.value]
        if assetsColumnMap.ASSET_CALL_TO_ACTION.value < len(row)
        else ""
    )

    image_asset_types = {
        "MARKETING_IMAGE",
        "SQUARE_MARKETING_IMAGE",
        "PORTRAIT_MARKETING_IMAGE",
        "LOGO",
        "LANDSCAPE_LOGO",
    }

    if asset_type == "YOUTUBE_VIDEO":
      mutate_operation, asset_resource, field_type = (
          self.google_ads_service.create_video_asset(
              asset_url, asset_type, customer_id
          )
      )
      operations.append(mutate_operation)
    elif asset_type in image_asset_types:
      mutate_operation, asset_resource, field_type = (
          self.google_ads_service.create_image_asset(
              asset_url,
              asset_name_or_text + f" #{uuid.uuid4()}",
              asset_type,
              customer_id,
          )
      )
      operations.append(mutate_operation)
    elif asset_type in [
        "HEADLINE",
        "DESCRIPTION",
        "LONG_HEADLINE",
        "BUSINESS_NAME",
    ]:
      mutate_operation, asset_resource, field_type = (
          self.google_ads_service.create_text_asset(
              asset_name_or_text, asset_type, customer_id
          )
      )
      if not new_asset_group:
        operations.append(
            self.google_ads_service.add_asset_to_asset_group(
                asset_resource, asset_group_id, field_type, customer_id
            )
        )
    elif asset_type == "CALL_TO_ACTION_SELECTION":
      mutate_operation, asset_resource, field_type = (
          self.google_ads_service.create_call_to_action_asset(
              asset_action_selection, asset_type, customer_id
          )
      )
      operations.append(mutate_operation)

    if asset_resource:
      operations.append(
          self.google_ads_service.add_asset_to_asset_group(
              asset_resource, asset_group_id, field_type, customer_id
          )
      )

    return operations, asset_resource
