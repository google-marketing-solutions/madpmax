import base64
import ads_api
import asset_creation
import auth
import campaign_creation
from cloudevents.http import CloudEvent
import data_processing
import functions_framework
from google.ads import googleads
import sheet_api
import yaml


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
        cfg["client_secret"],
    )
    self.google_ads_client = googleads.client.GoogleAdsClient.load_from_storage(
        "config.yaml", version="v14"
    )

    # Configuration input values.
    self.includeVideo = False
    self.sheet_name = "Assets"
    self.google_spread_sheet_id = cfg["spreadsheet_id"]
    self.google_customer_id = cfg["customer_id"]

    self.google_ads_service = ads_api.AdService(self.google_ads_client)
    self.sheet_service = sheet_api.SheetsService(
        credentials, self.google_ads_service
    )
    self.campaign_service = campaign_creation.CampaignService(
        self.google_ads_service, self.sheet_service, self.google_ads_client
    )
    self.asset_service = asset_creation.AssetService(self.google_ads_service)
    self.data_processing_service = data_processing.DataProcessingService(
        self.sheet_service, self.google_ads_service, self.asset_service
    )

  def refresh_spreadsheet(self):
    self.sheet_service.refresh_spreadsheet()

  def create_api_operations(self):
    """Reads the campaigns and asset groups from the input sheet, creates assets

    for the assets provided. Removes the provided placeholder assets, and writes
    the results back to the spreadsheet.
    """
    # Get Values from input sheet
    asset_values = self.sheet_service.get_sheet_values(
        self.sheet_name + "!A6:G", self.google_spread_sheet_id
    )
    asset_group_values = self.sheet_service.get_sheet_values(
        "AssetGroupList!A6:H", self.google_spread_sheet_id
    )
    new_asset_group_values = self.sheet_service.get_sheet_values(
        "NewAssetGroups!A6:J", self.google_spread_sheet_id
    )
    campaign_values = self.sheet_service.get_sheet_values(
        "CampaignList!A6:E", self.google_spread_sheet_id
    )
    new_campaign_data = self.sheet_service.get_sheet_values(
        "NewCampaigns!A6:M", self.google_spread_sheet_id
    )

    # Load new Campaigns Spreadsheet and create campaigns
    self.campaign_service.process_campaign_data_and_create_campaigns(
        new_campaign_data, self.google_spread_sheet_id, self.google_customer_id
    )

    (
        customer_id,
        asset_operations,
        sheet_results,
        asset_group_sheetlist,
        asset_group_headline_operations,
        asset_group_description_operations,
        row_to_operations_mapping,
        asset_group_operations,
    ) = self.data_processing_service.process_data(
        asset_values,
        asset_group_values,
        new_asset_group_values,
        campaign_values,
        self.google_spread_sheet_id,
    )

    if customer_id:
      # Update Assets only in Google Ads
      self.sheet_service.process_api_operations(
          "ASSETS",
          asset_operations,
          sheet_results,
          row_to_operations_mapping,
          asset_group_sheetlist,
          customer_id,
          self.google_spread_sheet_id,
          self.sheet_name,
      )

      # Create a new Asset Group and Update Assets.
      headlines = self.google_ads_service.create_multiple_text_assets(
          asset_group_headline_operations, customer_id
      )
      descriptions = self.google_ads_service.create_multiple_text_assets(
          asset_group_description_operations, customer_id
      )
      asset_group_operations, row_to_operations_mapping = (
          self.google_ads_service.compile_asset_group_operations(
              asset_group_operations,
              headlines,
              descriptions,
              row_to_operations_mapping,
              customer_id,
          )
      )
      self.sheet_service.process_api_operations(
          "ASSET_GROUPS",
          asset_group_operations,
          sheet_results,
          row_to_operations_mapping,
          asset_group_sheetlist,
          customer_id,
          self.google_spread_sheet_id,
          self.sheet_name,
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


if __name__ == "__main__":
  # GoogleAdsClient will read the google-ads.yaml configuration file in the
  # home directory if none is specified.
  cp = main()
  cp.refresh_spreadsheet()
  cp.create_api_operations()
