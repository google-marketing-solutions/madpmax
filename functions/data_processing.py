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
"""Provides functionality to create campaigns."""

from enums.asset_column_map import assetsColumnMap
from enums.asset_group_list_column_map import assetGroupListColumnMap
from enums.campaign_list_column_map import campaignListColumnMap
from enums.new_asset_groups_column_map import newAssetGroupsColumnMap


class DataProcessingService:
  """Class for processing sheet input data.

  Takes input data from the spreadsheet and processes the request in
  the correct order.
  """

  def __init__(self, sheet_service, google_ads_service, asset_service,
               asset_group_service):
    """Constructs the CampaignService instance.

    Args:
      sheet_service: instance of sheet_service for dependancy injection.
      google_ads_service: instance of the google_ads_service for dependancy
        injection.
      asset_service: instance of the asset_service for dependency injection.
      asset_group_service: instance of the asset_group_service for
      dependency injection.
    """
    self.sheet_service = sheet_service
    self.google_ads_service = google_ads_service
    self.asset_service = asset_service
    self.asset_group_service = asset_group_service

  def process_data(self, asset_values, asset_group_values,
                   new_asset_group_values, campaign_values):
    """Process data from spreadsheets to create mutation objects.

    Args:
      asset_values: Values from Assets spreadsheet page to create in Asset
        mutate object.
      asset_group_values: Values from exisitng AsseGrpup spreadsheet page.
      new_asset_group_values: Values from new Asset Group spreadsheet page to
        create AssetGroup muatte object.
      campaign_values: Values from exisitng Campaing spreadsheet page.

    Returns:
      customer_id: Google Ads customer id.
      asset_operations: Api operations list for Google Ads API, with all 
          assets.
      sheet_results: Object containing off results output for sheet.
      asset_group_sheetlist: Output oject with Asset group sheet output.
      asset_group_headline_operations: Api operations list for Google Ads 
          API, with all asset group headlines.
      asset_group_description_operations: Api operations list for Google
          Ads API, with all asset group descriptions.
      row_to_operations_mapping: Object with mapping between API operations
          and sheet.
      asset_group_operations: Api operations list for Google Ads API, with all
          asset groups.
    """
    # all operations across multiple assetGroups where the key is an assetGroup
    asset_operations = {}
    asset_group_operations = {}
    asset_group_headline_operations = {}
    asset_group_description_operations = {}
    asset_group_sheetlist = {}
    sheet_row_index = 0
    # The map used to store all the API results and error messages.
    sheet_results = {}

    # map to link sheet input rows to the asset operations for status and error
    # handling.
    row_to_operations_mapping = {}
    customer_id = None

    # Loop through of the input values in the provided spreadsheet / sheet.
    for row in asset_values:
      new_asset_group = False
      mutate_operations = []
      asset_group_details = None

      # Skip to next row in case Status is Success.
      if (row[assetsColumnMap.ASSET_STATUS] != "UPLOADED" and
          len(row) > assetsColumnMap.ASSET_TEXT):

        asset_group_alias = self.compile_asset_group_alias(row)

        if (asset_group_alias):
          # Use the Asset Group Alias to get Asset Group info from
          # the Google sheet.
          asset_group_details = self.sheet_service.get_sheet_row(
              asset_group_alias, asset_group_values, "ASSET_GROUP")

          if asset_group_details:
            asset_group_id = asset_group_details[
                assetGroupListColumnMap.ASSET_GROUP_ID
            ]
            customer_id = asset_group_details[
                assetGroupListColumnMap.CUSTOMER_ID]

            # Construct the the API operations dictionary to store all the api
            # operations for bulk processing.
            if customer_id not in asset_operations:
              asset_operations[customer_id] = {}
            if asset_group_alias not in asset_operations[customer_id]:
              asset_operations[customer_id][asset_group_alias] = []

          # Check if Asset Group already exists in Google Ads. If not create
          # Asset Group operation.
          elif not asset_group_details:
            new_asset_group = True
            # GENERATE ASSET GROUP OPERATION.
            new_asset_group_details = self.sheet_service.get_sheet_row(
                asset_group_alias, new_asset_group_values, "NEW_ASSET_GROUP")

            campaign_alias = self.compile_campaign_alias(row)

            campaign_details = self.sheet_service.get_sheet_row(
                campaign_alias, campaign_values, "CAMPAIGN")

            if campaign_details and new_asset_group_details:
              customer_id = campaign_details[campaignListColumnMap.CUSTOMER_ID]
              campaign_id = campaign_details[campaignListColumnMap.CAMPAIGN_ID]

              # Construct the the API operations dictionary to store all the
              # api operations for bulk processing.
              if customer_id not in asset_group_operations:
                asset_group_operations[customer_id] = {}
                asset_group_headline_operations[customer_id] = {}
                asset_group_description_operations[customer_id] = {}

              if asset_group_alias not in asset_group_operations[customer_id]:
                asset_group_operations[customer_id][asset_group_alias] = []
                asset_group_headline_operations[
                    customer_id][asset_group_alias] = []
                asset_group_description_operations[
                    customer_id][asset_group_alias] = []

                asset_group_mutate_operation, asset_group_id = (
                    self.asset_group_service.create_asset_group(
                        new_asset_group_details, campaign_id, customer_id
                    )
                )

                if asset_group_mutate_operation:

                  mutate_operations.append(asset_group_mutate_operation)

                  # Create AssetGroupList Sheet array.
                  asset_group_sheetlist[asset_group_alias] = [
                      new_asset_group_details[
                          newAssetGroupsColumnMap.CUSTOMER_NAME],
                      customer_id,
                      new_asset_group_details[
                          newAssetGroupsColumnMap.CAMPAIGN_NAME],
                      campaign_id,
                      new_asset_group_details[
                          newAssetGroupsColumnMap.ASSET_GROUP_NAME],
                      asset_group_id,
                  ]

          # Check if sheet results for the input sheet row already exists. If
          # not create a new empty map.
          if sheet_row_index not in sheet_results:
            sheet_results[sheet_row_index] = {}

          # Preset the default map values for Status and Message.
          sheet_results[sheet_row_index]["status"] = None
          sheet_results[sheet_row_index]["message"] = None
          sheet_results[sheet_row_index]["asset_group_asset"] = None

          # Asset name / asset type
          asset_type = row[assetsColumnMap.ASSET_TYPE]

          operations, asset_resource = (
              self.asset_service.create_asset_mutation(
                  row, customer_id, asset_group_id, new_asset_group)
              )

          mutate_operations.extend(operations)

          # Check if asset operation for the Asset Group already exists.
          # If not create a new list.
          if not new_asset_group:
            asset_operations[
                customer_id][asset_group_alias] += mutate_operations
          elif new_asset_group:
            if asset_type == "HEADLINE":
              asset_group_headline_operations[
                  customer_id][asset_group_alias].append(operations[0])
            if asset_type == "DESCRIPTION":
              asset_group_description_operations[
                  customer_id][asset_group_alias].append(operations[0])
            asset_group_operations[
                customer_id][asset_group_alias] += mutate_operations

          # Add reource name index and sheet row number to map, for
          # processing error and status messages to sheet.
          row_to_operations_mapping[asset_resource] = [sheet_row_index]

      sheet_row_index += 1

    return (
        asset_operations,
        sheet_results,
        asset_group_sheetlist,
        asset_group_headline_operations,
        asset_group_description_operations,
        row_to_operations_mapping,
        asset_group_operations
    )

  def compile_asset_group_alias(self, sheet_row):
    """Helper method to compile asset group alias from row content.

    Args:
      sheet_row: List of strings representing one row input from the
          spreadsheet.

    Returns:
      String value of the asset group alias or None.
    """
    result = None

    if(sheet_row[assetsColumnMap.CUSTOMER_NAME].strip() and
       sheet_row[assetsColumnMap.CAMPAIGN_NAME].strip() and
       sheet_row[assetsColumnMap.ASSET_GROUP_NAME].strip()):
      result = (sheet_row[assetsColumnMap.CUSTOMER_NAME] + ";" +
                sheet_row[assetsColumnMap.CAMPAIGN_NAME] + ";" +
                sheet_row[assetsColumnMap.ASSET_GROUP_NAME])

    return result

  def compile_campaign_alias(self, sheet_row):
    """Helper method to compile campaign alias from row content.

    Args:
      sheet_row: List of strings representing one row input from the
          spreadsheet.

    Returns:
      String value of the campaign alias or None.
    """
    result = None

    if(sheet_row[assetsColumnMap.CUSTOMER_NAME].strip() and
       sheet_row[assetsColumnMap.CAMPAIGN_NAME].strip()):
      result = (sheet_row[assetsColumnMap.CUSTOMER_NAME] + ";" +
                sheet_row[assetsColumnMap.CAMPAIGN_NAME])

    return result


