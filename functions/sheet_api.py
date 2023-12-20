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
"""Provides Google Sheets API to read and write sheets."""

import re

from enums.asset_column_map import assetsColumnMap
from enums.asset_group_list_column_map import assetGroupListColumnMap
from enums.asset_status import assetStatus
from enums.campaign_list_column_map import campaignListColumnMap
from enums.customer_list_column_map import customerListColumnMap
from enums.new_asset_groups_column_map import newAssetGroupsColumnMap
from enums.new_campaigns_column_map import newCampaignsColumnMap
from enums.sitelink_column_map import sitelinksColumnMap
from googleapiclient import discovery
import yaml

_SHEET_HEADER_SIZE = 5


class SheetsService:
  """Creates sheets service to read and write sheets.

  Attributes:
    spread_sheet_id: Google Spreadsheet id.
    customer_id: Google Ads customer id.
    google_ads_client: Google Ads API client.
    google_ads_service: Google Ads method class.
    _sheets_service: Google Sheets API method class.
  """

  def __init__(self, credentials, google_ads_client, google_ads_service):
    """Creates a instance of sheets service to handle requests.

    Args:
      credentials: API OAuth credentials object.
      google_ads_client: Google Ads API client.
      google_ads_service: Google Ads method class.
    """
    with open("config.yaml", "r") as ymlfile:
      cfg = yaml.safe_load(ymlfile)

    self.spread_sheet_id = cfg["spreadsheet_id"]
    self.customer_id = cfg["customer_id"]
    self.login_customer_id = cfg["login_customer_id"]
    self.google_ads_service = google_ads_service
    self.google_ads_client = google_ads_client
    self._sheets_service = discovery.build(
        "sheets", "v4", credentials=credentials
    ).spreadsheets()

  def get_sheet_values(self, cell_range):
    """Retrieves values from sheet.

    Args:
      cell_range: string representation of sheet range. For example,
        "sheet_name!A:C".

    Returns:
      Array of arrays of values in selectd field range.
    """
    result = (
        self._sheets_service.values()
        .get(spreadsheetId=self.spread_sheet_id, range=cell_range)
        .execute()
    )
    return result.get("values", [])

  def _set_cell_value(self, value, cell_range):
    """Sets Cell value on sheet.

    Args:
      value: The string value as input for the cell.
      cell_range: string representation of cell range. For example,
        "sheet_name!B2".
    """
    value_range_body = {"range": cell_range, "values": [[value]]}
    request = self._sheets_service.values().update(
        spreadsheetId=self.spread_sheet_id,
        valueInputOption="USER_ENTERED",
        range=cell_range,
        body=value_range_body,
    )
    request.execute()

  def get_sheet_row(self, key, sheet_values, type):
    """Returns the values of the sheetrow matching the alias.

    Args:
      key: The string value of the unique key for the row.
      sheet_values: Array of arrays representation of sheet_name.
      type: String input with type, "CUSTOMER", "CAMPAIGN", "NEW_CAMPAIGN",
        "ASSET_GROUP", "NEW_ASSET_GROUP"

    Returns:
      Array of row values, or None.
    """
    result = None
    row_key = None

    for row in sheet_values:
      if type == "CUSTOMER":
        row_key = row[customerListColumnMap.CUSTOMER_NAME]
      if type == "CAMPAIGN":
        row_key = (
            row[campaignListColumnMap.CUSTOMER_NAME]
            + ";"
            + row[campaignListColumnMap.CAMPAIGN_NAME]
        )
      if (
          type == "NEW_CAMPAIGN"
          and len(row) > newCampaignsColumnMap.CAMPAIGN_NAME.value
      ):
        row_key = (
            row[newCampaignsColumnMap.CUSTOMER_NAME]
            + ";"
            + row[newCampaignsColumnMap.CAMPAIGN_NAME]
        )
      if type == "ASSET_GROUP":
        row_key = (
            row[assetGroupListColumnMap.CUSTOMER_NAME]
            + ";"
            + row[assetGroupListColumnMap.CAMPAIGN_NAME]
            + ";"
            + row[assetGroupListColumnMap.ASSET_GROUP_NAME]
        )
      if (
          type == "NEW_ASSET_GROUP"
          and len(row) > newAssetGroupsColumnMap.ASSET_GROUP_NAME.value
      ):
        row_key = (
            row[newAssetGroupsColumnMap.CUSTOMER_NAME]
            + ";"
            + row[newAssetGroupsColumnMap.CAMPAIGN_NAME]
            + ";"
            + row[newAssetGroupsColumnMap.ASSET_GROUP_NAME]
        )

      if row_key == key:
        result = row
        break

    return result

  def get_row_number_by_value(self, input_list, sheet_values, col_index):
    """Returns the values of the sheetrow matching the id.

    Args:
      input_list: List of string values as input for the cell.
      sheet_values: Array of arrays representation of sheet_name.
      col_index: index of the column where to find value

    Returns:
      Row number
    """
    for row_index, row in enumerate(sheet_values):
      index = 0
      match_cnt = 0
      for input_value in input_list:
        if row[col_index + index] == input_value:
          match_cnt += 1
        if match_cnt == len(input_list):
          return row_index
        index += 1

    return 0

  def batch_update_requests(self, request_lists):
    """Batch update row with requests in target sheet.

    Args:
      request_lists: request data list.
    """
    batch_update_spreadsheet_request_body = {"requests": request_lists}
    self._sheets_service.batchUpdate(
        spreadsheetId=self.spread_sheet_id,
        body=batch_update_spreadsheet_request_body,
    ).execute()

  def get_sheet_id_by_name(self, sheet_name):
    """Get sheet id by sheet name.

    Args:
      sheet_name: sheet name.

    Returns:
      sheet_id: id of the sheet with the given name. Not a spreadsheet id.
    """
    spreadsheet = self._sheets_service.get(
        spreadsheetId=self.spread_sheet_id
    ).execute()
    for sheet in spreadsheet["sheets"]:
      if sheet["properties"]["title"] == sheet_name:
        return sheet["properties"]["sheetId"]

  def get_status_note(self, row_index, col_index, input_value, sheet_id):
    """Retrieves target cells to update error note in the Sheet.

    Args:
      row_index: Row index.
      col_index: Column index.
      input_value: Cell input value (string)
      sheet_id: Sheet id for the Sheet.

    Returns:
      error_note: cell information for updating error note.
    """
    error_note = {
        "updateCells": {
            "start": {
                "sheetId": sheet_id,
                "rowIndex": row_index,
                "columnIndex": col_index,
            },
            "rows": [
                {"values": [{"userEnteredValue": {"stringValue": input_value}}]}
            ],
            "fields": "userEnteredValue",
        }
    }
    return error_note

  def get_checkbox(self, row_index, col_index, sheet_id):
    """Retrieves target cells to update checkbox in the Sheet.

    Args:
      row_index: row index of the target cell.
      col_index: column index of the target cell.
      sheet_id: Sheet id for the Sheet.

    Returns:
      checkbox: cell information for updating checkbox.
    """
    checkbox = {
        "updateCells": {
            "start": {
                "sheetId": sheet_id,
                "rowIndex": row_index,
                "columnIndex": col_index,
            },
            "rows": [{
                "values": [
                    {
                        "dataValidation": {
                            "condition": {
                                "type": "BOOLEAN",
                            }
                        }
                    }
                ]
            }],
            "fields": "dataValidation",
        }
    }
    return checkbox

  def get_dropdown(self, row_index, col_index, input_value, sheet_id):
    """Retrieves target cells to update checkbox in the Sheet.

    Args:
      row_index: row index of the target cell.
      col_index: column index of the target cell.
      input_value: comma seperated string with dropdown values.
      sheet_id: Sheet id for the Sheet.

    Returns:
      dropdown: cell information for updating dropdown.
    """
    dropdown_values = []

    for value in input_value:
      dropdown_values.append({
          "userEnteredValue": value,
      })

    dropdown = {
        "setDataValidation": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": row_index,
                "endRowIndex": row_index + 1,
                "startColumnIndex": col_index,
                "endColumnIndex": col_index + 1,
            },
            "rule": {
                "condition": {"type": "ONE_OF_LIST", "values": dropdown_values},
                "showCustomUi": True,
                "strict": False,
            },
        }
    }
    return dropdown

  def get_thumbnail(self, row_index, col_index, sheet_id):
    """Retrieves target cells to update checkbox in the Sheet.

    Args:
      row_index: row index of the target cell.
      col_index: column index of the target cell.
      sheet_id: Sheet id for the Sheet.

    Returns:
      thumbnail: cell information for updating cell with image formula.
    """
    formula = "=IMAGE(I" + str(row_index + 1) + ")"
    thumbnail = {
        "updateCells": {
            "start": {
                "sheetId": sheet_id,
                "rowIndex": row_index,
                "columnIndex": col_index,
            },
            "rows": [
                {"values": [{"userEnteredValue": {"formulaValue": formula}}]}
            ],
            "fields": "userEnteredValue",
        }
    }
    return thumbnail

  def get_sort_request(
      self, row_index, col_index, sheet_id, sort_col_1, sort_col_2
  ):
    """Sorts range in sheet.

    Args:
      row_index: Start row index of the target range.
      col_index: Start column index of the target range.
      sheet_id: Sheet id for the Sheet.
      sort_col_1: Column index of the first sorting column.
      sort_col_2: Column index of the second sorting column.

    Returns:
      sort: Range information for sorting.
    """
    sort = {
        "sortRange": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": row_index,
                "startColumnIndex": col_index,
            },
            "sortSpecs": [
                {"sortOrder": "ASCENDING", "dimensionIndex": sort_col_1},
                {"sortOrder": "ASCENDING", "dimensionIndex": sort_col_2},
            ],
        }
    }
    return sort

  def variable_update_sheet_status(
      self,
      row_index,
      sheet_id,
      status_row_id,
      upload_status,
      error_message="",
      message_row_id=None,
  ):
    """Update status and error message (if provided) in the sheet.

    Args:
      row_index: index of sheet row.
      sheet_id: Sheet id.
      status_row_id: Row of status position.
      upload_status: Status of API operation.
      error_message: Optional string value with error.
      message_row_id: column of error messgae position.

    Raises:
      Exception: If unknown error occurs while updating rows in the Time
        Managed Sheet.
    """
    update_request_list = []

    status = self.get_status_note(
        row_index + _SHEET_HEADER_SIZE, status_row_id, upload_status, sheet_id
    )
    update_request_list.append(status)

    if error_message and message_row_id:
      error_note = self.get_status_note(
          row_index + _SHEET_HEADER_SIZE,
          message_row_id,
          error_message,
          sheet_id,
      )
      update_request_list.append(error_note)

    try:
      self.batch_update_requests(update_request_list)
    except Exception as e:
      print(f"Unable to update Sheet rows: {str(e)}")

  def update_asset_sheet_status(self, sheet_results, sheet_name):
    """Update error message in the sheet.

    Args:
      sheet_results: row information and error message.
      sheet_name: Sheet name.

    Raises:
      Exception: If unknown error occurs while updating rows in the Time
        Managed Sheet.
    """
    sheet_id = self.get_sheet_id(sheet_name)
    column_map = assetsColumnMap
    if sheet_name == "Sitelinks":
      column_map = sitelinksColumnMap
    update_request_list = []
    for row_index in sheet_results:
      error_status = self.get_status_note(
          row_index + _SHEET_HEADER_SIZE,
          column_map.ASSET_STATUS.value,
          sheet_results[row_index]["status"],
          sheet_id,
      )
      update_request_list.append(error_status)

      if sheet_results[row_index]["status"] == assetStatus.UPLOADED.value[0]:
        checkbox = self.get_checkbox(
            row_index + _SHEET_HEADER_SIZE,
            column_map.DELETE_ASSET.value,
            sheet_id,
        )
        update_request_list.append(checkbox)

      error_note = self.get_status_note(
          row_index + _SHEET_HEADER_SIZE,
          column_map.ERROR_MESSAGE.value,
          sheet_results[row_index]["message"],
          sheet_id,
      )
      update_request_list.append(error_note)

      if "asset_group_asset" in sheet_results[row_index]:
        asset_group_asset_resource = self.get_status_note(
            row_index + _SHEET_HEADER_SIZE,
            column_map.ASSET_GROUP_ASSET.value,
            sheet_results[row_index]["asset_group_asset"],
            sheet_id,
        )
        update_request_list.append(asset_group_asset_resource)
    try:
      self.batch_update_requests(update_request_list)
    except Exception as e:
      print(f"Unable to update Sheet rows: {str(e)}")

  def get_sheet_id(self, sheet_name):
    """Get sheet id of Sheet.

    Args:
      sheet_name: Google Sheet name.

    Returns:
      sheet_id: sheet id of Sheet.

    Raises:
      Exception: If error occurs while retrieving the Sheet ID.
    """
    sheet_id = None
    try:
      sheet_id = self.get_sheet_id_by_name(sheet_name)
    except Exception as e:
      print(f"Error while retrieving the Sheet ID: {str(e)}")
    return sheet_id

  def update_asset_group_sheet_status(
      self, status, error_message, row_index, sheet_id
  ):
    """Update error message in the sheet.

    Args:
      status: Asset Group API Operations status.
      error_message: Asset Group error message string.
      row_index: Sheet row index.
      sheet_id: Sheet id.

    Raises:
      Exception: If unknown error occurs while updating rows in the Time
        Managed Sheet.
    """
    update_request_list = []

    error_note = self.get_status_note(
        row_index + _SHEET_HEADER_SIZE,
        newAssetGroupsColumnMap.STATUS.value,
        status,
        sheet_id,
    )
    update_request_list.append(error_note)

    error_note = self.get_status_note(
        row_index + _SHEET_HEADER_SIZE,
        newAssetGroupsColumnMap.MESSAGE.value,
        error_message,
        sheet_id,
    )
    update_request_list.append(error_note)

    try:
      self.batch_update_requests(update_request_list)
    except Exception as e:
      print(f"Unable to update Sheet rows: {str(e)}")

  def add_new_asset_group_to_list_sheet(self, asset_group_sheetlist):
    """Update error message in the sheet.

    Args:
        asset_group_sheetlist: Array containing the information of the new asset
          group.

    Raises:
        Exception: If unknown error occurs while updating rows in the Time
          Managed Sheet.
    """
    resource = {"majorDimension": "ROWS", "values": [asset_group_sheetlist]}
    sheet_range = "AssetGroupList!A:G"

    try:
      self._sheets_service.values().append(
          spreadsheetId=self.spread_sheet_id,
          range=sheet_range,
          body=resource,
          valueInputOption="USER_ENTERED",
      ).execute()
    except Exception as e:
      print(f"Unable to update Sheet rows: {str(e)}")

  def add_new_campaign_to_list_sheet(self, campaign_sheetlist):
    """Update error message in the sheet.

    Args:
        campaign_sheetlist: Array containing the information of the new asset
          group.

    Raises:
        Exception: If unknown error occurs while updating rows in the Time
          Managed Sheet.
    """
    resource = {"majorDimension": "ROWS", "values": [campaign_sheetlist]}
    sheet_range = "CampaignList!A:D"

    try:
      self._sheets_service.values().append(
          spreadsheetId=self.spread_sheet_id,
          range=sheet_range,
          body=resource,
          valueInputOption="USER_ENTERED",
      ).execute()
    except Exception as e:
      print(f"Unable to update Sheet rows: {str(e)}")

  def update_asset_sheet_output(self, results, sheet_name, account_map):
    """Write exisitng assets to asset sheet.

    Args:
      results: Array of array containing the existing assets in Google Ads.
      sheet_name: Name of the sheet to write the results to.
      account_map: Google Ads account map, account ids and names.
    """
    sheet_output = []

    asset_resource_column = "!L:L"
    sheet_range = sheet_name + "!A:L"
    column_map = assetsColumnMap

    if sheet_name == "Sitelinks":
      asset_resource_column = "!J:J"
      sheet_range = sheet_name + "!A:J"
      column_map = sitelinksColumnMap

    asset_group_asset_values = self.get_sheet_values(
        sheet_name + asset_resource_column
    )

    index = 0
    last_row = len(self.get_sheet_values(sheet_name + "!C:C")) + 1
    for row in results:
      resource_name = row.asset_group_asset.resource_name
      if sheet_name == "Sitelinks":
        resource_name = row.campaign_asset.resource_name

      if [resource_name] not in asset_group_asset_values:
        # Create empty list of lists with lenght of sheet row.
        sheet_output.append([None] * len(column_map))

        if sheet_name == "Assets":
          asset_type = row.asset_group_asset.field_type.name

          sheet_output[index][
              column_map.ASSET_GROUP_NAME.value
          ] = row.asset_group.name
          sheet_output[index][column_map.ASSET_THUMBNAIL.value] = ""
          sheet_output[index][column_map.ASSET_TYPE.value] = asset_type
        if sheet_name == "Sitelinks":
          asset_type = row.campaign_asset.field_type.name

        sheet_output[index][column_map.ASSET_STATUS.value] = "UPLOADED"
        sheet_output[index][column_map.DELETE_ASSET.value] = ""
        sheet_output[index][
            column_map.CUSTOMER_NAME.value
        ] = row.customer.descriptive_name
        sheet_output[index][column_map.CAMPAIGN_NAME.value] = row.campaign.name

        sheet_output[index][column_map.ERROR_MESSAGE.value] = ""
        sheet_output[index][column_map.ASSET_GROUP_ASSET.value] = resource_name

        if asset_type in (
            "HEADLINE",
            "LONG_HEADLINE",
            "DESCRIPTION",
            "BUSINESS_NAME",
        ):
          sheet_output[index][
              assetsColumnMap.ASSET_TEXT.value
          ] = row.asset.text_asset.text
          sheet_output[index][assetsColumnMap.ASSET_CALL_TO_ACTION.value] = ""
          sheet_output[index][assetsColumnMap.ASSET_URL.value] = ""
        if asset_type in (
            "LOGO",
            "LANDSCAPE_LOGO",
            "MARKETING_IMAGE",
            "SQUARE_MARKETING_IMAGE",
            "PORTRAIT_MARKETING_IMAGE",
        ):
          sheet_output[index][assetsColumnMap.ASSET_TEXT.value] = row.asset.name
          sheet_output[index][assetsColumnMap.ASSET_CALL_TO_ACTION.value] = ""
          sheet_output[index][
              assetsColumnMap.ASSET_URL.value
          ] = row.asset.image_asset.full_size.url
        if asset_type == "CALL_TO_ACTION_SELECTION":
          sheet_output[index][assetsColumnMap.ASSET_TEXT.value] = row.asset.name
          sheet_output[index][assetsColumnMap.ASSET_CALL_TO_ACTION.value] = (
              self.google_ads_client.enums.CallToActionTypeEnum(
                  row.asset.call_to_action_asset.call_to_action
              ).name
          )
          sheet_output[index][assetsColumnMap.ASSET_URL.value] = ""
        if asset_type == "YOUTUBE_VIDEO":
          sheet_output[index][assetsColumnMap.ASSET_TEXT.value] = row.asset.name
          sheet_output[index][assetsColumnMap.ASSET_CALL_TO_ACTION.value] = ""
          sheet_output[index][assetsColumnMap.ASSET_URL.value] = (
              "https://www.youtube.com/watch?v="
              + row.asset.youtube_video_asset.youtube_video_id
          )
        if asset_type == "SITELINK" and sheet_name == "Sitelinks":
          sheet_output[index][column_map.FINAL_URLS.value] = (
              row.asset.final_urls[0]
          )
          sheet_output[index][
              column_map.LINK_TEXT.value
          ] = row.asset.sitelink_asset.link_text
          sheet_output[index][
              column_map.DESCRIPTION1.value
          ] = row.asset.sitelink_asset.description1
          sheet_output[index][
              column_map.DESCRIPTION2.value
          ] = row.asset.sitelink_asset.description2
          sheet_output[index][
              column_map.ASSET_GROUP_ASSET.value
          ] = row.campaign_asset.resource_name

        index += 1

    # The ID of the spreadsheet to update
    value_input_option = "USER_ENTERED"
    insert_data_option = "INSERT_ROWS"
    value_range_body = {"values": sheet_output}

    try:
      request = self._sheets_service.values().append(
          spreadsheetId=self.spread_sheet_id,
          range=sheet_range,
          valueInputOption=value_input_option,
          insertDataOption=insert_data_option,
          body=value_range_body,
      )
      response = request.execute()
    except Exception as e:
      print(f"Unable to update Sheet rows: {str(e)}")

    self.update_assets_columns(response, sheet_output, sheet_name, account_map)

  def update_assets_columns(
      self, response, sheet_output, sheet_name, account_map
  ):
    """Update custom columns in Assets Sheet.

    Includes the deletion checkbox, thumbnail formula and dropdown config.

    Args:
      response: API response object for Asset Sheet update.
      sheet_output: Input sheet object with the relevant new sheet values.
      sheet_name: Name of the sheet to write the results to.
      account_map: Google Ads account map, account ids and names.
    """
    column_map = assetsColumnMap
    if sheet_name == "Sitelinks":
      column_map = sitelinksColumnMap

    if response["tableRange"]:
      sheet_id = self.get_sheet_id(sheet_name)
      start_row = int(re.search("([0-9]*$)", response["tableRange"]).group())
      update_request_list = []
      i = 0
      if "updatedRows" in response["updates"]:
        customer_list = list(account_map.keys())
        while i < response["updates"]["updatedRows"]:
          update_request_list.append(
              self.get_checkbox(
                  start_row + i, column_map.DELETE_ASSET.value, sheet_id
              )
          )
          if sheet_name == "Assets":
            update_request_list.append(
                self.get_thumbnail(
                    start_row + i, column_map.ASSET_THUMBNAIL.value, sheet_id
                )
            )
          update_request_list.append(
              self.get_dropdown(
                  start_row + i,
                  column_map.CUSTOMER_NAME,
                  customer_list,
                  sheet_id,
              )
          )
          if sheet_output[i][column_map.CUSTOMER_NAME]:
            campaign_list = list(
                account_map[sheet_output[i][column_map.CUSTOMER_NAME]].keys()
            )
            update_request_list.append(
                self.get_dropdown(
                    start_row + i,
                    column_map.CAMPAIGN_NAME,
                    campaign_list,
                    sheet_id,
                )
            )
          if (
              sheet_output[i][column_map.CAMPAIGN_NAME]
              and sheet_name == "Assets"
          ):
            asset_group_list = account_map[
                sheet_output[i][column_map.CUSTOMER_NAME]
            ][sheet_output[i][column_map.CAMPAIGN_NAME]]
            update_request_list.append(
                self.get_dropdown(
                    start_row + i,
                    column_map.ASSET_GROUP_NAME,
                    asset_group_list,
                    sheet_id,
                )
            )

          i += 1

        sort = self.get_sort_request(_SHEET_HEADER_SIZE, 0, sheet_id, 0, 3)
        update_request_list.append(sort)

        try:
          self.batch_update_requests(update_request_list)
        except Exception as e:
          print(f"Unable to update Sheet rows: {str(e)}")

  def refresh_spreadsheet(self):
    """Update spreadsheet with exisitng assets, asset groups and campaigns."""
    account_map = {}
    results = self.google_ads_service.retrieve_all_customers(
        self.login_customer_id
    )
    account_map = self.update_sheet_lists(
        results, "CustomerList", "!B:B", account_map
    )

    for row in results:
      customer_id = str(row.customer_client.id)

      if customer_id:
        results = self.google_ads_service.retrieve_all_campaigns(customer_id)
        account_map = self.update_sheet_lists(
            results, "CampaignList", "!D:D", account_map
        )

        results = self.google_ads_service.retrieve_all_asset_groups(customer_id)
        account_map = self.update_sheet_lists(
            results, "AssetGroupList", "!F:F", account_map
        )

        results = self.google_ads_service.retrieve_all_assets(customer_id)
        self.update_asset_sheet_output(results, "Assets", account_map)

        results = self.google_ads_service.retrieve_sitelinks(customer_id)
        self.update_asset_sheet_output(results, "Sitelinks", account_map)

    self._set_cell_value(
        "=SORT(UNIQUE({CustomerList!$A$5:$A}))", "DropDownConfig!N3"
    )

  def refresh_campaign_list(self):
    """Update spreadsheet with Campaign list."""
    account_map = {}
    results = self.google_ads_service.retrieve_all_customers(
        self.login_customer_id
    )
    account_map = self.update_sheet_lists(
        results, "CustomerList", "!B:B", account_map
    )

    for row in results:
      customer_id = str(row.customer_client.id)

      if customer_id:
        results = self.google_ads_service.retrieve_all_campaigns(customer_id)
        self.update_sheet_lists(results, "CampaignList", "!D:D", account_map)

  def refresh_asset_group_list(self):
    """Update spreadsheet with Asset Group list."""
    account_map = {}
    results = self.google_ads_service.retrieve_all_customers(
        self.login_customer_id
    )
    account_map = self.update_sheet_lists(
        results, "CustomerList", "!B:B", account_map
    )

    for row in results:
      customer_id = str(row.customer_client.id)

      if customer_id:
        results = self.google_ads_service.retrieve_all_asset_groups(customer_id)
        self.update_sheet_lists(results, "AssetGroupList", "!F:F", account_map)

  def refresh_assets_list(self):
    """Update spreadsheet with Assets list."""
    account_map = {}
    results = self.google_ads_service.retrieve_all_customers(
        self.login_customer_id
    )
    account_map = self.update_sheet_lists(
        results, "CustomerList", "!B:B", account_map
    )

    for row in results:
      customer_id = str(row.customer_client.id)

      if customer_id:
        results = self.google_ads_service.retrieve_all_assets(customer_id)
        self.update_asset_sheet_output(results, "Assets", account_map)

  def refresh_sitelinks_list(self):
    """Update spreadsheet with Sitelinks list."""
    account_map = {}
    results = self.google_ads_service.retrieve_all_customers(
        self.login_customer_id
    )
    account_map = self.update_sheet_lists(
        results, "CustomerList", "!B:B", account_map
    )

    for row in results:
      customer_id = str(row.customer_client.id)

      if customer_id:
        results = self.google_ads_service.retrieve_sitelinks(customer_id)
        self.update_asset_sheet_output(results, "Sitelinks", account_map)

  def refresh_customer_id_list(self):
    """Update spreadsheet with customer id list."""
    results = self.google_ads_service.retrieve_all_customers(
        self.login_customer_id
    )
    self.update_sheet_lists(results, "CustomerList", "!B:B", {})

    self._set_cell_value(
        "=SORT(UNIQUE({CustomerList!$A$5:$A}))", "DropDownConfig!N3"
    )

  def update_sheet_lists(self, results, sheet_name, column, account_map):
    """Write exisitng customer list, campaigns, asset groups, assets and sitelinks to relative list sheet.

    Args:
      results: Array of array containing the existing asset groups in Google
        Ads.
      sheet_name: Name of the sheet to write the results to.
      column: string value representation of sheet column, with unique id.
      account_map: Google Ads account map, account ids and names.
    """
    existing_values = self.get_sheet_values(sheet_name + column)
    sheet_range = ""
    sheet_output = []
    index = 0
    for row in results:
      if sheet_name == "CustomerList":
        if row.customer_client.descriptive_name not in account_map:
          account_map[row.customer_client.descriptive_name] = {}
        row_item_id = str(row.customer_client.id)
        sheet_range = sheet_name + "!A:B"
      elif sheet_name == "CampaignList":
        if row.campaign.name not in account_map[row.customer.descriptive_name]:
          account_map[row.customer.descriptive_name][row.campaign.name] = []
        row_item_id = str(row.campaign.id)
        sheet_range = sheet_name + "!A:D"
      elif sheet_name == "AssetGroupList":
        if (
            row.asset_group.name
            not in account_map[row.customer.descriptive_name][row.campaign.name]
        ):
          account_map[row.customer.descriptive_name][row.campaign.name].append(
              row.asset_group.name
          )
        row_item_id = str(row.asset_group.id)
        sheet_range = sheet_name + "!A:F"

      if [row_item_id] not in existing_values:
        sheet_output.append([])
        sheet_output[index] = self.generate_list_sheet_output(row, sheet_name)

        index += 1

    value_input_option = "USER_ENTERED"
    insert_data_option = "INSERT_ROWS"
    value_range_body = {"values": sheet_output}

    try:
      request = self._sheets_service.values().append(
          spreadsheetId=self.spread_sheet_id,
          range=sheet_range,
          valueInputOption=value_input_option,
          insertDataOption=insert_data_option,
          body=value_range_body,
      )
      request.execute()
    except Exception as e:
      print(f"Unable to update Sheet rows: {str(e)}")

    return account_map

  def generate_list_sheet_output(self, row, sheet_name):
    """Compile list of sheet output for Google Ads resources.

    Args:
      row: API result row from search query.
      sheet_name: Name of the sheet for which data is processed.

    Returns:
      Array of sheet values.
    """
    if sheet_name == "CustomerList":
      output = [None] * len(customerListColumnMap)
      output[customerListColumnMap.CUSTOMER_NAME.value] = (
          row.customer_client.descriptive_name
      )
      output[customerListColumnMap.CUSTOMER_ID.value] = row.customer_client.id
    if sheet_name == "CampaignList":
      output = [None] * len(campaignListColumnMap)
      output[campaignListColumnMap.CAMPAIGN_NAME.value] = row.campaign.name
      output[campaignListColumnMap.CAMPAIGN_ID.value] = row.campaign.id
      output[campaignListColumnMap.CUSTOMER_NAME.value] = (
          row.customer.descriptive_name
      )
      output[campaignListColumnMap.CUSTOMER_ID.value] = row.customer.id
    if sheet_name == "AssetGroupList":
      output = [None] * len(assetGroupListColumnMap)
      output[assetGroupListColumnMap.ASSET_GROUP_NAME.value] = (
          row.asset_group.name
      )
      output[assetGroupListColumnMap.ASSET_GROUP_ID.value] = row.asset_group.id
      output[assetGroupListColumnMap.CAMPAIGN_NAME.value] = row.campaign.name
      output[assetGroupListColumnMap.CAMPAIGN_ID.value] = row.campaign.id
      output[assetGroupListColumnMap.CUSTOMER_NAME.value] = (
          row.customer.descriptive_name
      )
      output[assetGroupListColumnMap.CUSTOMER_ID.value] = row.customer.id

    return output

  def process_api_operations(
      self,
      mutate_type,
      mutate_operations,
      sheet_results,
      row_to_operations_mapping,
      asset_group_sheetlist,
      sheet_name,
  ):
    """Logic to process API bulk operations based on type.

    Based on the request type, the bulk API requests will be send to the API.
    Corresponding API response will be
    parsed and processed both as terminal output and as output to the Google
    Sheet.

    Args:
      mutate_type: Type of mutate operations (string) "ASSETS", "SITELINKS"
        ASSET_GROUPS.
      mutate_operations: Object of Google Ads API mutate operations.
      sheet_results: Results object for sheet output.
      row_to_operations_mapping: Sheet row to API operations mapping
      asset_group_sheetlist: List of Asset Groups for Sheets.
      sheet_name: Name of sheet.
    """
    # Bulk requests are grouped by Asset Group Alias and are processed
    # one by one in bulk.

    new_asset_group_values = self.get_sheet_values("NewAssetGroups!A6:L")

    for customer_id in mutate_operations:
      for asset_group_alias in mutate_operations[customer_id]:
        # Send the bulk request to the API and retrieve the API response object
        # and the compiled
        # Error message for asset Groups.
        asset_group_response, asset_group_error_message = (
            self.google_ads_service.bulk_mutate(
                mutate_type,
                mutate_operations[customer_id][asset_group_alias],
                customer_id,
            )
        )

        # Check if a successful API response, if so, process output.
        if asset_group_response:
          sheet_results.update(
              self.google_ads_service.process_asset_results(
                  asset_group_response,
                  mutate_operations[customer_id][asset_group_alias],
                  row_to_operations_mapping,
                  mutate_type,
              )
          )

          if mutate_type == "ASSET_GROUPS":
            row_number = self.get_row_number_by_value(
                asset_group_alias.split(";"),
                new_asset_group_values,
                newAssetGroupsColumnMap.CUSTOMER_NAME.value,
            )

            sheet_id = self.get_sheet_id("NewAssetGroups")
            self.update_asset_group_sheet_status(
                "UPLOADED", "", row_number, sheet_id
            )

            asset_group_sheetlist[asset_group_alias][
                assetGroupListColumnMap.ASSET_GROUP_ID.value
            ] = asset_group_response.mutate_operation_responses[
                0
            ].asset_group_result.resource_name.split(
                "/"
            )[
                -1
            ]
            sheet_id = self.get_sheet_id("AssetGroupList")

            self.add_new_asset_group_to_list_sheet(
                asset_group_sheetlist[asset_group_alias]
            )

        # In case Asset Group creation returns an error string, updated the
        # results object and process to sheet.
        elif asset_group_error_message and mutate_type == "ASSET_GROUPS":
          sheet_results.update(
              self.google_ads_service.process_asset_group_results(
                  asset_group_error_message,
                  mutate_operations[customer_id][asset_group_alias],
                  row_to_operations_mapping,
              )
          )
          row_number = self.get_row_number_by_value(
              asset_group_alias.split(";"),
              new_asset_group_values,
              newAssetGroupsColumnMap.CUSTOMER_NAME.value,
          )

          sheet_id = self.get_sheet_id("NewAssetGroups")

          self.update_asset_group_sheet_status(
              "ERROR", asset_group_error_message, row_number, sheet_id
          )

    self.update_asset_sheet_status(sheet_results, sheet_name)
