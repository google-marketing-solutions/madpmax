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
import enum


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
    customer_id_inclusion_list: String representation of list of Google Ads
          customer ids.
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
  customer_id_inclusion_list: str
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
  eu_political_ads: int = 11
  error_message: int = 12


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
class CampaignList:
  """Column map for campaignList sheet.

  Spreadsheet API returns a list of lists when retrieving data from a sheet.
  Column ids are needed to read and write the correct data  fields from the
  sheet. This class provides a mapping from column names to column ids. In case
  the sheet get's edited the tool can be updated from this single place.

  Atrributes:
    customer_name: Column ID for customer name in the CustomerList sheet.
    customer_id: Column ID for customer id in the CustomerList sheet.
    campaign_name: Column ID for customer name in the CustomerList sheet.
    campaign_id: Column ID for customer id in the CustomerList sheet.
  """
  customer_name: int = 0
  customer_id: int = 1
  campaign_name: int = 2
  campaign_id: int = 3


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


@dataclasses.dataclass(frozen=True)
class EuPoliticalAds:
  """Map for the eu political ads policy flag of an campaign.

  The status can be either set to "CONTAINS_EU_POLITICAL_ADVERTISING" or 
  "DOES_NOT_CONTAIN_EU_POLITICAL_ADVERTISING".

  Atrributes:
    yes: Campaign contains EU political ads.
    no: Campaign does not contain EU political ads.
  """
  yes: str = "CONTAINS_EU_POLITICAL_ADVERTISING"
  no: str = "DOES_NOT_CONTAIN_EU_POLITICAL_ADVERTISING"


@dataclasses.dataclass(frozen=True)
class Assets:
  """Map for the columns of Assets sheet.

  Spreadsheet API returns a list of lists when retrieving data from a sheet.
  Column ids are needed to read and write the correct data  fields from the
  sheet. This class provides a mapping from column names to column ids. In case
  the sheet get's edited the tool can be updated from this single place.

  Atrributes:
    status: Column reference with the upload status.
    delete_asset: Column reference for the delete option.
    customer_name: Column reference with the customer name.
    campaign_name: Column reference with the campaign name.
    asset_group_name: Column reference with the asset group name.
    type: Column reference with the type.
    asset_text: Column reference with the asset text.
    asset_call_to_action: Column reference with the call to action for the
        asset.
    asset_url: Column reference with the asset url.
    asset_thumbnail: Column reference with the asset thumbnail.
    error_message: Column reference with the error message.
    asset_group_asset: Column reference with the asset group asset.
  """
  status: int = 0
  delete_asset: int = 1
  customer_name: int = 2
  campaign_name: int = 3
  asset_group_name: int = 4
  type: int = 5
  asset_text: int = 6
  asset_call_to_action: int = 7
  asset_url: int = 8
  asset_thumbnail: int = 9
  error_message: int = 10
  asset_group_asset: int = 11


@dataclasses.dataclass(frozen=True)
class AssetTypes:
  """A mapping of the asset type input spreadsheet.

  Mad pMax asset creation requires specific asset types. This enum ensures a 
  correct mapping to asset types, maintained from one single place.

  Atrributes:
    marketing_image: Asset type for marketing image.
    square_image: Asset type for square image.
    portrait_marketing_image: Asset type for portrait marketing image.
    square_logo: Asset type for square logo.
    landscape_logo: Asset type for landscape logo.
    youtube_video: Asset type for youtube video.
    headline: Asset type for headline.
    description: Asset type for description.
    long_headline: Asset type for long headline.
    business_name: Asset type for business name.
    call_to_action: Asset type for call to action.
    sitelink: Asset type for sitelink.
  """
  marketing_image: str = "MARKETING_IMAGE"
  square_image: str = "SQUARE_MARKETING_IMAGE"
  portrait_marketing_image: str = "PORTRAIT_MARKETING_IMAGE"
  square_logo: str = "LOGO"
  landscape_logo: str = "LANDSCAPE_LOGO"
  youtube_video: str = "YOUTUBE_VIDEO"
  headline: str = "HEADLINE"
  description: str = "DESCRIPTION"
  long_headline: str = "LONG_HEADLINE"
  business_name: str = "BUSINESS_NAME"
  call_to_action: str = "CALL_TO_ACTION_SELECTION"
  sitelink: str = "SITELINK"


