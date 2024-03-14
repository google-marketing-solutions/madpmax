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
 * @fileoverview This file contains the functions that are triggered by
 * edits made to the spreadsheet. It triggers validation of input to prevent
 * downstream API errors.
 */

/**
 * This function is called when a cell is edited.
 * @param {Event} e The event object.
 */
function onEdit(e) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const column = e.range.getColumn();
  const row = e.range.getRow();
  const numRows = e.range.getNumRows();
  const sheetName = e.range.getSheet().getSheetName();

  // More scenarios will be added with following CLs.
  switch (sheetName) {
    case SHEET_NAMES.NEW_ASSET_GROUPS:
      checkMinimumAssets(ss);
      break;
    default:
      break;
  }
}

/**
 * Validates the minimal asset requirements for each Asset Groups.
 *
 * Checks newAssetGroup sheet when edited. Loops through the rows that have
 * been edited. Validates the Assets and writes the status back to the sheet.
 * @param {Spreadsheet} spreadSheet The spreadsheet object.
 */
function checkMinimumAssets(spreadSheet) {
  newAssetGroupsSheet = spreadSheet.getSheetByName(SHEET_NAMES.NEW_ASSET_GROUPS);
  newValues = newAssetGroupsSheet.getDataRange().getValues();

  let result = {};

  for (let id in newValues) {
    if (newValues.hasOwnProperty(id)) {
      let headlineCount = 0;
      let longHeadlineCount = 0;
      let descriptionCount = 0;
      let businessCount = 0;
      let imageCount = 0;
      let squareImageCount = 0;
      let logoCount = 0;

      result[id] = { message: '', status: true };

      if (newValues[id][NEW_ASSET_GROUPS.STATUS] === ROW_STATUS.UPLOADED) { continue; }
      if (
        newValues[id][NEW_ASSET_GROUPS.ACCOUNT_NAME] === '' ||
        newValues[id][NEW_ASSET_GROUPS.CAMPAIGN_NAME] === '' ||
        newValues[id][NEW_ASSET_GROUPS.ASSET_GROUP_NAME] === ''
      ) {
        continue;
      }
      if (id < 5) {  continue; }

      headlineCount = assetCounter(
        headlineCount, newValues[id][NEW_ASSET_GROUPS.HEADLINE1],
      );
      headlineCount = assetCounter(
        headlineCount,  newValues[id][NEW_ASSET_GROUPS.HEADLINE2],
      );
      headlineCount = assetCounter(
        headlineCount, newValues[id][NEW_ASSET_GROUPS.HEADLINE3],
      );
      descriptionCount = assetCounter(
        descriptionCount, newValues[id][NEW_ASSET_GROUPS.DESCRIPTION1],
      );
      descriptionCount = assetCounter(
        descriptionCount, newValues[id][NEW_ASSET_GROUPS.DESCRIPTION2],
      );
      longHeadlineCount = assetCounter(
        longHeadlineCount, newValues[id][NEW_ASSET_GROUPS.LONG_HEADLINE],
      );
      businessCount = assetCounter(
        businessCount, newValues[id][NEW_ASSET_GROUPS.BUSINESS_NAME],
      );
      imageCount = assetCounter(
        imageCount, newValues[id][NEW_ASSET_GROUPS.MARKETING_IMAGE],
      );
      squareImageCount = assetCounter(
        squareImageCount, newValues[id][NEW_ASSET_GROUPS.SQUARE_IMAGE],
      );
      logoCount = assetCounter(
        logoCount, newValues[id][NEW_ASSET_GROUPS.LOGO]
      );

      result[id] = assetStatus(
        newValues[id][NEW_ASSET_GROUPS.HEADLINE1],
        headlineCount,
        REQUIRED_ASSETS.HEADLINES,
        result[id],
        ASSET_TYPES.HEADLINE,
      );
      result[id] = assetStatus(
        newValues[id][NEW_ASSET_GROUPS.LONG_HEADLINE],
        longHeadlineCount,
        REQUIRED_ASSETS.LONG_HEADLINES,
        result[id],
        ASSET_TYPES.LONG_HEADLINE,
      );
      result[id] = assetStatus(
        newValues[id][NEW_ASSET_GROUPS.DESCRIPTION1],
        descriptionCount,
        REQUIRED_ASSETS.DESCRIPTIONS,
        result[id],
        ASSET_TYPES.DESCRIPTION,
      );
      result[id] = assetStatus(
        newValues[id][NEW_ASSET_GROUPS.BUSINESS_NAME],
        businessCount,
        REQUIRED_ASSETS.BUSINESS_NAME,
        result[id],
        ASSET_TYPES.BUSINESS,
      );
      result[id] = assetStatus(
        newValues[id][NEW_ASSET_GROUPS.MARKETING_IMAGE],
        imageCount,
        REQUIRED_ASSETS.MARKETING_IMAGE,
        result[id],
        ASSET_TYPES.IMAGE,
      );
      result[id] = assetStatus(
        newValues[id][NEW_ASSET_GROUPS.SQUARE_IMAGE],
        squareImageCount,
        REQUIRED_ASSETS.SQUARE_IMAGE,
        result[id],
        ASSET_TYPES.SQUARE_IMAGE,
      );
      result[id] = assetStatus(
        newValues[id][NEW_ASSET_GROUPS.LOGO],
        logoCount,
        REQUIRED_ASSETS.LOGO,
        result[id],
        ASSET_TYPES.LOGO,
      );

      if (!result[id].status) {
        result[id].message =
          'ERROR: Asset requirements are not met:' + result[id].message;
      } else {
        result[id].message = 'SUCCESS';
      }

      const outputRow = Number(id) + 1;
      newAssetGroupsSheet.getRange(outputRow, 2).setValue(result[id].message);
    }
  }
}

