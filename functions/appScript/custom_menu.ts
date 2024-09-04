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
 * The event handler triggered when opening the spreadsheet.
 * Triggers the generation of a custom UI menu, which can be used to
 * trigger further functionalities in the solution, through PubSub Triggers.
 * @param {Event} e The onOpen event.
 */
function onOpen(e) {
  updateUploadedValuesIntoProperty();
  const ui = SpreadsheetApp.getUi();

  ui.createMenu('pMax Execute')
    .addSubMenu(
      ui
        .createMenu('Refresh Spreadsheet')
        .addItem('Refresh all sheets', 'pubsubRefreshAllRequest')
        .addSeparator()
        .addItem('CustomerList', 'pubsubRefreshCustomersRequest')
        .addItem('CampaignList', 'pubsubRefreshCampaignsRequest')
        .addItem('AssetGroupList', 'pubsubRefreshAssetGroupsRequest')
        .addItem('Assets', 'pubsubRefreshAssetsRequest')
        .addItem('Sitelinks', 'pubsubRefreshSitelinksRequest'),
    )
    .addSeparator()
    .addItem('Upload to Google Ads', 'pubsubUploadRequest')
    .addSeparator()
    .addItem('Delete Assets', 'pubsubDeleteRequest')
    .addToUi();
}

/**
 * Generate a PubSub trigger to the Cloud Project.
 * PubSub Trigger will be processed and based on the attached attribute
 * It will run the related action in the Cloud Function.
 */
function pubsubRefreshAllRequest() {
  const attr = {
    id: 'madmax',
    value: 'run_all',
  };
  pubsub(PROJECT_NAME, PUBSUB_TOPIC, attr, 'REFRESH');
  updateUploadedValuesIntoProperty();
}

/**
 * Generate a PubSub trigger to the Cloud Project.
 * PubSub Trigger will be processed and based on the attached attribute
 * It will run the related action in the Cloud Function.
 */
function pubsubRefreshCustomersRequest() {
  const attr = {
    id: 'madmax',
    value: 'run_all',
  };
  pubsub(PROJECT_NAME, PUBSUB_TOPIC, attr, 'REFRESH_CUSTOMER_LIST');
  updateUploadedValuesIntoProperty();
}

/**
 * Generate a PubSub trigger to the Cloud Project.
 * PubSub Trigger will be processed and based on the attached attribute
 * It will run the related action in the Cloud Function.
 */
function pubsubRefreshCampaignsRequest() {
  const attr = {
    id: 'madmax',
    value: 'run_all',
  };
  pubsub(PROJECT_NAME, PUBSUB_TOPIC, attr, 'REFRESH_CAMPAIGN_LIST');
  updateUploadedValuesIntoProperty();
}

/**
 * Generate a PubSub trigger to the Cloud Project.
 * PubSub Trigger will be processed and based on the attached attribute
 * It will run the related action in the Cloud Function.
 */
function pubsubRefreshAssetGroupsRequest() {
  const attr = {
    id: 'madmax',
    value: 'run_all',
  };
  pubsub(PROJECT_NAME, PUBSUB_TOPIC, attr, 'REFRESH_ASSET_GROUP_LIST');
  updateUploadedValuesIntoProperty();
}

/**
 * Generate a PubSub trigger to the Cloud Project.
 * PubSub Trigger will be processed and based on the attached attribute
 * It will run the related action in the Cloud Function.
 */
function pubsubRefreshAssetsRequest() {
  const attr = {
    id: 'madmax',
    value: 'run_all',
  };
  pubsub(PROJECT_NAME, PUBSUB_TOPIC, attr, 'REFRESH_ASSETS');
  updateUploadedValuesIntoProperty();
}

/**
 * Generate a PubSub trigger to the Cloud Project.
 * PubSub Trigger will be processed and based on the attached attribute
 * It will run the related action in the Cloud Function.
 */
function pubsubRefreshSitelinksRequest() {
  const attr = {
    id: 'madmax',
    value: 'run_all',
  };
  pubsub(PROJECT_NAME, PUBSUB_TOPIC, attr, 'REFRESH_SITELINKS');
  updateUploadedValuesIntoProperty();
}

/**
 * Generate a PubSub trigger to the Cloud Project.
 * PubSub Trigger will be processed and based on the attached attribute
 * It will run the related action in the Cloud Function.
 */
function pubsubUploadRequest() {
  const attr = {
    id: 'madmax',
    value: 'run_all',
  };
  pubsub(PROJECT_NAME, PUBSUB_TOPIC, attr, 'UPLOAD');
}

/**
 * Generate a PubSub trigger to the Cloud Project.
 * PubSub Trigger will be processed and based on the attached attribute
 * It will run the related action in the Cloud Function.
 */
function pubsubDeleteRequest() {
  const attr = {
    id: 'madmax',
    value: 'run_all',
  };
  pubsub(PROJECT_NAME, PUBSUB_TOPIC, attr, 'DELETE');
}
