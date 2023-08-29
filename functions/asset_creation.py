
"""Provides functionality to create campaigns."""

from datetime import datetime
from datetime import datetime
import enum
import ads_api
from uuid import uuid4


class AssetService:

  class assetsColumnMap(enum.IntEnum):
    ASSET_GROUP_ALIAS = 0,
    ASSET_STATUS = 1,
    DELETE_ASSET = 2,
    ASSET_TYPE = 3,
    ASSET_TEXT = 4,
    ASSET_CALL_TO_ACTION = 5,
    ASSET_URL = 6,
    ERROR_MESSAGE = 7,
    ASSET_GROUP_ASSET = 8

  def __init__(self):
    """Constructs the AssetService instance.

    Args:
      googleAdsService: instance of the googleAdsService for dependancy
        injection.
    """
    self.googleAdsService = ads_api.AdService("config.yaml")


  def _create_asset_mutation(self, row, customer_id, asset_group_id, new_asset_group):
    """Set up mutate object for creating asset.

    Args:
      asset_type: type of the asset
    """
    operations = []
    if self.assetsColumnMap.ASSET_URL.value < len(row):
        asset_url = row[self.assetsColumnMap.ASSET_URL]
    else:
      asset_url = ""

    # Asset name / asset type / call to action selection
    asset_type = row[self.assetsColumnMap.ASSET_TYPE]
    asset_name_or_text = row[self.assetsColumnMap.ASSET_TEXT]
    if self.assetsColumnMap.ASSET_CALL_TO_ACTION < len(row):
        asset_action_selection = row[self.assetsColumnMap.ASSET_CALL_TO_ACTION]

    if asset_type == "YOUTUBE_VIDEO":
        asset_creation_mutate_operation, asset_resource, field_type = (
            self.googleAdsService._create_video_asset(
                asset_url, asset_type, customer_id
            )
        )
        operations.append(asset_creation_mutate_operation)

        asset_to_asset_group_mutate_operation = (
            self.googleAdsService._add_asset_to_asset_group(
                asset_resource, asset_group_id, field_type, customer_id
            )
        )
        operations.append(asset_to_asset_group_mutate_operation)
    # Possible values "MARKETING_IMAGE", "SQUARE_MARKETING_IMAGE", "PORTRAIT_MARKETING_IMAGE"
    # Possible values "LOGO", "LANDSCAPE_LOGO"
    elif "IMAGE" in asset_type or "LOGO" in asset_type:
      # TODO add removal of images if needed
      # TODO add image error handling
      asset_creation_mutate_operation, asset_resource, field_type = (
          self.googleAdsService._create_image_asset(
              asset_url,
              asset_name_or_text + f" #{uuid4()}",
              asset_type,
              customer_id
          )
      )
      operations.append(asset_creation_mutate_operation)

      asset_to_asset_group_mutate_operation = (
          self.googleAdsService._add_asset_to_asset_group(
              asset_resource, asset_group_id, field_type, customer_id
          )
      )
      operations.append(asset_to_asset_group_mutate_operation)
    elif asset_type == "HEADLINE" or asset_type == "DESCRIPTION":
      asset_creation_mutate_operation, asset_resource, field_type = (
          self.googleAdsService._create_text_asset(
              asset_name_or_text, asset_type, customer_id
          )
      )
      operations.append(asset_creation_mutate_operation)

      if not new_asset_group:
        asset_to_asset_group_mutate_operation = self.googleAdsService._add_asset_to_asset_group(
            asset_resource, asset_group_id, field_type, customer_id
        )
        operations.append(asset_to_asset_group_mutate_operation)
    elif asset_type == "LONG_HEADLINE" or asset_type == "BUSINESS_NAME":
      asset_creation_mutate_operation, asset_resource, field_type = (
          self.googleAdsService._create_text_asset(
              asset_name_or_text, asset_type, customer_id
          )
      )
      operations.append(asset_creation_mutate_operation)

      asset_to_asset_group_mutate_operation = self.googleAdsService._add_asset_to_asset_group(
          asset_resource, asset_group_id, field_type, customer_id
      )
      operations.append(asset_to_asset_group_mutate_operation)
    elif asset_type == "CALL_TO_ACTION":
        asset_creation_mutate_operation, asset_resource, field_type = (
            self.googleAdsService._create_call_to_action_asset(
                asset_action_selection, customer_id
            )
        )
        operations.append(asset_creation_mutate_operation)

        asset_to_asset_group_mutate_operation = (
            self.googleAdsService._add_asset_to_asset_group(
                asset_resource, asset_group_id, field_type, customer_id
            )
        )
        operations.append(asset_to_asset_group_mutate_operation)
    
    return operations, asset_resource

  