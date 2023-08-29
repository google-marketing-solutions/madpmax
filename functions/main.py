import base64
import ads_api
import auth
import campaign_creation
from cloudevents.http import CloudEvent
import functions_framework
from google.ads import googleads
import sheet_api
import yaml
import asset_creation
from enums.asset_column_map import assetsColumnMap
from enums.asset_group_list_column_map import assetGroupListColumnMap 
from enums.new_asset_groups_column_map import newAssetGroupsColumnMap
from enums.campaign_list_column_map import campaignListColumnMap
import data_processing


class main:

  # Input column map, descripting the column names for the input data from the
  # RawData sheet.
  def __init__(self):
    with open("config.yaml", "r") as ymlfile:
      cfg = yaml.safe_load(ymlfile)

    credentials = auth.get_credentials_from_file(
        cfg["oauth_token"],
        cfg["refresh_token"],
        cfg["client_id"],
        cfg["client_secret"]
    )

    # Configuration input values.
    self.includeVideo = False
    self.sheetName = "Assets"
    self.googleSpreadSheetId = cfg["spreadsheet_id"]
    self.googleCustomerId = cfg["customer_id"]

    self.sheetService = sheet_api.SheetsService(credentials)
    self.googleAdsService = ads_api.AdService("config.yaml")
    self.campaignService = campaign_creation.CampaignService(
        "config.yaml", self.googleAdsService, self.sheetService
    )
    self.assetService = asset_creation.AssetService()

  def refresh_spreadsheet(self):
      self.sheetService.refresh_spreadsheet()  


  def create_api_operations(self):
    """TODO 
    Reads the campaigns and asset groups from the input sheet, creates assets
    for the assets provided. Removes the provided placeholder assets, and writes
    the results back to the spreadsheet."""
    # Get Values from input sheet
    asset_values = self.sheetService._get_sheet_values(
        self.sheetName + "!A6:G", self.googleSpreadSheetId
    )
    asset_group_values = self.sheetService._get_sheet_values(
        "AssetGroupList!A6:H", self.googleSpreadSheetId
    )
    new_asset_group_values = self.sheetService._get_sheet_values(
        "NewAssetGroups!A6:J", self.googleSpreadSheetId
    )
    campaign_values = self.sheetService._get_sheet_values(
        "CampaignList!A6:E", self.googleSpreadSheetId
    )
    new_campaign_data = self.sheetService._get_sheet_values(
        "NewCampaigns!A6:M", self.googleSpreadSheetId
    )

    # Load new Campaigns Spreadsheet and create campaigns
    self.campaignService._process_campaign_data_and_create_campaigns(
        new_campaign_data, self.googleSpreadSheetId, self.googleCustomerId
    )

    # all operations across multiple assetGroups where the key is an assetGroup
    asset_operations = {}
    asset_group_operations = {}
    asset_group_headline_operations = {}
    asset_group_description_operations = {}
    asset_group_sheetlist = {}

    # The map used to store all the API results and error messages.
    sheet_results = {}

    # map to link sheet input rows to the asset operations for status and error handling.
    row_to_operations_mapping = {}
    sheet_row_index = 0
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
      ] in ("UPLOADED", "GOOGLE ADS"):
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

    if customer_id:
      # Update Assets only in Google Ads
      self.sheetService.process_api_operations(
          "ASSETS",
          asset_operations,
          sheet_results,
          row_to_operations_mapping,
          asset_group_sheetlist,
          customer_id,
          self.googleSpreadSheetId,
          self.sheetName
      )

      # Create a new Asset Group and Update Assets.
      headlines = self.googleAdsService._create_multiple_text_assets(
          asset_group_headline_operations, customer_id
      )
      descriptions = self.googleAdsService._create_multiple_text_assets(
          asset_group_description_operations, customer_id
      )
      asset_group_operations, row_to_operations_mapping = (
          self.googleAdsService.compile_asset_group_operations(
              asset_group_operations,
              headlines,
              descriptions,
              row_to_operations_mapping,
              customer_id
          )
      )
      self.sheetService.process_api_operations(
          "ASSET_GROUPS",
          asset_group_operations,
          sheet_results,
          row_to_operations_mapping,
          asset_group_sheetlist,
          customer_id,
          self.googleSpreadSheetId,
          self.sheetName
      )

# Triggered from a message on a Cloud Pub/Sub topic.
@functions_framework.cloud_event
def pubSubEntry(cloud_event: CloudEvent) -> None:
  if cloud_event:
    # Print out the data from Pub/Sub, to prove that it worked
    print(
        "------- START "
        + base64.b64decode(cloud_event.data["message"]["data"]).decode()
        + " EXECUTION -------"
    )

    cp = main()
    message_data = base64.b64decode(
        cloud_event.data["message"]["data"]
    ).decode()
    if message_data == "REFRESH":
      cp.refresh_spreadsheet()
    elif message_data == "UPLOAD":
      cp.create_api_operations()

    print(
        "------- END "
        + base64.b64decode(cloud_event.data["message"]["data"]).decode()
        + " EXECUTION -------"
    )
