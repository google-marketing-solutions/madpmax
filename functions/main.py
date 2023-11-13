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
"""Main function, Used to run the mad pMax Creative Management tools."""

import base64
import ads_api
import asset_creation
import auth
from cloudevents.http import CloudEvent
import data_processing
import functions_framework
from google.ads import googleads
import sheet_api
import campaign_creation
import sitelink_creation
import yaml


class main:
  # Input column map, descripting the column names for the input data from the
  # RawData sheet.

  def __init__(self):
    with open("config.yaml", "r") as ymlfile:
      cfg = yaml.safe_load(ymlfile)

    credentials = auth.get_credentials_from_file(
        cfg["access_token"], cfg["refresh_token"],
        cfg["client_id"], cfg["client_secret"]
    )
    self.google_ads_client = googleads.client.GoogleAdsClient.load_from_storage(
        "config.yaml", version="v14")

    # Configuration input values.
    self.sheet_name = "Assets"
    self.google_spread_sheet_id = cfg["spreadsheet_id"]

    self.customer_id = cfg["customer_id"]
    self.login_customer_id = cfg["login_customer_id"]

    self.google_ads_service = ads_api.AdService(self.google_ads_client)
    self.sheet_service = sheet_api.SheetsService(
      credentials, self.google_ads_client, self.google_ads_service)
    self.campaign_service = campaign_creation.CampaignService(
        self.google_ads_service, self.sheet_service, self.google_ads_client)
    self.sitelink_service = sitelink_creation.SitelinkService(
        self.google_ads_service, self.sheet_service, self.google_ads_client)
    self.asset_service = asset_creation.AssetService(self.google_ads_service)
    self.data_processing_service = data_processing.DataProcessingService(
        self.sheet_service, self.google_ads_service, self.asset_service)

  def refresh_spreadsheet(self):
    self.sheet_service.refresh_spreadsheet()

  def create_api_operations(self):
    """Reads the campaigns and asset groups from the input sheet, creates assets.

        For the assets provided. Removes the provided placeholder assets, and
        writes the results back to the spreadsheet.
    """
    # Get Values from input sheet
    new_campaign_data = self.sheet_service.get_sheet_values(
        "NewCampaigns!A6:L")

    # Load new Campaigns Spreadsheet and create campaigns
    self.campaign_service.process_campaign_data_and_create_campaigns(
        new_campaign_data, self.google_spread_sheet_id, self.login_customer_id)

    # Get Values from input sheet
    asset_data = self.sheet_service.get_sheet_values(
        self.sheet_name + "!A6:L")
    asset_group_data = self.sheet_service.get_sheet_values(
        "AssetGroupList!A6:F")
    new_asset_group_data = self.sheet_service.get_sheet_values(
        "NewAssetGroups!A6:K")
    campaign_data = self.sheet_service.get_sheet_values(
        "CampaignList!A6:D")
    sitelink_data = self.sheet_service.get_sheet_values(
        "Sitelinks!A6:J")

    (asset_operations, sheet_results, asset_group_sheetlist,
        asset_group_headline_operations, asset_group_description_operations,
        row_to_operations_mapping, asset_group_operations
     ) = self.data_processing_service.process_data(
        asset_data, asset_group_data, new_asset_group_data,
        campaign_data
    )

    if len(asset_operations) > 0:
      # Update Assets only in Google Ads
      self.sheet_service.process_api_operations(
          "ASSETS", asset_operations, sheet_results, row_to_operations_mapping,
          asset_group_sheetlist, self.sheet_name)
    if len(asset_group_operations) > 0:
      # create asset group description api objects.
      descriptions = self.google_ads_service.create_multiple_text_assets(
          asset_group_description_operations)
      asset_group_operations, row_to_operations_mapping = (
          self.google_ads_service.compile_asset_group_operations(
              asset_group_operations, descriptions, "DESCRIPTIONS",
              row_to_operations_mapping))

      # create asset group headlines api objects.
      headlines = self.google_ads_service.create_multiple_text_assets(
          asset_group_headline_operations)
      asset_group_operations, row_to_operations_mapping = (
          self.google_ads_service.compile_asset_group_operations(
              asset_group_operations, headlines, "HEADLINES",
              row_to_operations_mapping))

      self.sheet_service.process_api_operations(
          "ASSET_GROUPS", asset_group_operations, sheet_results,
          row_to_operations_mapping, asset_group_sheetlist, self.sheet_name)

    # Load new Sitelinks Spreadsheet and create Sitelinks
    self.sitelink_service.process_sitelink_data(sitelink_data, campaign_data)


@functions_framework.cloud_event
def pmax_trigger(cloud_event: CloudEvent):
  """Listener function for pubsub trigger.

  Based on trigger message activate corresponding mad Max
  function.

  Args:
    cloud_event: Cloud event class for pubsub event.
  """
  if cloud_event:
    # Print out the data from Pub/Sub, to prove that it worked
    print("------- START " +
          base64.b64decode(cloud_event.data["message"]["data"]).decode() +
          " EXECUTION -------")

    cp = main()
    message_data = base64.b64decode(
        cloud_event.data["message"]["data"]).decode()
    if message_data == "REFRESH":
      cp.refresh_spreadsheet()
    elif message_data == "UPLOAD":
      cp.create_api_operations()

    print("------- END " +
          base64.b64decode(cloud_event.data["message"]["data"]).decode() +
          " EXECUTION -------")


if __name__ == "__main__":
  # GoogleAdsClient will read the google-ads.yaml configuration file in the
  # home directory if none is specified.
  pmax_operations = main()
  pmax_operations.refresh_spreadsheet()
  pmax_operations.create_api_operations()
