var props = PropertiesService.getDocumentProperties();
var globalUserEditedPropertyName = 'UserEditedCampaignValues';

function getProperty() {
  return JSON.parse(PropertiesService.getDocumentProperties().getProperty(globalUserEditedPropertyName)) || {};
}

function setProperty(propertyObject) {
  PropertiesService.getDocumentProperties().setProperty(globalUserEditedPropertyName, JSON.stringify(propertyObject));
}

function assetGroupDataValidation(spreadSheet, sheetName, column, numCols, row, numRows){
  var sheet = spreadSheet.getSheetByName(sheetName);
  var dropDownRange = sheet.getRange(row, newAssetGroupsColumns.campaignName);
  var accountCell = sheet.getRange(row, newAssetGroupsColumns.accountName).getValue();

  var userEditedCampaignsValues = getProperty();
  
  const dropdownArray = Object.keys(userEditedCampaignsValues[accountCell]);
  var rule = SpreadsheetApp.newDataValidation().requireValueInList(dropdownArray, true).build();
  
  dropDownRange.setDataValidation(rule);

  if(numRows > 1) {
    assetGroupDataValidation(spreadSheet, sheetName, column, numCols, row + 1, numRows - 1)
  }
}

function assetDataValidation(spreadSheet, column, numCols, row, numRows){
  var sheet = spreadSheet.getSheetByName("Assets");

  const userEditedProperty = getProperty()
  const accountCell = sheet.getRange(row+":"+row).getValues();
  const customer = accountCell[0][assetsColumns.accountName-1];
  const campaign = accountCell[0][assetsColumns.campaignName-1];

  const campaignDropDown = sheet.getRange(row, assetsColumns.campaignName);
  const assetGroupDropDown = sheet.getRange(row, assetsColumns.assetGroupName);
      
  const campaigns = Object.keys(userEditedProperty[customer]);
  let ruleForCampaigns = SpreadsheetApp.newDataValidation().requireValueInList(campaigns, true).build();
    campaignDropDown.setDataValidation(ruleForCampaigns);

    if (column == assetsColumns.campaignName){
      const assetGroups = userEditedProperty[customer][campaign];
      let ruleForAssetGroups = SpreadsheetApp.newDataValidation().requireValueInList(assetGroups, true).build();
      assetGroupDropDown.setDataValidation(ruleForAssetGroups);
    }

  if(numRows > 1) {
    assetDataValidation(spreadSheet, column, numCols, row + 1, numRows - 1)
  }
}


function addNewCampaignUserEditsIntoProperty(value, oldValue, row, lastRowChanged, column, numberOfColumnsChanged, numberOfRowsChanged, sheet, property_name) {
  let userEditedPropertyValuesObject = getProperty();

  if (numberOfColumnsChanged > 1 || numberOfRowsChanged > 1) {
    userEditedPropertyValuesObject = { ...userEditedPropertyValuesObject, ...editCampaignValuesThroughPullingRowData(row, lastRowChanged, sheet, newCampaignsColumns.campaignName-1, newCampaignsColumns.accountName-1) };
  } else if (column === newCampaignsColumns.accountName) {
    const campaignNameValue = getCellValueFromRowData(sheet, row, newCampaignsColumns.campaignName-1);
    if (campaignNameValue !== "") {
      //if we have this Camapign in the proprty - replace
      delete userEditedPropertyValuesObject[oldValue][campaignNameValue];
      userEditedPropertyValuesObject[value] = { ...userEditedPropertyValuesObject[value], [campaignNameValue]: [] };
    }
  } else if (column === newCampaignsColumns.campaignName) {
    const customer = getCellValueFromRowData(sheet, row, newCampaignsColumns.accountName-1);
    if (oldValue && userEditedPropertyValuesObject[customer][oldValue] !== undefined) {
      delete userEditedPropertyValuesObject[customer][oldValue];
    }
    userEditedPropertyValuesObject[customer] = { ...userEditedPropertyValuesObject[customer], [value]: [] };
  }

  setProperty(userEditedPropertyValuesObject);
}

