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
"""Module containing all data mappings.

Mad pMax works with a spreadsheet as data source, when changes are made to the
spreadsheet template, or sheetnames, they need to be updated here.
"""
import dataclasses


@dataclasses.dataclass()
class ConfigFile:
  """Instance with mapping of the config file.

  Attributes:
    use_proto_plus: Whether or not to use proto-plus messages.
    developer_token: Developer token from Google Ads MCC level.
    client_id: OAuth cleint id.
    client_secret: OAuth secret.
    access_token: Access token for Google Ads API access.
    refresh_token: Refresh token for Google Ads API access.
    login_customer_id: Google Ads customer id of MCC level.
    customer_id: Google Ads customer id under MCC level.
    spreadsheet_id: Id of spreadsheet to work with. Consist of numbers and
        letters. Eg take form the link to your template spreadsheet
        https://docs.google.com/spreadsheets/d/{spreadsheet_id}
  """
  use_proto_plus: bool
  developer_token: str
  client_id: str
  client_secret: str
  access_token: str
  refresh_token: str
  login_customer_id: int
  customer_id: int
  spreadsheet_id: str


@dataclasses.dataclass(frozen=True)
class SheetNames:
  """A mapping of the sheetnames in input spreadsheet.

  Mad pMax relies on sheetnames to collect the input data, send it to the API
  and write status back to the sheet. This enum ensures a correct mapping to
  sheetnames, maintained from one single place.

  Atrributes:
    customers: Sheetname in spreadsheet containing customer details.
    campaigns: Sheetname in spreadsheet containing campaign details.
    new_campaigns: Sheetname in spreadsheet containing campaign input.
    asset_groups: Sheetname in spreadsheet containing asset group details.
    new_asset_groups: Sheetname in spreadsheet containing campaign input.
    sitelinks: Sheetname in spreadsheet containing sitelinks details and input.
    assets: Sheetname in spreadsheet containing assets details and input.
  """
  customers: str = "CustomerList"
  campaigns: str = "CampaignList"
  new_campaigns: str = "NewCampaigns"
  asset_groups: str = "AssetGroupList"
  new_asset_groups: str = "NewAssetGroups"
  sitelinks: str = "Sitelinks"
  assets: str = "Assets"


@dataclasses.dataclass(frozen=True)
class SheetRanges:
  """A mapping of the sheet ranges in input spreadsheet.

  Mad pMax relies on ranges on the sheet to collect the input data, send it to
  the API and write status back to the sheet. This enum ensures a correct column
  reference, maintained from one single place.

  Atrributes:
    customers: Range in spreadsheet containing customer details.
    campaigns: Range in spreadsheet containing campaign details.
    new_campaigns: Range in spreadsheet containing campaign input.
    asset_groups: Range in spreadsheet containing asset group details.
    new_asset_groups: Range in spreadsheet containing campaign input.
    sitelinks: Range in spreadsheet containing sitelinks details and input.
    assets: Range in spreadsheet containing assets details and input.
  """
  customers: str = "A6:B"
  campaigns: str = "A6:D"
  new_campaigns: str = "A6:L"
  asset_groups: str = "A6:F"
  new_asset_groups: str = "A6:T"
  sitelinks: str = "A6:J"
  assets: str = "A6:L"


@dataclasses.dataclass(frozen=True)
class NewCampaigns:
  """Column map for newCampaigns sheet.

  Spreadsheet API returns a list of lists when retrieving data from a sheet.
  Column ids are needed to read and write the correct data  fields from the
  sheet. This class provides a mapping from column names to column ids. In case
  the sheet get's edited the tool can be updated from this single place.

  Atrributes:
    campaign_upload_status: Column reference with the upload status.
    customer_name: Column reference with the customer name.
    campaign_name: Column reference with the campaign name.
    campaign_budget: Column reference with the campaign budget.
    budget_delivery_method: Column reference with the budget delivery method.
    campaign_status: Column reference with the campaign status.
    bidding_strategy: Column reference with the bidding strategy.
    campaign_target_roas: Column reference with the target roas goal.
    campaign_target_cpa: Column reference with the target cpa goal.
    campaign_start_date: Column reference with the start date of the campaign.
    campaign_end_date: Column reference with the end date of the campaign.
    error_message: Column reference with the error message.
  """
  campaign_upload_status: int = 0
  customer_name: int = 1
  campaign_name: int = 2
  campaign_budget: int = 3
  budget_delivery_method: int = 4
  campaign_status: int = 5
  bidding_strategy: int = 6
  campaign_target_roas: int = 7
  campaign_target_cpa: int = 8
  campaign_start_date: int = 9
  campaign_end_date: int = 10
  error_message: int = 11


@dataclasses.dataclass(frozen=True)
class CustomerList:
  """Column map for customerList sheet.

  Spreadsheet API returns a list of lists when retrieving data from a sheet.
  Column ids are needed to read and write the correct data  fields from the
  sheet. This class provides a mapping from column names to column ids. In case
  the sheet get's edited the tool can be updated from this single place.

  Atrributes:
    customer_name: Column ID for customer name in the CustomerList sheet.
    customer_id: Column ID for customer id in the CustomerList sheet.
  """
  customer_name: int = 0
  customer_id: int = 1


@dataclasses.dataclass(frozen=True)
class RowStatus:
  """Map for the status of a sheet row.

  The status can be either set to "UPLOADED" or "ERROR", depending on the
  API request status for the input row.

  Atrributes:
    uploaded: Successfully uploaded to Google Ads.
    error: Error occured during processing.
  """
  uploaded: str = "UPLOADED"
  error: str = "ERROR"


@dataclasses.dataclass(frozen=True)
class ApiStatus:
  """Map for the status of an item e.g. campaign in Google Ads.

  The status can be either set to "ENABLED" or "PAUSED".

  Atrributes:
    paused: Google Ads entity is paused from serving impressions.
    enabled: Google Ads entity is enabled to serve impressions.
  """
  paused: str = "PAUSED"
  enabled: str = "ENABLED"
