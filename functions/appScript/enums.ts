/**
 * Copyright 2024 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *       http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/**
 * Sheetnames as in the master spreadsheet.
 * @enum {string}
 */
const SHEET_NAMES = {
  CUSTOMERS: 'CustomerList',
  CAMPAIGNS: 'CampaignList',
  ASSET_GROUPS: 'AssetGroupList',
  ASSETS: 'Assets',
  SITELINKS: 'Sitelinks',
  NEW_CAMPAIGNS: 'NewCampaigns',
  NEW_ASSET_GROUPS: 'NewAssetGroups',
};

/**
 * Minimum asset requirements per pmax asset group.
 * @enum {number}
 */
const REQUIRED_ASSETS = {
  HEADLINES: 3,
  LONG_HEADLINES: 1,
  DESCRIPTIONS: 2,
  BUSINESS_NAME: 1,
  MARKETING_IMAGE: 1,
  SQUARE_IMAGE: 1,
  LOGO: 1,
};

/**
 * Column mapping for the NewAssetGroups sheet.
 * @enum {number}
 */
const NEW_ASSET_GROUPS = {
  STATUS: 0,
  ASSET_CHECK: 1,
  ACCOUNT_NAME: 2,
  CAMPAIGN_NAME: 3,
  ASSET_GROUP_NAME: 4,
  ASSET_GROUP_STATUS: 5,
  FINAL_URL: 6,
  MOBILE_URL: 7,
  PATH1: 8,
  PATH2: 9,
  HEADLINE1: 10,
  HEADLINE2: 11,
  HEADLINE3: 12,
  DESCRIPTION1: 13,
  DESCRIPTION2: 14,
  LONG_HEADLINE: 15,
  BUSINESS_NAME: 16,
  MARKETING_IMAGE: 17,
  SQUARE_IMAGE: 18,
  LOGO: 19
};

/**
 * Column mapping for the NewCampaigns sheet.
 * @enum {number}
 */
const NEW_CAMPAIGNS = {
  STATUS: 0,
  ACCOUNT_NAME: 1,
  CAMPAIGN_NAME: 2
};

/**
 * Column mapping for the Assets sheet.
 * @enum {number}
 */
const ASSETS = {
  STATUS: 0,
  DELETE_OPTION: 1,
  ACCOUNT_NAME: 2,
  CAMPAIGN_NAME: 3,
  ASSET_GROUP_NAME: 4,
  TYPE: 5
};

/**
 * Column mapping for the Sitelinks sheet.
 * @enum {number}
 */
const SITELINKS = {
  STATUS: 0,
  DELETE_OPTION: 1,
  ACCOUNT_NAME: 2,
  CAMPAIGN_NAME: 3,
  LINK_TEXT: 4
};

/**
 * Column mapping for the AssetGroupList sheet.
 * @enum {number}
 */
const ASSET_GROUP_LIST = {
  CUSTOMER_NAME: 0,
  CUSTOMER_ID: 1,
  CAMPAIGN_NAME: 2,
  CAMPAIGN_ID: 3,
  ASSET_GROUP_NAME: 4,
  ASSET_GROUP_ID: 5
};

/**
 * Column mapping for the CampaignList sheet.
 * @enum {number}
 */
const CAMPAIGN_LIST = {
  CUSTOMER_NAME: 0,
  CUSTOMER_ID: 1,
  CAMPAIGN_NAME: 2,
  CAMPAIGN_ID: 3
};

/**
 * Column mapping for the CustomerList sheet.
 * @enum {number}
 */
const CUSTOMER_LIST = {
  CUSTOMER_NAME: 0,
  CUSTOMER_ID: 1
};

/**
 * Row Status codes as in the master spreadsheet.
 * @enum {string}
 */
const ROW_STATUS = {
  UPLOADED: 'UPLOADED',
  ERROR: 'ERROR'
}

/**
 * Asset Types for pMAx as in the master spreadsheet.
 * @enum {string}
 */
const ASSET_TYPES = {
  HEADLINE: 'HEADLINE',
  LONG_HEADLINE: 'LONG_HEADLINE',
  DESCRIPTION: 'DESCRIPTION',
  BUSINESS: 'BUSINESS',
  IMAGE: 'IMAGE',
  SQUARE_IMAGE: 'SQUARE_IMAGE',
  LOGO: 'LOGO'
}