function addNewAssetGroupsUserEditsIntoProperty(value, oldValue, row, lastRowChanged, column, numberOfColumnsChanged, numberOfRowsChanged, sheet) {
  const customer = getCellValueFromRowData(sheet, row, newAssetGroupsColumns.accountName-1);
  const campaign = getCellValueFromRowData(sheet, row, newAssetGroupsColumns.campaignName-1);

  let userEditedPropertyValuesObject = getProperty();

  if (numberOfColumnsChanged > 1 || numberOfRowsChanged > 1) {
    userEditedPropertyValuesObject = {
      ...userEditedPropertyValuesObject,
      ...editAssetGroupValuesThroughPullingRowData(row, lastRowChanged, sheet, newAssetGroupsColumns.assetGroupName-1, newAssetGroupsColumns.accountName-1)
    };
  } else if (column === newAssetGroupsColumns.assetGroupName) {
    if (oldValue && userEditedPropertyValuesObject[customer]?.[campaign] !== undefined) {
      const indexOfOldValue = userEditedPropertyValuesObject[customer][campaign].indexOf(oldValue);
      if (indexOfOldValue !== -1) {
        userEditedPropertyValuesObject[customer][campaign].splice(indexOfOldValue, 1);
      }
    }
    userEditedPropertyValuesObject[customer][campaign] = [
      ...(userEditedPropertyValuesObject[customer][campaign] || []),
      value
    ];
  } else if (column === newAssetGroupsColumns.campaignName && oldValue && getCellValueFromRowData(sheet, row, newAssetGroupsColumns.assetGroupName-1) !== "") {
    if (!userEditedPropertyValuesObject[customer]?.[value]) {
      userEditedPropertyValuesObject[customer][value] = [];
    }
    const indexOfOldValue = userEditedPropertyValuesObject[customer][oldValue]?.indexOf(getCellValueFromRowData(sheet, row, newAssetGroupsColumns.assetGroupName-1));
    if (indexOfOldValue !== -1) {
      userEditedPropertyValuesObject[customer][value].push(userEditedPropertyValuesObject[customer][oldValue][indexOfOldValue]);
      userEditedPropertyValuesObject[customer][oldValue].splice(indexOfOldValue, 1);
    }
  } else if (column === newAssetGroupsColumns.accountName && oldValue && getCellValueFromRowData(sheet, row, newAssetGroupsColumns.assetGroupName-1) !== "") {
    if (!userEditedPropertyValuesObject[value]?.[campaign]) {
      userEditedPropertyValuesObject[value][campaign] = [];
    }
    const indexOfOldValue = userEditedPropertyValuesObject[oldValue]?.[campaign]?.indexOf(getCellValueFromRowData(sheet, row, newAssetGroupsColumns.assetGroupName-1));
    if (indexOfOldValue !== -1) {
      userEditedPropertyValuesObject[value][campaign].push(userEditedPropertyValuesObject[oldValue][campaign][indexOfOldValue]);
      userEditedPropertyValuesObject[oldValue][campaign].splice(indexOfOldValue, 1);
    }
  }

  setProperty(userEditedPropertyValuesObject);
}


function getCellValueFromRowData(sheet, row, position){
    let range = sheet.getRange(row + ':' + row).getValues();

    return range[0][position]
}

function editCampaignValuesThroughPullingRowData(row, lastRowChanged, sheet, positionForName, positionForCustomer){
    let resultValues = {};

  for (let index = row; index <= lastRowChanged; index++) {
    let customer = getCellValueFromRowData(sheet, index, positionForCustomer);
    let name = getCellValueFromRowData(sheet, index, positionForName);

    if (!resultValues[customer]) {
      resultValues[customer] = {};
    }

    resultValues[customer][name] = [];
  }

  return resultValues;
}

function editAssetGroupValuesThroughPullingRowData(row, lastRowChanged, sheet, positionForName, positionForCustomer, positionForCampaign){
    let resultValues = {};

  for (let index = row; index <= lastRowChanged; index++) {
    let customer = getCellValueFromRowData(sheet, index, positionForCustomer);
    let campaign = getCellValueFromRowData(sheet, index, positionForCampaign);
    let name = getCellValueFromRowData(sheet, index, positionForName);

    resultValues[customer] = resultValues[customer] || {};

    if (!resultValues[customer][campaign]) {
      resultValues[customer][campaign] = [name];
    } else {
      resultValues[customer][campaign].push(name);
    }
  }

  return resultValues;
}


function updateUploadedValuesIntoProperty(){
  const assetGroupSheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('AssetGroupList');
  const camapignSheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('CampaignList');
  var assetGroupValues = assetGroupSheet.getRange('6:' + assetGroupSheet.getMaxRows()).getValues();    //row 6 is where actual data starts 
  var campaignValues = camapignSheet.getRange('6:' + camapignSheet.getMaxRows()).getValues();

  let campaignAssetGroupStructure = getProperty();
  if (!campaignAssetGroupStructure) {
    campaignAssetGroupStructure = {};
  }
  campaignValues.forEach(row => {
    const customer = row[campaignListColumns.customerName-1];
    const campaign = row[campaignListColumns.campaignName-1];
    campaignAssetGroupStructure[customer] = campaignAssetGroupStructure[customer] || {};
    campaignAssetGroupStructure[customer][campaign] = campaignAssetGroupStructure[customer][campaign] || [];
  });

  assetGroupValues.forEach(row => {
    const customer = row[assetGroupListColumns.customerName-1];
    const campaign = row[assetGroupListColumns.campaignName-1];
    const assetGroup = row[assetGroupListColumns.assetGroupName-1];
    
    campaignAssetGroupStructure[customer] = campaignAssetGroupStructure[customer] || {};
    campaignAssetGroupStructure[customer][campaign] = campaignAssetGroupStructure[customer][campaign] || [];
    
    campaignAssetGroupStructure[customer][campaign].push(assetGroup);
  });

   setProperty(campaignAssetGroupStructure);
}