@dataclasses.dataclass(frozen=True)
class AssetGroupList:
  """Map for the columns of AssetGroupList sheet.

  Spreadsheet API returns a list of lists when retrieving data from a sheet.
  Column ids are needed to read and write the correct data  fields from the
  sheet. This class provides a mapping from column names to column ids. In case
  the sheet get's edited the tool can be updated from this single place.

  Atrributes:
    customer_name: Column reference with the customer name.
    customer_id: Column reference with the customer id.
    campaign_name: Column reference with the campaign name.
    camapign_id: Column reference with the camapign id.
    asset_group_name: Column reference with the asset group name.
    asset_group_id: Column reference with the asset group id.
  """
  customer_name: int = 0
  customer_id: int = 1
  campaign_name: int = 2
  camapign_id: int = 3
  asset_group_name: int = 4
  asset_group_id: int = 5


@dataclasses.dataclass(frozen=True)
class Sitelinks:
  """Column map for Sitelinks sheet.

  Spreadsheet API returns a list of lists when retrieving data from a sheet.
  Column ids are needed to read and write the correct data  fields from the
  sheet. This class provides a mapping from column names to column ids. In case
  the sheet get's edited the tool can be updated from this single place.

  Atrributes:
    upload_status: Column reference with the upload status.
    delete_sitelink: Column reference with the delete status.
    customer_name: Column reference with the customer name.
    campaign_name: Column reference with the campaign name.
    link_text: Column reference with the link text.
    final_urls: Column reference with the final urls.
    description1: Column reference with the description 1.
    description2: Column reference with the description 2.
    error_message: Column reference with the error message.
    sitelink_resource: Column reference with the GA resource name.
  """
  upload_status: int = 0
  delete_sitelink: int = 1
  customer_name: int = 2
  campaign_name: int = 3
  link_text: int = 4
  final_urls: int = 5
  description1: int = 6
  description2: int = 7
  error_message: int = 8
  sitelink_resource: int = 9

class newAssetGroupsColumnMap(enum.IntEnum):
  """Column map for new Asset Group Column Map sheet.

  Spreadsheet API returns a list of lists when retrieving data from a sheet.
  Column ids are needed to read and write the correct data fields from the
  sheet. This class provides a mapping from column names to column ids. In case
  the sheet get's edited the tool can be updated from this single place.

  Atrributes:
    status: Column reference with the upload status.
    asset_check: Column reference for the asset check.
    customer_name: Column reference with the customer name.
    campaign_name: Column reference with the campaign name.
    asset_group_name: Column reference with the asset group name.
    asset_group_status: Column reference with the asset group status.
    final_url: Column reference for the final URL for the asset group creation.
    mobile_url: Column reference for the mobile URL for the asset group creation.
    path1: Column reference for the first path.
    path2: Column reference for the second path.
    headline1: Column reference for the headline 1.
    headline2: Column reference for the headline 2.
    headline3: Column reference for the headline 3.
    description1: Column reference for the description 1.
    description2: Column reference for the description 2.
    long_headline: Column reference for the long headline.
    business_name: Column reference for the business name.
    marketing_image: Column reference for the marketing image.
    square_marketing_image: Column reference for the square marketing image.
    logo: Column reference for the logo.
    message: Column reference for the message.
  """
  STATUS = 0
  ASSET_CHECK = 1
  CUSTOMER_NAME = 2
  CAMPAIGN_NAME = 3
  ASSET_GROUP_NAME = 4
  ASSET_GROUP_STATUS = 5
  FINAL_URL = 6
  MOBILE_URL = 7
  PATH1 = 8
  PATH2 = 9
  HEADLINE1 = 10
  HEADLINE2 = 11
  HEADLINE3 = 12
  DESCRIPTION1 = 13
  DESCRIPTION2 = 14
  LONG_HEADLINE = 15
  BUSINESS_NAME = 16
  MARKETING_IMAGE = 17
  SQUARE_MARKETING_IMAGE = 18
  LOGO = 19
  MESSAGE = 20
