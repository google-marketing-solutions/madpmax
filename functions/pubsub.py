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

from functools import cached_property
from absl import logging
import ads_api
import asset_creation
import asset_group_creation
import auth
import campaign_creation
import data_processing
import data_references
from google.ads.googleads import client
import sheet_api
import sitelink_creation


class PubSub:
  """Main function to call update and refresh for spreadsheet functionality."""

  def __init__(
      self,
      config: data_references.ConfigFile,
      google_ads_client: client.GoogleAdsClient
  ) -> None:
    """Constructs the PubSub instance.

    Args:
        config: JSON formatted configuration data for accessing API.
        google_ads_client: Instance of Google Ads API client.

    Returns:
        None. Initiates instances during the call.
    """
    self.config = config
    self.google_ads_client = google_ads_client

  @cached_property
  def credentials(self):
    return auth.get_credentials_from_file(
        self.config.access_token,
        self.config.refresh_token,
        self.config.client_id,
        self.config.client_secret,
    )

  @cached_property
  def login_customer_id(self):
    return self.config.login_customer_id

  @cached_property
  def google_ads_service(self):
    return ads_api.AdService(self.google_ads_client)

  @cached_property
  def sheet_service(self):
    return sheet_api.SheetsService(
        self.credentials, self.google_ads_client, self.google_ads_service
    )

  @cached_property
  def campaign_service(self):
    return campaign_creation.CampaignService(
        self.google_ads_service, self.sheet_service, self.google_ads_client
    )

  @cached_property
  def asset_service(self):
    return asset_creation.AssetService(
        self.google_ads_client, self.google_ads_service, self.sheet_service
    )

  @cached_property
  def asset_group_service(self):
    return asset_group_creation.AssetGroupService(
        self.google_ads_service,
        self.sheet_service,
        self.asset_service,
        self.google_ads_client,
    )

  @cached_property
  def data_processing_service(self):
    return data_processing.DataProcessingService(
        self.sheet_service,
        self.google_ads_service,
        self.asset_service,
        self.asset_group_service,
    )

  @cached_property
  def sitelink_service(self):
    return sitelink_creation.SitelinkService(
        self.sheet_service, self.google_ads_service, self.google_ads_client
    )

  def refresh_spreadsheet(self) -> None:
    """Requests the overall data from the Ads API and updates the spreadsheet."""
    self.sheet_service.refresh_spreadsheet()

  def refresh_customer_id_list(self) -> None:
    """Requests customer list data from the Ads API and updates the spreadsheet."""
    self.sheet_service.refresh_customer_id_list()

  def refresh_campaign_list(self) -> None:
    """Requests campaign data from the Ads API and updates the spreadsheet."""
    self.sheet_service.refresh_campaign_list()

  def refresh_asset_group_list(self) -> None:
    """Requests asset group data from the Ads API and updates the spreadsheet."""
    self.sheet_service.refresh_asset_group_list()

  def refresh_assets_list(self) -> None:
    """Requests assets data from the Ads API and updates the spreadsheet."""
    self.sheet_service.refresh_assets_list()

  def refresh_sitelinks_list(self) -> None:
    """Requests sitelinks data from the Ads API and updates the spreadsheet."""
    self.sheet_service.refresh_sitelinks_list()

  def create_api_operations(self) -> None:
    """Reads the campaigns and asset groups from the input sheet, creates assets.

    For the assets provided. Removes the provided placeholder assets, and
    writes the results back to the spreadsheet.
    """
    logging.info("Processing NewCampaigns data")
    new_campaign_data = self.sheet_service.get_sheet_values(
        data_references.SheetNames.new_campaigns
        + "!"
        + data_references.SheetRanges.new_campaigns
    )
    logging.info("Processing Sitelink data")
    sitelink_data = self.sheet_service.get_sheet_values(
        data_references.SheetNames.sitelinks
        + "!"
        + data_references.SheetRanges.sitelinks
    )
    logging.info("Processing Assets data")
    asset_data = self.sheet_service.get_sheet_values(
        data_references.SheetNames.assets
        + "!"
        + data_references.SheetRanges.assets
    )
    logging.info("Processing New Asset Groups data")
    new_asset_group_data = self.sheet_service.get_sheet_values(
        data_references.SheetNames.new_asset_groups
        + "!"
        + data_references.SheetRanges.new_asset_groups
    )
    logging.info("Processing Asset Groups data")
    asset_group_data = self.sheet_service.get_sheet_values(
        data_references.SheetNames.asset_groups
        + "!"
        + data_references.SheetRanges.asset_groups
    )
    logging.info("Processing Campaign data")
    campaign_data = self.sheet_service.get_sheet_values(
        data_references.SheetNames.campaigns
        + "!"
        + data_references.SheetRanges.campaigns
    )

    if new_campaign_data:
      logging.info("Creating new Campaigns")
      self.campaign_service.process_campaign_input_sheet(new_campaign_data)

    if new_asset_group_data and campaign_data:
      logging.info("Creating new Asset Groups")
      self.asset_group_service.process_asset_group_data_and_create(
          new_asset_group_data, campaign_data
      )

    if asset_data and asset_group_data:
      logging.info("Creating Assets")
      self.asset_service.process_asset_data_and_create(
          asset_data, asset_group_data
      )

    if sitelink_data and campaign_data:
      logging.info("Creating new Sitelinks")
      self.sitelink_service.process_sitelink_data(sitelink_data, campaign_data)
