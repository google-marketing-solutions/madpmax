"""Provides functionality to create campaigns."""

from uuid import uuid4
from enums.asset_column_map import assetsColumnMap


class AssetService:

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
      asset_type: type of the asset
    """
    operations = []
    if assetsColumnMap.ASSET_URL.value < len(row):
      asset_url = row[assetsColumnMap.ASSET_URL.value]
    else:
      asset_url = ""

    # Asset name / asset type / call to action selection
    asset_type = row[assetsColumnMap.ASSET_TYPE.value]
    asset_name_or_text = ""

    if assetsColumnMap.ASSET_TEXT.value < len(row):
      asset_name_or_text = row[assetsColumnMap.ASSET_TEXT.value]

    if assetsColumnMap.ASSET_CALL_TO_ACTION.value < len(row):
      asset_action_selection = row[assetsColumnMap.ASSET_CALL_TO_ACTION.value]

    print(
        "asset Text after try: ", asset_name_or_text, " with type ", asset_type
    )
    if asset_type == "YOUTUBE_VIDEO":
      asset_creation_mutate_operation, asset_resource, field_type = (
          self.google_ads_service._create_video_asset(
              asset_url, asset_type, customer_id
          )
      )
      operations.append(asset_creation_mutate_operation)

      asset_to_asset_group_mutate_operation = (
          self.google_ads_service.add_asset_to_asset_group(
              asset_resource, asset_group_id, field_type, customer_id
          )
      )
      operations.append(asset_to_asset_group_mutate_operation)
    # Possible values "MARKETING_IMAGE", "SQUARE_MARKETING_IMAGE", "PORTRAIT_MARKETING_IMAGE"
    # Possible values "LOGO", "LANDSCAPE_LOGO"
    elif "IMAGE" in asset_type or "LOGO" in asset_type:
      asset_creation_mutate_operation, asset_resource, field_type = (
          self.google_ads_service._create_image_asset(
              asset_url,
              asset_name_or_text + f" #{uuid4()}",
              asset_type,
              customer_id,
          )
      )
      operations.append(asset_creation_mutate_operation)

      asset_to_asset_group_mutate_operation = (
          self.google_ads_service.add_asset_to_asset_group(
              asset_resource, asset_group_id, field_type, customer_id
          )
      )
      operations.append(asset_to_asset_group_mutate_operation)
    elif asset_type == "HEADLINE" or asset_type == "DESCRIPTION":
      asset_creation_mutate_operation, asset_resource, field_type = (
          self.google_ads_service._create_text_asset(
              asset_name_or_text, asset_type, customer_id
          )
      )
      operations.append(asset_creation_mutate_operation)

      if not new_asset_group:
        asset_to_asset_group_mutate_operation = (
            self.google_ads_service.add_asset_to_asset_group(
                asset_resource, asset_group_id, field_type, customer_id
            )
        )
        operations.append(asset_to_asset_group_mutate_operation)
    elif asset_type == "LONG_HEADLINE" or asset_type == "BUSINESS_NAME":
      asset_creation_mutate_operation, asset_resource, field_type = (
          self.google_ads_service._create_text_asset(
              asset_name_or_text, asset_type, customer_id
          )
      )
      operations.append(asset_creation_mutate_operation)

      asset_to_asset_group_mutate_operation = (
          self.google_ads_service.add_asset_to_asset_group(
              asset_resource, asset_group_id, field_type, customer_id
          )
      )
      operations.append(asset_to_asset_group_mutate_operation)
    elif asset_type == "CALL_TO_ACTION":
      asset_creation_mutate_operation, asset_resource, field_type = (
          self.google_ads_service._create_call_to_action_asset(
              asset_action_selection, asset_type, customer_id
          )
      )
      operations.append(asset_creation_mutate_operation)

      asset_to_asset_group_mutate_operation = (
          self.google_ads_service.add_asset_to_asset_group(
              asset_resource, asset_group_id, field_type, customer_id
          )
      )
      operations.append(asset_to_asset_group_mutate_operation)

    return operations, asset_resource
