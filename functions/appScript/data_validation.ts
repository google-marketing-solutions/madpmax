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
 * Generate data validation dropdowns for Asset Group Sheet.
 * @param {Spreadsheet} spreadSheet Spreadsheet class from Google Sheet API.
 * @param {number} column Column index
 * @param {number} row Row number of the input
 * @param {number} numRows Rowcount of the input
 */
function assetGroupDataValidation(
  spreadSheet,
  column,
  row,
  numRows,
) {
  if (column <= NEW_ASSET_GROUPS.ASSET_GROUP_NAME + 1) {
    const sheet = spreadSheet.getSheetByName(SHEET_NAMES.NEW_ASSET_GROUPS);
    const dropDownRange = sheet.getRange(row, NEW_ASSET_GROUPS.CAMPAIGN_NAME + 1);
    const accountCell = sheet
      .getRange(row, NEW_ASSET_GROUPS.ACCOUNT_NAME + 1)
      .getValue();
    const userEditedCampaignsValues = getProperty();

    const dropdownArray = Object.keys(userEditedCampaignsValues[accountCell]);
    const rule = SpreadsheetApp.newDataValidation()
      .requireValueInList(dropdownArray, true)
      .build();

    dropDownRange.setDataValidation(rule);

    if (numRows > 1) {
      assetGroupDataValidation(spreadSheet, sheetName, row + 1, numRows - 1);
    }
  }
}

/**
 * Generate data validation dropdowns for Assets Sheet.
 * @param {Spreadsheet} spreadSheet Spreadsheet class from Google Sheet API.
 * @param {number} column Column index
 * @param {number} row Row index of the input
 * @param {number} numRows Rowcount of the input
 */
function assetDataValidation(
  spreadSheet,
  column,
  row,
  numRows,
) {
  if (column <= ASSETS.ASSET_GROUP_NAME + 1) {
    const sheet = spreadSheet.getSheetByName(SHEET_NAMES.ASSETS);

    const userEditedProperty = getProperty();
    const accountCell = sheet.getRange(row + ':' + row).getValues();
    const customer = accountCell[0][ASSETS.ACCOUNT_NAME];

    if (column === ASSETS.ACCOUNT_NAME + 1) {
      const dropDown = sheet.getRange(row, ASSETS.CAMPAIGN_NAME + 1);
      const campaigns = Object.keys(userEditedProperty[customer]);
      const ruleForCampaigns = SpreadsheetApp.newDataValidation()
        .requireValueInList(campaigns, true)
        .build();
      dropDown.setDataValidation(ruleForCampaigns);
    }

    if (column === ASSETS.CAMPAIGN_NAME + 1) {
      const campaign = accountCell[0][ASSETS.CAMPAIGN_NAME];
      const assetGroups = userEditedProperty[customer][campaign];
      const dropDown = sheet.getRange(row, ASSETS.ASSET_GROUP_NAME + 1);
      const ruleForAssetGroups = SpreadsheetApp.newDataValidation()
        .requireValueInList(assetGroups, true)
        .build();
      dropDown.setDataValidation(ruleForAssetGroups);
    }

    if (numRows > 1) {
      assetDataValidation(spreadSheet, column, row + 1, numRows - 1);
    }
  }
}
