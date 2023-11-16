function onEdit(e) {
  
  var editedValue = e.value;
  var ss=SpreadsheetApp.getActiveSpreadsheet();
  var oldValue = e.oldValue;
  var column = e.range.getColumn();
  var numberOfColumnsChanged = e.range.getNumColumns();
  var numberOfRowsChanged = e.range.getNumColumns();
  var row = e.range.getRow();
  var lastRowChanged =  e.range.getLastRow();
  var numCols = e.range.getNumColumns()
  var numRows = e.range.getNumRows()
  var sheetName = e.range.getSheet().getSheetName();

  // Set Dynamic Dropdowns for Assets Sheet
  if(sheetName == "Assets" && column <= assetsColumns.assetGroupName) {// if customer changes any name related columns 
    assetDataValidation(ss, column, numCols, row, numRows);
  }

  // Set Dynamic Dropdowns for NewAssetGroups  or add new edited values into properties
  if(sheetName == "NewAssetGroups") {
    if(column <= newAssetGroupsColumns.assetGroupName){ //if user changes a name, campaign or customer 
      addNewAssetGroupsUserEditsIntoProperty(editedValue, oldValue, row, lastRowChanged, column, numberOfColumnsChanged, numberOfRowsChanged, ss.getSheetByName(sheetName));

      assetGroupDataValidation(ss, sheetName, column, numCols, row, numRows)
    }
  }

  if(sheetName == "NewCampaigns" && column <= newCampaignsColumns.campaignName) {
    addNewCampaignUserEditsIntoProperty(editedValue, oldValue, row, lastRowChanged, column, numberOfColumnsChanged, numberOfRowsChanged, ss.getSheetByName(sheetName), globalUserEditedPropertyName);
  }
  
  if(sheetName == "Sitelinks") {
    if (column <= sitelinksColimns.campaignName) {
      assetGroupDataValidation(ss, sheetName, column, numCols, row, numRows)
    }
  } 
  const headlines_required = 3;
  const long_headlines_required = 1;
  const descriptions_required = 2;
  const business_name_required = 1;
  const marketing_image_required = 1;
  const square_marketing_image_required = 1;
  const logo_required = 1;

  // Check for Minimum Asset requirements for a new asset group.
  if(sheetName=="NewAssetGroups" || sheetName=="Assets") {
    // Get values from net AssetGroups
    newAssetGroupsSheet = ss.getSheetByName("NewAssetGroups")
    newAssetGroupsValues = newAssetGroupsSheet.getDataRange().getValues();

    // Get values from Assets
    newAssetsSheet = ss.getSheetByName("Assets")
    newAssetsValues = newAssetsSheet.getDataRange().getValues();

// As column numbers starty at 1, deducting 1 from column number to get the correct position in array 
    for(let row_index = assetsColumns.type-1; row_index < newAssetGroupsValues.length; row_index++){

      let headlines_cnt = 0;
      let long_headlines_cnt = 0;
      let descriptions_cnt = 0;
      let business_name_cnt = 0;
      let marketing_image_cnt = 0;
      let square_marketing_image_cnt = 0;
      let logo_cnt = 0;

      if(newAssetGroupsValues[row_index][newAssetGroupsColumns.status-1] != "UPLOADED" && (newAssetGroupsValues[row_index][newAssetGroupsColumns.accountName-1] != "" && newAssetGroupsValues[row_index][newAssetGroupsColumns.campaignName-1] != "" && newAssetGroupsValues[row_index][newAssetGroupsColumns.assetGroupName-1] != "") && (newAssetGroupsValues[row_index][newAssetGroupsColumns.accountName-1] != null && newAssetGroupsValues[row_index][newAssetGroupsColumns.campaignName-1] != null && newAssetGroupsValues[row_index][newAssetGroupsColumns.assetGroupName-1] != null)) {
        for(let i = newAssetGroupsColumns.assetGroupName; i < newAssetsValues.length; i++){
          const newAssetGroupKey = newAssetGroupsValues[row_index][newAssetGroupsColumns.accountName-1] + ";" + newAssetGroupsValues[row_index][newAssetGroupsColumns.campaignName-1] + ";" + newAssetGroupsValues[row_index][newAssetGroupsColumns.assetGroupName-1]
          const newAssetKey = newAssetsValues[i][assetsColumns.accountName-1] + ";" + newAssetsValues[i][assetsColumns.campaignName-1] + ";" + newAssetsValues[i][assetsColumns.assetGroupName-1]
          //Block of statements
          if(newAssetsValues[i] != null && newAssetsValues[i] != "" && newAssetKey == newAssetGroupKey){
            switch (newAssetsValues[i][assetsColumns.type-1]) {
              case "HEADLINE":
                headlines_cnt += 1;
                break;
              case "LONG_HEADLINE":
                long_headlines_cnt += 1;
                break;
              case "DESCRIPTION":
                descriptions_cnt += 1;
                break;
              case "BUSINESS_NAME":
                business_name_cnt += 1;
                break;
              case "MARKETING_IMAGE":
                marketing_image_cnt += 1;
                break;
              case "SQUARE_MARKETING_IMAGE":
                square_marketing_image_cnt += 1;
                break;
              case "LOGO":
                logo_cnt += 1;
                break;
            }
          }
        }

        let status = true
        let message = ""

        if(headlines_cnt < headlines_required){
          status = false
          message = message + "\n\tNot enough headlines assigned to the Asset Group. (" + (headlines_required - headlines_cnt) + " headline(s) missing)" 
        }
        if(long_headlines_cnt < long_headlines_required){
          status = false
          message = message + "\n\tNot enough long headlines assigned to the Asset Group. (" + (long_headlines_required - long_headlines_cnt) + " long headline(s) missing)" 
        }
        if(descriptions_cnt < descriptions_required){
          status = false
          message = message + "\n\tNot enough descriptions assigned to the Asset Group. (" + (descriptions_required - descriptions_cnt) + " description(s) missing)" 
        }
        if(business_name_cnt < business_name_required){
          status = false
          message = message + "\n\tNo business name assigned to the Asset Group. (" + (business_name_required - business_name_cnt) + " business name missing)" 
        }
        if(marketing_image_cnt < marketing_image_required){
          status = false
          message = message + "\n\tNot enough landscape images assigned to the Asset Group. (" + (marketing_image_required - marketing_image_cnt) + " marketing image missing)" 
        }
        if(square_marketing_image_cnt < square_marketing_image_required){
          status = false
          message = message + "\n\tNot enough square images assigned to the Asset Group. (" + (marketing_image_required - marketing_image_cnt) + " square marketing image missing)" 
        }
        if(logo_cnt < logo_required){
          status = false
          message = message + "\n\tNo logo assigned to the Asset Group. (" + (logo_required - logo_cnt) + " logo missing)" 
        }

        if(!status){
          message = "Minimum Asset requirement are not met:" + message
        } else {
          message = "SUCCESS"
        }

        newAssetGroupsSheet.getRange(row_index + 1, 2).setValue(message)

        Logger.log(message)

      }
    }
  }
}

function onOpen(e){ 
  updateUploadedValuesIntoProperty();

  SpreadsheetApp.getUi()
      .createMenu('pMax Execute')
      .addItem('Refresh Sheet', 'pubsubRefreshRequest')
      .addSeparator() 
      .addItem('Upload to Google Ads', 'pubsubUploadRequest')
      .addToUi();

}

function pubsubRefreshRequest() {
  const attr = {
    id: "madmax",
    value: "run_all"
  };
  pubsub(PROJECT_NAME, PUBSUB_TOPIC, attr, "REFRESH")
  updateUploadedValuesIntoProperty();
}

function pubsubUploadRequest() {
  const attr = {
    id: "madmax",
    value: "run_all"
  };
  pubsub(PROJECT_NAME, PUBSUB_TOPIC, attr, "UPLOAD")
}