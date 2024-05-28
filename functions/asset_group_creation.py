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

from collections.abc import Sequence
import ads_api
from asset_creation import AssetService
import data_references
from google.ads.googleads import client
from sheet_api import SheetsService
import utils
import validators


class AssetGroupService:
  """Class for Campaign Creation.

  Contains all methods to create pMax Campaings in Google Ads.
  """

  def __init__(
      self,
      google_ads_service: ads_api.AdService,
      sheet_service: SheetsService,
      asset_service: AssetService,
      google_ads_client: client.GoogleAdsClient,
  ) -> None:
    """Constructs the CampaignService instance.

    Args:
      google_ads_service: Instance of the google_ads_service for dependancy
        injection.
      sheet_service: Instance of sheet_service for dependancy injection.
      asset_service: Instance of asset_creation for dependancy injection.
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
      self,
      asset_group_data: Sequence[Sequence[str | int]],
      campaign_data: Sequence[Sequence[str | int]],
  ) -> None:
    """Creates campaigns via google API based.

    Args:
      asset_group_data: Actual data for creating new asset groups in array form.
      campaign_data: Campaign data from spreadsheet in array form.
    """
    for index, asset_group_row in enumerate(asset_group_data):
      if (
          asset_group_row[data_references.newAssetGroupsColumnMap.STATUS.value]
          != data_references.RowStatus.uploaded
          and len(asset_group_row)
          > data_references.newAssetGroupsColumnMap.LOGO.value
      ):
        campaign_alias = self.compile_campaign_alias(asset_group_row)
        campaign_details = self.sheet_service.get_sheet_row(
            campaign_alias, campaign_data, data_references.SheetNames.campaigns
        )
        asset_group_name = asset_group_row[
            data_references.newAssetGroupsColumnMap.ASSET_GROUP_NAME.value
        ]
        if not campaign_details:
          utils.process_api_response_and_errors(
              None,
              "No Campaign details for this Asset Group",
              index,
              self.sheet_id,
              data_references.SheetNames.new_asset_groups,
          )

        asset_group_id = self.asset_group_temp_id
        # Increment temp id for next Asset Group
        self.asset_group_temp_id -= 1

        operations = self.generate_mandatory_assets_for_asset_group(
            asset_group_row, asset_group_id, asset_group_name, campaign_details
        )

        response, error_message = self.google_ads_service.bulk_mutate(
            operations,
            campaign_details[data_references.CampaignList.customer_id],
        )
        utils.process_api_response_and_errors(
            response,
            error_message,
            index,
            self.sheet_id,
            data_references.SheetNames.new_asset_groups,
            self.sheet_service,
            campaign_details,
            asset_group_name,
        )

  def generate_mandatory_assets_for_asset_group(
      self,
      asset_group_row: Sequence[str | int],
      asset_group_id: str,
      asset_group_name: str,
      campaign_details: Sequence[str | int],
  ) -> Sequence[
      tuple[ads_api.AssetOperation, ads_api.AssetGroupOperation]
      | ads_api.AssetToAssetGroupOperation
  ]:
    """Logic to create mandatory assets for asset group into one dictionary.

    When creating the API operations for a new Asset Group, the API expects
    the operations in a specific order. First 3 headlines and 2 descriptions,
    and consequently all other asset operations can be appended.
    This function consolidates all mandatory assets for asset group
    in the correct order and returns a list of operations to send to the API.

    Args:
      asset_group_row: List of asset group values.
      asset_group_id: Google Ads Asset Group id
      asset_group_name: Name of the asset group.
      campaign_details: List of campaign data.

    Returns:
      List of Assets Operations from creating assets and tuple of Assets
      Operations and Asset Group Operation from appending Assets to Asset Group.
    """
    operations = []
    campaign_id = campaign_details[data_references.CampaignList.campaign_id]
    customer_id = campaign_details[data_references.CampaignList.customer_id]

    operations.append(
        self.create_asset_group(
            asset_group_name,
            asset_group_row[
                data_references.newAssetGroupsColumnMap.ASSET_GROUP_STATUS.value
            ],
            asset_group_row[
                data_references.newAssetGroupsColumnMap.FINAL_URL.value
            ],
            asset_group_row[
                data_references.newAssetGroupsColumnMap.MOBILE_URL.value
            ],
            asset_group_row[
                data_references.newAssetGroupsColumnMap.PATH1.value
            ],
            asset_group_row[
                data_references.newAssetGroupsColumnMap.PATH2.value
            ],
            asset_group_id,
            campaign_id,
            customer_id,
        )
    )

    # Create 3 mandatory headline assets, extend them to Bulk Operations Object.
    headline_data = asset_group_row[
        data_references.newAssetGroupsColumnMap.HEADLINE1.value : data_references.newAssetGroupsColumnMap.HEADLINE3.value
        + 1
    ]
    headlines = self.create_mandatory_text_assets(
        headline_data,
        customer_id,
    )
    operations.extend(
        self.consolidate_mandatory_assets_group_operations(
            headlines,
            data_references.AssetTypes.headline,
            asset_group_id,
            customer_id,
        )
    )

    # Create 2 mandatory description assets and extend them to Bulk
    # Operations Object.
    descriptions = asset_group_row[
        data_references.newAssetGroupsColumnMap.DESCRIPTION1.value : data_references.newAssetGroupsColumnMap.DESCRIPTION2.value
        + 1
    ]
    description_resource_names = self.create_mandatory_text_assets(
        descriptions,
        customer_id,
    )
    operations.extend(
        self.consolidate_mandatory_assets_group_operations(
            description_resource_names,
            data_references.AssetTypes.description,
            asset_group_id,
            customer_id,
        )
    )

    # Create all other mandatory assets and extend them to
    # Bulk Operations Object.
    # These asset types can be created and assigned to the new asset group
    # in one and the same bulk operation.
    operations.extend(
        self.create_other_assets_asset_group(
            asset_group_row[
                data_references.newAssetGroupsColumnMap.LONG_HEADLINE.value : data_references.newAssetGroupsColumnMap.LOGO.value
                + 1
            ],
            asset_group_id,
            customer_id,
        )
    )

    return operations

  def create_other_assets_asset_group(
      self, assets: Sequence[str], asset_group_id: str, customer_id: int
  ) -> Sequence[tuple[ads_api.AssetOperation, ads_api.AssetGroupOperation]]:
    """Logic to create mandatory other assets for asset group.

    When creating the API operations for a new Asset Group. The API expects
    the operations in a specific order. First 3 headlines and 2 descriptions,
    and consequently all other asset operations can be appended.
    This function generates the other assets (Image, Logo, Business name, etc.)
    creation operations and the operations to assign these assets to the
    assetgroup and returns the operations object.

    Args:
      assets: ARRAY of STRINGS, asset values.
      asset_group_id: STR Google Ads Asset Group id.
      customer_id: INT Google Ads customer id.

    Returns:
      ARRAY of Assets and Asset Group : Google Ads API Operation objects.
    """
    operations = []

    for index, asset_value in enumerate(assets):
      col_num = (
          data_references.newAssetGroupsColumnMap.LONG_HEADLINE.value + index
      )
      asset_type = data_references.newAssetGroupsColumnMap(col_num).name

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
      self,
      resource_names: Sequence[str],
      asset_type: str,
      asset_group_id: str,
      customer_id: str,
  ) -> Sequence[ads_api.AssetToAssetGroupOperation]:
    """Logic to create mandatory text assets for asset group.

    When creating the API operations for a new Asset Group. The API expects
    the operations in a specific order. 3 headlines and 2 descriptions. This
    function creates the asset group assignment operations to assign existing
    text assets in Google ads to the new asset group.

    Args:
      resource_names: ARRAY of STRINGS, consisting of Google Ads Resource names.
      asset_type: ENUM The asset type that is created, HEADLINE, DESCRIPTION.
      asset_group_id: Google Ads Asset Group id.
      customer_id: Google Ads customer id.

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

  def create_mandatory_text_assets(
      self, text_assets: Sequence[str], customer_id: str
  ) -> Sequence[str]:
    """Logic to create mandatory text assets for asset group.

    When creating the API operations for a new Asset Group. The API expects
    the operations in a specific order. 3 headlines and 2 descriptions, need
    to pre-exist in Google Ads, and should be added with their definite
    resource names to the Asset Group Operations object. This function creates
    the mandatory text assets in Google ads and returns the definite resource
    names.

    Args:
      text_assets: ARRAY of STRINGS, text asset values.
      customer_id: Google Ads customer id.

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
      asset_group_name: str,
      asset_group_status: str,
      asset_group_final_url: str,
      asset_group_mobile_url: str,
      asset_group_path1: str,
      asset_group_path2: str,
      asset_group_id: str,
      campaign_id: str,
      customer_id: str,
  ) -> ads_api.AssetGroupOperation:
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

  def compile_campaign_alias(
      self, sheet_row: Sequence[str | int]
  ) -> str | None:
    """Helper method to compile campaign alias from row content.

    Args:
      sheet_row: List of strings representing one row input from the
        spreadsheet.

    Returns:
      String value of the campaign alias or None.
    """
    result = None

    if (
        sheet_row[data_references.Assets.customer_name].strip()
        and sheet_row[data_references.Assets.campaign_name].strip()
    ):
      result = (
          sheet_row[data_references.Assets.customer_name]
          + ";"
          + sheet_row[data_references.Assets.campaign_name]
      )

    return result
