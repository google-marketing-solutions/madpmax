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

const USER_EDITED_PROPERTY_NAME = 'UserEditedCampaignValues';

/**
 * Returns the property object from the document properties
 * @return {{customer: {campaign: string[]}}} Object containing account mapping
 */
function getProperty() {
  return (
    JSON.parse(
      PropertiesService.getDocumentProperties().getProperty(
        USER_EDITED_PROPERTY_NAME,
      ),
    ) || {}
  );
}

/**
 * Sets the property object in the document properties
 * @param {{customer: {campaign: string[]}}} propertyObject Object containing
 *    account mapping
 */
function setProperty(propertyObject) {
  PropertiesService.getDocumentProperties().setProperty(
    USER_EDITED_PROPERTY_NAME,
    JSON.stringify(propertyObject),
  );
}

/**
 * Deleted the property object from the document properties.
 */
function clearProperty() {
  PropertiesService.getDocumentProperties().deleteProperty(
    USER_EDITED_PROPERTY_NAME
  );
}

/**
 * Adds the new campaign user edits into the property object
 * @param {string} value New cell value
 * @param {string} oldValue Previous cell value
 * @param {number} row Index of the row of the edited cell
 * @param {number} column Index of the column of the edited cell
 * @param {number} numberOfColumnsChanged Count of number of columns edited.
 * @param {number} numberOfRowsChanged Count of number of rows edited.
 * @param {Spreadsheet.Sheet} sheet Sheet object contain sheet data.
 */
function addNewCampaignUserEditsIntoProperty(
  value,
  oldValue,
  row,
  column,
  numberOfColumnsChanged,
  numberOfRowsChanged,
  sheet,
) {
  if (column <= NEW_CAMPAIGNS.CAMPAIGN_NAME + 1) {
    let userEditedPropertyValuesObject = getProperty();

    const customer = getCellValueFromRowData(
      sheet,
      row,
      NEW_CAMPAIGNS.CUSTOMER_NAME,
    );
    const campaign = getCellValueFromRowData(
      sheet,
      row,
      NEW_CAMPAIGNS.CAMPAIGN_NAME,
    );

    if (numberOfColumnsChanged > 1 || numberOfRowsChanged > 1) {
      updateUploadedValuesIntoProperty();
    } else if (column === NEW_CAMPAIGNS.CUSTOMER_NAME + 1) {
      if (campaign !== '') {
        delete userEditedPropertyValuesObject[oldValue][campaign];
        userEditedPropertyValuesObject[value] = {
          ...userEditedPropertyValuesObject[value],
          [campaign]: [],
        };
      }
    } else if (column === NEW_CAMPAIGNS.CAMPAIGN_NAME + 1) {
      if (
        oldValue &&
        userEditedPropertyValuesObject[customer][oldValue] !== undefined
      ) {
        delete userEditedPropertyValuesObject[customer][oldValue];
      }
      userEditedPropertyValuesObject[customer] = {
        ...userEditedPropertyValuesObject[customer],
        [value]: [],
      };
    }

    setProperty(userEditedPropertyValuesObject);
  }
}

/**
 * Adds the new asset group user edits into the property object
 * @param {string} value New cell value
 * @param {string} oldValue Previous cell value
 * @param {number} row Index of the row of the edited cell
 * @param {number} column Index of the column of the edited cell
 * @param {number} numberOfColumnsChanged Count of number of columns edited.
 * @param {number} numberOfRowsChanged Count of number of rows edited.
 * @param {Spreadsheet.Sheet} sheet Sheet object contain sheet data.
 */
function addNewAssetGroupsUserEditsIntoProperty(
  value,
  oldValue,
  row,
  column,
  numberOfColumnsChanged,
  numberOfRowsChanged,
  sheet,
) {
  if (column <= NEW_ASSET_GROUPS.ASSET_GROUP_NAME + 1) {
    const customer = getCellValueFromRowData(
      sheet,
      row,
      NEW_ASSET_GROUPS.CUSTOMER_NAME,
    );
    const campaign = getCellValueFromRowData(
      sheet,
      row,
      NEW_ASSET_GROUPS.CAMPAIGN_NAME,
    );

    let userEditedPropertyValuesObject = getProperty();

    if (numberOfColumnsChanged > 1 || numberOfRowsChanged > 1) {
      updateUploadedValuesIntoProperty();
    } else if (column === NEW_ASSET_GROUPS.ASSET_GROUP_NAME + 1) {
      if (
        oldValue &&
        userEditedPropertyValuesObject[customer]?.[campaign] !== undefined
      ) {
        const indexOfOldValue =
          userEditedPropertyValuesObject[customer][campaign].indexOf(oldValue);
        if (indexOfOldValue !== -1) {
          userEditedPropertyValuesObject[customer][campaign].splice(
            indexOfOldValue,
            1,
          );
        }
      }
      userEditedPropertyValuesObject[customer][campaign] = [
        ...(userEditedPropertyValuesObject[customer][campaign] || []),
        value,
      ];
    } else if (
      column === NEW_ASSET_GROUPS.CAMPAIGN_NAME + 1 &&
      oldValue &&
      getCellValueFromRowData(
        sheet,
        row,
        NEW_ASSET_GROUPS.ASSET_GROUP_NAME,
      ) !== ''
    ) {
      if (!userEditedPropertyValuesObject[customer]?.[value]) {
        userEditedPropertyValuesObject[customer][value] = [];
      }
      const indexOfOldValue = userEditedPropertyValuesObject[customer][
        oldValue
      ]?.indexOf(
        getCellValueFromRowData(
          sheet,
          row,
          NEW_ASSET_GROUPS.ASSET_GROUP_NAME,
        ),
      );
      if (indexOfOldValue !== -1) {
        userEditedPropertyValuesObject[customer][value].push(
          userEditedPropertyValuesObject[customer][oldValue][indexOfOldValue],
        );
        userEditedPropertyValuesObject[customer][oldValue].splice(
          indexOfOldValue,
          1,
        );
      }
    } else if (
      column === NEW_ASSET_GROUPS.CUSTOMER_NAME + 1 &&
      oldValue &&
      getCellValueFromRowData(
        sheet,
        row,
        NEW_ASSET_GROUPS.ASSET_GROUP_NAME,
      ) !== ''
    ) {
      if (!userEditedPropertyValuesObject[value]?.[campaign]) {
        userEditedPropertyValuesObject[value][campaign] = [];
      }
      const indexOfOldValue = userEditedPropertyValuesObject[oldValue]?.[
        campaign
      ]?.indexOf(
        getCellValueFromRowData(
          sheet,
          row,
          NEW_ASSET_GROUPS.ASSET_GROUP_NAME,
        ),
      );
      if (indexOfOldValue !== -1) {
        userEditedPropertyValuesObject[value][campaign].push(
          userEditedPropertyValuesObject[oldValue][campaign][indexOfOldValue],
        );
        userEditedPropertyValuesObject[oldValue][campaign].splice(
          indexOfOldValue,
          1,
        );
      }
    }

    setProperty(userEditedPropertyValuesObject);
  }
}

