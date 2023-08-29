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
    self.googleAdsClient = (
        googleads.client.GoogleAdsClient.load_from_storage(
            "config.yaml", version="v14"
        )
    )

    # Configuration input values.
    self.includeVideo = False
    self.sheetName = "Assets"
    self.googleSpreadSheetId = cfg["spreadsheet_id"]
    self.googleCustomerId = cfg["customer_id"]

    self.sheetService = sheet_api.SheetsService(credentials)
    self.googleAdsService = ads_api.AdService("config.yaml")
    self.campaignService = campaign_creation.CampaignService(
        self.googleAdsService, self.sheetService, self.googleAdsClient
    )
    self.assetService = asset_creation.AssetService()
    self.dataProcessingService = data_processing.DataProcessingService(self.sheetService, self.googleAdsService, self.assetService)

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

    customer_id, asset_operations, sheet_results, asset_group_sheetlist, asset_group_headline_operations, asset_group_description_operations, row_to_operations_mapping, asset_group_operations = self.dataProcessingService.process_data(asset_values, asset_group_values, new_asset_group_values, campaign_values) 
    
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
