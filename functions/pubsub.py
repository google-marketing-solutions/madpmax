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

import ads_api
import asset_creation
import asset_group_creation
import campaign_creation
import data_processing
import sheet_api
import sitelink_creation


class PubSub:
  """Main function to call classes and methods to upload to api."""

  def __init__(self, credentials, google_ads_client):
    self.google_ads_service = ads_api.AdService(google_ads_client)
    self.sheet_service = sheet_api.SheetsService(
        credentials, google_ads_client, self.google_ads_service
    )
    self.campaign_service = campaign_creation.CampaignService(
        self.google_ads_service, self.sheet_service, google_ads_client
    )
    self.asset_service = asset_creation.AssetService(self.google_ads_service)
    self.asset_group_service = asset_group_creation.AssetGroupService(
        self.google_ads_service, self.sheet_service, google_ads_client
    )
    self.data_processing_service = data_processing.DataProcessingService(
        self.sheet_service, self.google_ads_service, self.asset_service,
        self.asset_group_service
    )
    self.sitelink_service = sitelink_creation.SitelinkService(
        self.google_ads_service, self.sheet_service, google_ads_client
    )

  def refresh_spreadsheet(self):
    self.sheet_service.refresh_spreadsheet()

  def refresh_customer_id_list(self):
    self.sheet_service.refresh_customer_id_list()

  def refresh_campaign_list(self):
    self.sheet_service.refresh_campaign_list()

  def refresh_asset_group_list(self):
    self.sheet_service.refresh_asset_group_list()

  def refresh_assets_list(self):
    self.sheet_service.refresh_assets_list()

  def refresh_sitelinks_list(self):
    self.sheet_service.refresh_sitelinks_list()

  def create_api_operations(self, login_customer_id):
    """Reads the campaigns and asset groups from the input sheet, creates assets.

    For the assets provided. Removes the provided placeholder assets, and
    writes the results back to the spreadsheet.

    Args:
      login_customer_id: Google ads customer id.
    """
    # Get Values from input sheet
    new_campaign_data = self.sheet_service.get_sheet_values("NewCampaigns!A6:L")

    # Load new Campaigns Spreadsheet and create campaigns
    self.campaign_service.process_campaign_data_and_create_campaigns(
        new_campaign_data, login_customer_id
    )

    asset_sheet_name = "Assets"
    # Get Values from input sheet
    asset_data = self.sheet_service.get_sheet_values(asset_sheet_name + "!A6:L")
    asset_group_data = self.sheet_service.get_sheet_values(
        "AssetGroupList!A6:F"
    )
    new_asset_group_data = self.sheet_service.get_sheet_values(
        "NewAssetGroups!A6:K"
    )
    campaign_data = self.sheet_service.get_sheet_values("CampaignList!A6:D")
    sitelink_data = self.sheet_service.get_sheet_values("Sitelinks!A6:J")

    (
        asset_operations,
        sheet_results,
        asset_group_sheetlist,
        asset_group_headline_operations,
        asset_group_description_operations,
        row_to_operations_mapping,
        asset_group_operations,
    ) = self.data_processing_service.process_data(
        asset_data, asset_group_data, new_asset_group_data, campaign_data
    )

    if asset_operations:
      # Update Assets only in Google Ads
      self.sheet_service.process_api_operations(
          "ASSETS",
          asset_operations,
          sheet_results,
          row_to_operations_mapping,
          asset_group_sheetlist,
          asset_sheet_name,
      )
    if asset_group_operations:
      # create asset group description api objects.
      descriptions = self.google_ads_service.create_multiple_text_assets(
          asset_group_description_operations
      )
      asset_group_operations, row_to_operations_mapping = (
          self.google_ads_service.compile_asset_group_operations(
              asset_group_operations,
              descriptions,
              "DESCRIPTIONS",
              row_to_operations_mapping,
          )
      )

      # create asset group headlines api objects.
      headlines = self.google_ads_service.create_multiple_text_assets(
          asset_group_headline_operations
      )
      asset_group_operations, row_to_operations_mapping = (
          self.google_ads_service.compile_asset_group_operations(
              asset_group_operations,
              headlines,
              "HEADLINES",
              row_to_operations_mapping,
          )
      )

      self.sheet_service.process_api_operations(
          "ASSET_GROUPS",
          asset_group_operations,
          sheet_results,
          row_to_operations_mapping,
          asset_group_sheetlist,
          asset_sheet_name,
      )

    # Load new Sitelinks Spreadsheet and create Sitelinks
    self.sitelink_service.process_sitelink_data(sitelink_data, campaign_data)
