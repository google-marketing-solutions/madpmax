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

from enums.asset_status import assetStatus
from enums.campaign_list_column_map import campaignListColumnMap
from enums.new_asset_groups_column_map import newAssetGroupsColumnMap
from enums.sheets import sheets
from typing import List
import reference_enums
import validators


class AssetGroupService:
  """Class for Campaign Creation.

  Contains all methods to create pMax Campaings in Google Ads.
  """

  def __init__(
      self, google_ads_service, sheet_service, asset_service, google_ads_client
  ):
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
    self.asset_service = asset_service
    self._cache_ad_group_ad = {}
    self.prev_image_asset_list = None
    self.prev_customer_id = None
    self.asset_group_temp_id = -1000
    self.sheet_id = self.sheet_service.get_sheet_id("NewAssetGroups")

  def process_asset_group_data_and_create(
      self, asset_group_data, campaign_data
  ):
    """Creates campaigns via google API based.

    Args:
      asset_group_data: Actual data for creating new asset groups in array form.
      campaign_data: Campaign data from spreadsheet in array form.
    """
    operations = []

    for index, asset_group_row in enumerate(asset_group_data):
      if (
          asset_group_row[newAssetGroupsColumnMap.STATUS.value]
          != assetStatus.UPLOADED.value
          and len(asset_group_row) > newAssetGroupsColumnMap.LOGO.value
      ):
        campaign_alias = self.compile_campaign_alias(asset_group_row)
        campaign_details = self.sheet_service.get_sheet_row(
            campaign_alias, campaign_data, sheets.CAMPAIGN.value
        )

        # Set Campaing Variables used to create and assign Asset Groups
        if campaign_details:
          customer_id = campaign_details[campaignListColumnMap.CUSTOMER_ID.value]
          customer_name = campaign_details[campaignListColumnMap.CUSTOMER_NAME.value]
          campaign_id = campaign_details[campaignListColumnMap.CAMPAIGN_ID.value]
          campaign_name = campaign_details[campaignListColumnMap.CAMPAIGN_NAME.value]

        # Set Asset Groups Variables used to create and assign Asset Groups
        asset_group_name = asset_group_row[
            newAssetGroupsColumnMap.ASSET_GROUP_NAME.value
        ]
        asset_group_status = asset_group_row[
            newAssetGroupsColumnMap.ASSET_GROUP_STATUS.value
        ]
        asset_group_final_url = asset_group_row[
            newAssetGroupsColumnMap.FINAL_URL.value
        ]
        asset_group_mobile_url = asset_group_row[
            newAssetGroupsColumnMap.MOBILE_URL.value
        ]
        asset_group_path1 = asset_group_row[newAssetGroupsColumnMap.PATH1.value]
        asset_group_path2 = asset_group_row[newAssetGroupsColumnMap.PATH2.value]
        asset_group_id = self.asset_group_temp_id
        # Increment temp id for next Asset Group
        self.asset_group_temp_id -= 1

        # Append Asset Group Creation to Bulk Operations Object.
        operations.append(
            self.create_asset_group(
                asset_group_name,
                asset_group_status,
                asset_group_final_url,
                asset_group_mobile_url,
                asset_group_path1,
                asset_group_path2,
                asset_group_id,
                campaign_id,
                customer_id,
            )
        )

        # Create 3 mandatory headline assets and extend them to Bulk Operations
        # Object.
        headlines = asset_group_row[
            newAssetGroupsColumnMap.HEADLINE1.value : newAssetGroupsColumnMap.HEADLINE3.value
            + 1
        ]
        headline_resource_names = self.create_mandatory_assets_asset_group(
            headlines, customer_id
        )
        operations.extend(
            self.consolidate_mandatory_assets_group_operations(
                headline_resource_names,
                assetTypes.HEADLINE,
                asset_group_id,
                customer_id,
            )
        )

        # Create 2 mandatory description assets and extend them to Bulk
        # Operations Object.
        descriptions = asset_group_row[
            newAssetGroupsColumnMap.DESCRIPTION1.value : newAssetGroupsColumnMap.DESCRIPTION2.value
            + 1
        ]
        description_resource_names = self.create_mandatory_assets_asset_group(
            descriptions, customer_id
        )
        operations.extend(
            self.consolidate_mandatory_assets_group_operations(
                description_resource_names,
                assetTypes.DESCRIPTION,
                asset_group_id,
                customer_id,
            )
        )

        # Create all other mandatory assets and extend them to
        # Bulk Operations Object.
        # These asset types can be created and assigned to the new asset group
        # in one and the same bulk operation.
        other_assets = asset_group_row[
            newAssetGroupsColumnMap.LONG_HEADLINE.value : newAssetGroupsColumnMap.LOGO.value
            + 1
        ]
        operations.extend(
            self.create_other_assets_asset_group(
                other_assets, asset_group_id, customer_id
            )
        )

        # Send the operations to the Google Ads API and collect the response.
        response, error_message = self.google_ads_service.bulk_mutate(
            operations, customer_id
        )

        # Handle response from bulk creation and write status back to the
        # spreadsheet.
        if error_message:
          self.sheet_service.variable_update_sheet_status(
              index,
              self.sheet_id,
              newAssetGroupsColumnMap.STATUS.value,
              assetStatus.ERROR.value,
              error_message,
              newAssetGroupsColumnMap.MESSAGE.value,
          )
        else:
          self.sheet_service.variable_update_sheet_status(
              index,
              self.sheet_id,
              newAssetGroupsColumnMap.STATUS.value,
              assetStatus.UPLOADED.value,
              newAssetGroupsColumnMap.MESSAGE.value,
          )

          # Retrieve the asset group id, and add it to the sheetlist array.
          asset_group_id = response.mutate_operation_responses[
              0
          ].asset_group_result.resource_name.split("/")[-1]

          # Add asset_group_sheetlist to the spreadsheet.
          self.sheet_service.add_new_asset_group_to_list_sheet([
              customer_name,
              customer_id,
              campaign_name,
              campaign_id,
              asset_group_name,
              asset_group_id,
          ])

  def create_other_assets_asset_group(
      self, assets, asset_group_id, customer_id
  ):
    """Logic to create mandatory other assets for asset group.

    When creating the API operations for a new Asset Group. The API expects
    the operations in a specific order. First 3 headlines and 2 descriptions,
    and consequently all other asset operations can be appended.
    This function generates the other assets (Image, Logo, Business name, etc.)
    creation operations and the operations to assign these assets to the
    assetgroup and returns the operations object.

    Args:
      assets: ARRAY of STRINGS, asset values.
      asset_group_id: INT Google Ads Asset Group id
      customer_id: INT Google Ads customer id.

    Returns:
      ARRAY of Objects: Google Ads API Operation objects.
    """
    operations = []

    for index, asset_value in enumerate(assets):
      col_num = newAssetGroupsColumnMap.LONG_HEADLINE.value + index
      asset_type = newAssetGroupsColumnMap(col_num).name

      asset_operation = self.asset_service.create_asset(
          asset_type, asset_value, customer_id
      )
      resource_name = asset_operation.asset_operation.create.resource_name

      if resource_name:
        asset_group_asset_operation = (
            self.asset_service.add_asset_to_asset_group(
                resource_name, asset_group_id, asset_type, customer_id
            )
        )

        operations.extend([asset_operation, asset_group_asset_operation])

    return operations

  def consolidate_mandatory_assets_group_operations(
      self, resource_names, asset_type, asset_group_id, customer_id
  ):
    """Logic to create mandatory text assets for asset group.

    When creating the API operations for a new Asset Group. The API expects
    the operations in a specific order. 3 headlines and 2 descriptions. This
    function creates the asset group assignment operations to assign existing
    text assets in Google ads to the new asset group.

    Args:
      resource_names: ARRAY of STRINGS, consisting of Google Ads Resource names.
      asset_type: ENUM The asset type that is created, HEADLINE, DESCRIPTION.
      asset_group_id: INT Google Ads Asset Group id.
      customer_id: INT Google Ads customer id.

    Returns:
      ARRAY of Objects: Google Ads API Operation objects for asset assignment.
    """
    operations = []
    for resource_name in resource_names:
      operations.append(
          self.asset_service.add_asset_to_asset_group(
              resource_name, asset_group_id, asset_type, customer_id
          )
      )

    return operations

  def create_mandatory_assets_asset_group(self, text_assets, customer_id):
    """Logic to create mandatory text assets for asset group.

    When creating the API operations for a new Asset Group. The API expects
    the operations in a specific order. 3 headlines and 2 descriptions, need
    to pre-exist in Google Ads, and should be added with their definite
    resource names to the Asset Group Operations object. This function creates
    the mandatory text assets in Google ads and returns the definite resource
    names.

    Args:
      text_Assets: ARRAY of STRINGS, text asset values.
      customer_id: INT Google Ads customer id.

    Returns:
      ARRAY of STRINGS, consisting of Google Ads Resource names.
    """
    operations = []

    for text in text_assets:
      operations.append(self.asset_service.create_text_asset(text, customer_id))

    resource_names = self.google_ads_service.create_multiple_text_assets(
        operations, customer_id
    )

    return resource_names

  def create_asset_group(
      self,
      asset_group_name,
      asset_group_status,
      asset_group_final_url,
      asset_group_mobile_url,
      asset_group_path1,
      asset_group_path2,
      asset_group_id,
      campaign_id,
      customer_id,
  ):
    """Creates a list of MutateOperations that create a new asset_group.

    A temporary ID will be assigned to this asset group so that it can
    be referenced by other objects being created in the same Mutate request.

    Args:
      asset_group_name: String value with Asset Group Name.
      asset_group_status: ENUM with Asset group status.
      asset_group_final_url: String value with landing page url.
      asset_group_mobile_url: String value with mobile landing page.
      asset_group_path1: String value with url path.
      asset_group_path2: String value with url path.
      asset_group_id: a google ads asset group id.
      campaign_id: a pmax campaign ID.
      customer_id: a client customer ID.

    Returns:
      MutateOperation that create a new asset group.
    """
    mutate_operation = None

    asset_group_service = self._google_ads_client.get_service(
        "AssetGroupService"
    )
    campaign_service = self._google_ads_client.get_service("CampaignService")

    if not asset_group_name:
      raise ValueError("Asset Group Name is required to create an Asset Group")
    if not asset_group_status:
      raise ValueError("Status is required to create an Asset Group")
    if not asset_group_final_url:
      raise ValueError("Final URL is required to create an Asset Group")
    if not validators.url(asset_group_final_url):
      raise ValueError(
          f"Final URL '{asset_group_final_url}' is not a valid URL"
      )
    if not asset_group_mobile_url:
      raise ValueError("Mobile URL is required to create an Asset Group")
    if not validators.url(asset_group_mobile_url):
      raise ValueError(
          f"Mobile URL '{asset_group_mobile_url}' is not a valid URL"
      )

    # Create the AssetGroup
    mutate_operation = self._google_ads_client.get_type("MutateOperation")
    asset_group = mutate_operation.asset_group_operation.create
    asset_group.name = asset_group_name
    asset_group.status = self._google_ads_client.enums.AssetGroupStatusEnum[
        asset_group_status
    ]
    asset_group.final_urls.append(asset_group_final_url)
    asset_group.final_mobile_urls.append(asset_group_mobile_url)
    asset_group.path1 = asset_group_path1
    asset_group.path2 = asset_group_path2
    asset_group.resource_name = asset_group_service.asset_group_path(
        customer_id,
        asset_group_id,
    )
    asset_group.campaign = campaign_service.campaign_path(
        customer_id, campaign_id
    )

    return mutate_operation

  def compile_campaign_alias(self, sheet_row: List[str | int]) -> str | None:
    """Helper method to compile campaign alias from row content.

    Args:
      sheet_row: List of strings representing one row input from the
        spreadsheet.

    Returns:
      String value of the campaign alias or None.
    """
    result = None

    if (
        sheet_row[reference_enums.AssetsColumnMap.customer_name].strip()
        and sheet_row[reference_enums.AssetsColumnMap.campaign_name].strip()
    ):
      result = (
          sheet_row[reference_enums.AssetsColumnMap.customer_name]
          + ";"
          + sheet_row[reference_enums.AssetsColumnMap.campaign_name]
      )

    return result