/**
 * Incremental counter, to count the occurences of each Asset Type.
 * @param {number} counter The counter object.
 * @param {string} cellValue The cell value object.
 * @returns {number} The incremental count value for the number of assets.
 */
function assetCounter(counter, cellValue) {
  if (cellValue !== '') {
    counter = counter + 1;
  }
  return counter;
}

/**
 * Validate if the the Asset Groups meets requirements for each asset type.
 *
 * Assigns the respective status and error message if relevant.
 * @param {string} assetValue The asset value object.
 * @param {number} assetCount The asset count object.
 * @param {number} assetRequirement The asset requirement object.
 * @param {{status: boolean, message: string}} assetStatus The asset status
 *    object.
 * @param {string} assetType The asset type object.
 * @returns {{status: boolean, message: string}} Object containg the status
 *    details for the given Asset Type.
 */
function assetStatus(
  assetValue,
  assetCount,
  assetRequirement,
  assetStatus,
  assetType,
) {
  let errorMssg = '';
  let urlError = '';
  let noValueError = '';
  let validURL = true;

  switch (assetType) {
    case ASSET_TYPES.HEADLINE:
      noValueError =
        '\n\tNot enough headlines assigned to the Asset Group (3 required)';
      break;
    case ASSET_TYPES.LONG_HEADLINE:
      noValueError =
        '\n\tNo long headlines assigned to the Asset Group (1 required)';
      break;
    case ASSET_TYPES.DESCRIPTION:
      noValueError =
        '\n\tNot enough descriptions assigned to the Asset Group (2 required)';
      break;
    case ASSET_TYPES.BUSINESS:
      noValueError =
        '\n\tNo business name assigned to the Asset Group. (1 required)';
      break;
    case ASSET_TYPES.IMAGE:
      noValueError =
        '\n\tNo marketing image assigned to the Asset Group. (1 required)';
      validURL = isValidURL(assetValue);
      urlError = '\n\tMarketing Image contains an invalid URL';
      break;
    case ASSET_TYPES.SQUARE_IMAGE:
      noValueError =
        '\n\tNo square image assigned to the Asset Group. (1 required)';
      validURL = isValidURL(assetValue);
      urlError = '\n\tSquare Image contains an invalid URL';
      break;
    case ASSET_TYPES.LOGO:
      noValueError = '\n\tNo logo assigned to the Asset Group. (1 required)';
      validURL = isValidURL(assetValue);
      urlError = '\n\tLogo contains an invalid URL';
      break;
    default:
      break;
  }
  if (noValueError && !urlError) {
    errorMssg = errorMssg + noValueError;
  }
  if (!validURL && urlError && assetValue) {
    errorMssg = errorMssg + urlError;
  }

  if (assetCount < assetRequirement || !validURL) {
    assetStatus.status = false;
    assetStatus.message = assetStatus.message + errorMssg;
  }
  return assetStatus;
}

/**
 * Validate sting is in URL format for image assets.
 * @param {string} str The string object.
 * @returns {boolean} True is the string contains a url otherwise false.
 */
function isValidURL(str) {
  return (
    /^(http(s):\/\/.)[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)$/g.test(
      str,
    )
  )
}
