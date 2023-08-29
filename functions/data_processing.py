"""Provides functionality to create campaigns."""

from enums.asset_column_map import assetsColumnMap
from enums.asset_group_list_column_map import assetGroupListColumnMap 
from enums.new_asset_groups_column_map import newAssetGroupsColumnMap
from enums.campaign_list_column_map import campaignListColumnMap
from enums.asset_status import assetStatus

class DataProcessingService:

  def __init__(self, sheet_service, googleAdsService, assetService):
    """Constructs the CampaignService instance.

    Args:
      ads_account_file: Path to Google Ads API account file.
      googleAdsService: instance of the googleAdsService for dependancy
        injection.
      sheetService: instance of sheetService for dependancy injection.
    """
    self.sheetService = sheet_service
    self.googleAdsService = googleAdsService
    self.assetService = assetService
    

  def process_data(
      self,
      asset_values,
      asset_group_values,
      new_asset_group_values,
      campaign_values

  ):
    """TODO
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

    # map to link sheet input rows to the asset operations for status and error handling.
    row_to_operations_mapping = {}
    customer_id = None
    # TODO FIGURE OUT A WAY TO HANDLE MULTIPLE CUSTOMER IDS.

    # Loop through of the input values in the provided spreadsheet / sheet.
    for row in asset_values:
      new_asset_group = False
      mutate_operations = []
      asset_group_details = None

      # Skip to next row in case Status is Success.
      if assetsColumnMap.ASSET_STATUS < len(row) and row[
          assetsColumnMap.ASSET_STATUS
      ] in (assetStatus.UPLOADED.value[0], assetStatus.GOOGLE_ADS.value[0]):
        sheet_row_index += 1
        continue

      asset_group_alias = row[assetsColumnMap.ASSET_GROUP_ALIAS]

      if not asset_group_alias:
        continue

      # Use the Asset Group Alias to get Asset Group info from the Google sheet.
      asset_group_details = self.sheetService._get_sheet_row(
          row[assetsColumnMap.ASSET_GROUP_ALIAS],
          asset_group_values,
          assetGroupListColumnMap.ASSET_GROUP_ALIAS.value
      )

      if asset_group_details:
        asset_group_id = asset_group_details[
            assetGroupListColumnMap.ASSET_GROUP_ID
        ]
        customer_id = asset_group_details[
            assetGroupListColumnMap.CUSTOMER_ID
        ]

        if asset_group_alias not in asset_operations:
          asset_operations[asset_group_alias] = []

      # Check if Asset Group already exists in Google Ads. If not create Asset Group operation.
      elif not asset_group_details:
        new_asset_group = True
        # GENERATE ASSET GROUP OPERATION.
        new_asset_group_details = self.sheetService._get_sheet_row(
            row[assetsColumnMap.ASSET_GROUP_ALIAS],
            new_asset_group_values,
            newAssetGroupsColumnMap.ASSET_GROUP_ALIAS.value
        )

        campaign_details = self.sheetService._get_sheet_row(
            new_asset_group_details[
                newAssetGroupsColumnMap.CAMPAIGN_ALIAS
            ],
            campaign_values,
            campaignListColumnMap.CAMPAIGN_NAME.value,
        )

        if not campaign_details or not new_asset_group_details:
          continue

        customer_id = campaign_details[campaignListColumnMap.CUSTOMER_ID]
        campaign_id = campaign_details[campaignListColumnMap.CAMPAIGN_ID]

        if asset_group_alias not in asset_group_operations:
          asset_group_operations[asset_group_alias] = []
          asset_group_headline_operations[asset_group_alias] = []
          asset_group_description_operations[asset_group_alias] = []
          asset_group_mutate_operation, asset_group_id = (
              self.googleAdsService._create_asset_group(
                  new_asset_group_details, campaign_id, customer_id
              )
          )
          mutate_operations.append(asset_group_mutate_operation)

          # Create AssetGroupList Sheet array.
          asset_group_sheetlist[asset_group_alias] = [
              asset_group_alias,
              new_asset_group_details[
                  newAssetGroupsColumnMap.ASSET_GROUP_NAME
              ],
              asset_group_id
          ] + campaign_details[1:]

      # Check if sheet results for the input sheet row already exists. If not create a new empty map.
      if sheet_row_index not in sheet_results:
        sheet_results[sheet_row_index] = {}

      # Preset the default map values for Status and Message.
      sheet_results[sheet_row_index]["status"] = None
      sheet_results[sheet_row_index]["message"] = None
      sheet_results[sheet_row_index]["asset_group_asset"] = None

      # Asset name / asset type
      asset_type = row[assetsColumnMap.ASSET_TYPE]

      operations, asset_resource = self.assetService._create_asset_mutation(row, customer_id, asset_group_id, new_asset_group)  
      mutate_operations.extend(operations)

      # Check if asset operation for the Asset Group already exists. If not create a new list.
      # TODO: check the asset_creation_operation part
      if not new_asset_group:
        asset_operations[asset_group_alias] += mutate_operations
      elif new_asset_group:
        if asset_type == "HEADLINE":
          asset_group_headline_operations[asset_group_alias].append(
              operations[0]
          )
        if asset_type == "DESCRIPTION":
          asset_group_description_operations[asset_group_alias].append(
              operations[0]
          )
        asset_group_operations[asset_group_alias] += mutate_operations

      # Add reource name index and sheet row number to map, for processing error and status messages to sheet.
      row_to_operations_mapping[asset_resource] = sheet_row_index

      sheet_row_index += 1

    return customer_id, asset_operations, sheet_results, asset_group_sheetlist, asset_group_headline_operations, asset_group_description_operations, row_to_operations_mapping, asset_group_operations    