/**
 * Gets the cell value from the row data
 * @param {Spreadsheet.Sheet} sheet Sheet object contain sheet data.
 * @param {number} row Row index of change.
 * @param {number} position Index of cell.
 * @return {string} Cell content.
 */
function getCellValueFromRowData(sheet, row, position) {
  const range = sheet.getRange(row + ':' + row).getValues();

  return range[0][position];
}

/**
 * Updates the uploaded values into the property
 */
function updateUploadedValuesIntoProperty() {
  const assetGroupSheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(
    SHEET_NAMES.ASSET_GROUPS,
  );
  const campaignSheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(
    SHEET_NAMES.CAMPAIGNS,
  );
  const newAssetGroupSheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(
    SHEET_NAMES.NEW_ASSET_GROUPS,
  );
  const newCampaignSheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(
    SHEET_NAMES.NEW_CAMPAIGNS,
  );
  const assetGroupValues = assetGroupSheet
    .getRange('6:' + assetGroupSheet.getMaxRows())
    .getValues(); // row 6 is where actual data starts
  const campaignValues = campaignSheet
    .getRange('6:' + campaignSheet.getMaxRows())
    .getValues();
  const newAssetGroupValues = newAssetGroupSheet
    .getRange('6:' + newAssetGroupSheet.getMaxRows())
    .getValues(); // row 6 is where actual data starts
  const newCampaignValues = newCampaignSheet
    .getRange('6:' + newCampaignSheet.getMaxRows())
    .getValues();

  clearProperty();
  let campaignAssetGroupStructure = getProperty();
  if (!campaignAssetGroupStructure) {
    campaignAssetGroupStructure = {};
  }
  campaignValues.forEach((row) => {
    const customer = row[CAMPAIGN_LIST.CUSTOMER_NAME];
    const campaign = row[CAMPAIGN_LIST.CAMPAIGN_NAME];
    campaignAssetGroupStructure[customer] =
      campaignAssetGroupStructure[customer] || {};
    campaignAssetGroupStructure[customer][campaign] =
      campaignAssetGroupStructure[customer][campaign] || [];
  });

  newCampaignValues.forEach((row) => {
    const customer = row[NEW_CAMPAIGNS.CUSTOMER_NAME];
    const campaign = row[NEW_CAMPAIGNS.CAMPAIGN_NAME];
    campaignAssetGroupStructure[customer] =
      campaignAssetGroupStructure[customer] || {};
    campaignAssetGroupStructure[customer][campaign] =
      campaignAssetGroupStructure[customer][campaign] || [];
  });

  assetGroupValues.forEach((row) => {
    const customer = row[ASSET_GROUP_LIST.CUSTOMER_NAME];
    const campaign = row[ASSET_GROUP_LIST.CAMPAIGN_NAME];
    const assetGroup = row[ASSET_GROUP_LIST.ASSET_GROUP_NAME];
    try {
      campaignAssetGroupStructure[customer][campaign].push(assetGroup);
    } catch (error) {
      Logger.log(error);
    }
  });

  newAssetGroupValues.forEach((row) => {
    const customer = row[NEW_ASSET_GROUPS.CUSTOMER_NAME];
    const campaign = row[NEW_ASSET_GROUPS.CAMPAIGN_NAME];
    const assetGroup = row[NEW_ASSET_GROUPS.ASSET_GROUP_NAME];
    try {
      campaignAssetGroupStructure[customer][campaign].push(assetGroup);
    } catch (error) {
      Logger.log(error);
    }
  });

  setProperty(campaignAssetGroupStructure);
}
