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
from googleapiclient import discovery
import enum
import re
from pprint import pprint


class SheetsService():
    """Creates sheets service to read and write sheets.
    Attributes:
      _sheets_services: service that is used for making Sheets API calls.
      _spreadsheet_id: id of the spreadsheet to read from and write to.
    """

    class assetsColumnMap(enum.IntEnum):
        ASSET_GROUP_ALIAS = 0,
        ASSET_STATUS = 1,
        DELETE_ASSET = 2,
        ASSET_TYPE = 3,
        ASSET_TEXT = 4,
        ASSET_CALL_TO_ACTION = 5,
        ASSET_URL = 6,
        ERROR_MESSAGE = 7,
        ASSET_GROUP_ASSET = 8

    class assetGroupListColumnMap(enum.IntEnum):
        ASSET_GROUP_ALIAS = 0,
        ASSET_GROUP_NAME = 1,
        ASSET_GROUP_ID = 2,
        CAMPAIGN_NAME = 3,
        CAMPAIGN_ID = 4,
        CUSTOMER_NAME = 5,
        CUSTOMER_ID = 6

    class newAssetGroupsColumnMap(enum.IntEnum):
        ASSET_GROUP_ALIAS = 0,
        CAMPAIGN_ALIAS = 1,
        ASSET_CHECK = 2,
        ASSET_GROUP_NAME = 3,
        FINAL_URL = 4,
        MOBILE_URL = 5,
        PATH1 = 6,
        PATH2 = 7,
        CAMPAIGN_STATUS = 8,
        STATUS = 9,
        MESSAGE = 10

    class newCampaignsColumnMap(enum.IntEnum):
        CAMPAIGN_ALIAS = 0,
        CAMPAIGN_SETTINGS_ALIAS = 1,
        CAMPAIGN_NAME = 2,
        START_DATE = 3,
        END_DATE = 4,
        CUSTOMER_ID = 5

    class campaignListColumnMap(enum.IntEnum):
        CAMPAIGN_ALIAS = 0,
        CAMPAIGN_NAME = 1,
        CAMPAIGN_ID = 2,
        CUSTOMER_NAME = 3,
        CUSTOMER_ID = 4

    class assetStatus(enum.Enum):
        UPLOADED = "UPLOADED",
        ERROR = "ERROR",
        NEW = "NEW"

    def __init__(self, credentials):
        """Creates a instance of sheets service to handle requests."""
        self._sheets_service = discovery.build(
            "sheets", "v4", credentials=credentials).spreadsheets()

    def _get_sheet_values(self, cell_range, spreadsheet_id):
        """Gets values from sheet.
        Args:
          cell_range: string representation of sheet range. For example,
            "SheetName!A:C".
          spreadsheet_id: string representation of the spreadsheet id. 
        Returns:
          Array of arrays of values in selectd field range.
        """
        result = self._sheets_service.values().get(
            spreadsheetId=spreadsheet_id, range=cell_range).execute()
        return result.get("values", [])

    def _set_cell_value(self, value, cell_range, spreadsheet_id):
        """Sets Cell value on sheet.
        Args:
          value: The string value as input for the cell.
          cell_range: string representation of cell range. For example,
            "SheetName!B2".
          spreadsheet_id: string representation of the spreadsheet id.
        """
        value_range_body = {
            "range": cell_range,
            "values": [
                [value]
            ]
        }
        request = self._sheets_service.values().update(spreadsheetId=spreadsheet_id,
                                                       valueInputOption="USER_ENTERED", range=cell_range, body=value_range_body)
        response = request.execute()

    def _get_sheet_row(self, id, sheet_name, sheet_range, spreadsheet_id):
        """Returns the values of the sheetrow matching the id.

        Args:
          id: The string value as input for the cell.
          sheet_name: string representation of sheetname.
          sheet_range: string representation of sheet range.
          spreadsheet_id: string representation of the spreadsheet id.

        Returns:
        Array of row values, or None.
        """
        result = None
        values = self._get_sheet_values(sheet_name+sheet_range, spreadsheet_id)

        for row in values:
            if row[self.assetGroupListColumnMap.ASSET_GROUP_ALIAS] == id:
                result = row
                break

        return result

    def _get_row_number(self, id, sheet_name, sheet_range, spreadsheet_id):
        """Returns the values of the sheetrow matching the id.

        Args:
          id: The string value as input for the cell.
          sheet_name: string representation of sheetname.
          sheet_range: string representation of sheet range.
          spreadsheet_id: string representation of the spreadsheet id.

        Returns:
        Row number
        """
        index = 0
        values = self._get_sheet_values(sheet_name+sheet_range, spreadsheet_id)

        for row in values:
            if row[self.assetGroupListColumnMap.ASSET_GROUP_ALIAS] == id:
                result = row
                break
            index += 0

        return index

    def batch_update_requests(self, request_lists, spreadsheet_id):
        """Batch update row with requests in target sheet.
        Args:
          request_lists: request data list.
        """
        batch_update_spreadsheet_request_body = {"requests": request_lists}
        self._sheets_service.batchUpdate(
            spreadsheetId=spreadsheet_id,
            body=batch_update_spreadsheet_request_body).execute()

    def get_sheet_id_by_name(self, sheet_name, spreadsheet_id):
        """Get sheet id by sheet name.
        Args:
          sheet_name: sheet name.
        Returns:
          sheet_id: id of the sheet with the given name. Not a spreadsheet id.
        """
        spreadsheet = self._sheets_service.get(
            spreadsheetId=spreadsheet_id).execute()
        for _sheet in spreadsheet["sheets"]:
            if _sheet["properties"]["title"] == sheet_name:
                return _sheet["properties"]["sheetId"]

    def get_status_note(self, row_index, col_index, input_value, sheet_id):
        """Gets target cells to update error note in the Sheet.
        Args:
        update_row: error note content.
        update_index: row index of the target cell.
        sheet_id: Sheet id for the Sheet.
        Returns:
        error_note: cell information for updating error note.
        """
        error_note = {
            "updateCells": {
                "start": {
                    "sheetId": sheet_id,
                    "rowIndex": row_index,
                    "columnIndex": col_index
                },
                "rows": [{
                    "values": [{
                        "userEnteredValue": {
                            "stringValue": input_value
                        }
                    }]
                }],
                "fields": "userEnteredValue"
            }
        }
        return error_note

    def get_checkbox(self, row_index, col_index, sheet_id):
        """Gets target cells to update checkbox in the Sheet.
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
                    "columnIndex": col_index
                },
                "rows": [{
                    "values": [{
                        "dataValidation": {
                            "condition": {
                                "type": "BOOLEAN",
                            }
                        }
                    }]
                }],
                "fields": "dataValidation"
            }
        }
        return checkbox

    def get_sort_request(self, row_index, col_index, sheet_id, sort_col_1, sort_col_2):
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
                    {
                        "sortOrder": "ASCENDING",
                        "dimensionIndex": sort_col_1
                    },
                    {
                        "sortOrder": "ASCENDING",
                        "dimensionIndex": sort_col_2
                    }
                ]
            }
        }
        return sort

    def update_asset_sheet_status(self, sheet_results, sheet_id, spreadsheet_id):
        """Update error message in the sheet.
        Args:
            sheet_results: row information and error message.
            sheet_id: Sheet id.
            spreadsheet_id: the id for the Google Spreadsheet
        Raises:
            Exception: If unknown error occurs while updating rows in the Time Managed
            Sheet.
        """
        update_request_list = []
        for row_index in sheet_results:
            error_status = self.get_status_note(row_index + 5, self.assetsColumnMap.ASSET_STATUS, sheet_results[row_index]["status"],
                                              sheet_id)
            update_request_list.append(error_status)

            if sheet_results[row_index]["status"] == self.assetStatus.UPLOADED.value[0]:
                checkbox = self.get_checkbox(row_index + 5, self.assetsColumnMap.DELETE_ASSET,
                                                sheet_id)
                update_request_list.append(checkbox)

            error_note = self.get_status_note(row_index + 5, self.assetsColumnMap.ERROR_MESSAGE, sheet_results[row_index]["message"],
                                              sheet_id)
            update_request_list.append(error_note)

            asset_group_asset_resource = self.get_status_note(row_index + 5, self.assetsColumnMap.ASSET_GROUP_ASSET, sheet_results[row_index]["asset_group_asset"],
                                              sheet_id)
            update_request_list.append(asset_group_asset_resource)
        try:
            self.batch_update_requests(update_request_list, spreadsheet_id)
        except Exception as e:
            print(f"Unable to update Sheet rows: {str(e)}")

    def get_sheet_id(self, sheet_name, spreadsheet_id):
        """Get sheet id of Sheet.
        Args:
            sheets_name: Google Sheet name.
        Returns:
            sheet_id: sheet id of Sheet.
        Raises:
            Exception: If error occurs while retrieving the Sheet ID.
        """
        try:
            sheet_id = self.get_sheet_id_by_name(
                sheet_name, spreadsheet_id)
        except Exception as e:
            print(f"Error while retrieving the Sheet ID: {str(e)}")
        return sheet_id

    def update_asset_group_sheet_status(self, error_message, row_index, sheet_id, spreadsheet_id):
        """Update error message in the sheet.
        Args:
            sheet_results: row information and error message.
            sheet_id: Sheet id.
            spreadsheet_id: the id for the Google Spreadsheet
        Raises:
            Exception: If unknown error occurs while updating rows in the Time Managed
            Sheet.
        """
        update_request_list = []

        error_note = self.get_status_note(row_index + 5, self.newAssetGroupsColumnMap.STATUS, "UPLOADED",
                                          sheet_id)
        update_request_list.append(error_note)

        error_note = self.get_status_note(row_index + 5, self.newAssetGroupsColumnMap.MESSAGE, error_message,
                                          sheet_id)
        update_request_list.append(error_note)

        try:
            self.batch_update_requests(update_request_list, spreadsheet_id)
        except Exception as e:
            print(f"Unable to update Sheet rows: {str(e)}")

    def add_new_asset_group_to_list_sheet(self, asset_group_sheetlist, sheet_id, spreadsheet_id):
        """Update error message in the sheet.
        Args:
            asset_group_sheetlist: Array containing the information of the new asset group.
            sheet_id: Sheet id.
            spreadsheet_id: the id for the Google Spreadsheet
        Raises:
            Exception: If unknown error occurs while updating rows in the Time Managed
            Sheet.
        """
        resource = {
            "majorDimension": "ROWS",
            "values": [asset_group_sheetlist]
        }
        range = "AssetGroupList!A:G";

        try:
            self._sheets_service.values().append(
            spreadsheetId=spreadsheet_id,
            range=range,
            body=resource,
            valueInputOption="USER_ENTERED"
            ).execute()
        except Exception as e:
            print(f"Unable to update Sheet rows: {str(e)}")

    def update_asset_sheet_output(self, results, sheet_name, spreadsheet_id):
        """Write exisitng assets to asset sheet
        
        Args:
            results: Array of array containing the existing assets in Google Ads.
            sheet_name: Name of the sheet to write the results to.
            spreadsheet_id: Google spreadsheet id.
        """
        asset_group_asset_values = self._get_sheet_values(
            sheet_name + "!I:I", spreadsheet_id)

        asset_group_alias_values = self._get_sheet_values(
            "AssetGroupList!A:C", spreadsheet_id)

        sheet_output = []
        index = 0
        for row in results:
            if [row.asset_group_asset.resource_name] not in asset_group_asset_values:
                alias = None
                for alias_row in asset_group_alias_values:
                    if len(alias_row) > 2:
                        if alias_row[2] == str(row.asset_group.id):
                            alias = alias_row[0]

                sheet_output.append([None] * len(self.assetsColumnMap))
                sheet_output[index][0] = alias
                sheet_output[index][1] = "GOOGLE ADS"
                sheet_output[index][2] = ""
                sheet_output[index][3] = row.asset_group_asset.field_type.name

                sheet_output[index][7] = ""
                sheet_output[index][8] = row.asset_group_asset.resource_name

                if row.asset_group_asset.field_type.name in ("HEADLINE", "LONG_HEADLINE", "DESCRIPTION", "BUSINESS_NAME"):
                    sheet_output[index][4] = row.asset.text_asset.text
                    sheet_output[index][5] = ""
                    sheet_output[index][6] = ""
                if row.asset_group_asset.field_type.name in ("LOGO", "LANDSCAPE_LOGO", "MARKETING_IMAGE", "SQUARE_MARKETING_IMAGE", "PORTRAIT_MARKETING_IMAGE"):
                    sheet_output[index][4] = row.asset.name
                    sheet_output[index][5] = ""
                    sheet_output[index][6] = row.asset.image_asset.full_size.url
                if row.asset_group_asset.field_type.name == "CALL_TO_ACTION_SELECTION":
                    sheet_output[index][4] = row.asset.name
                    sheet_output[index][5] = row.asset.call_to_action_asset.call_to_action
                    sheet_output[index][6] = ""
                if row.asset_group_asset.field_type.name == "YOUTUBE_VIDEO":
                    sheet_output[index][4] = row.asset.name
                    sheet_output[index][5] = ""
                    sheet_output[index][6] = "https://www.youtube.com/watch?v=" + row.asset.youtube_video_asset.youtube_video_id
                    
                index += 1

        # The ID of the spreadsheet to update
        range_ = sheet_name + "!A:I"
        value_input_option = "USER_ENTERED"
        insert_data_option = "INSERT_ROWS"
        value_range_body = {
            "values": sheet_output
        }

        try:
            request = self._sheets_service.values().append(spreadsheetId=spreadsheet_id, range=range_, valueInputOption=value_input_option, insertDataOption=insert_data_option, body=value_range_body)
            response = request.execute()
        except Exception as e:
            print(f"Unable to update Sheet rows: {str(e)}")

        if response["tableRange"]:
            sheet_id = self.get_sheet_id(sheet_name, spreadsheet_id)
            start_row = int(re.search("([0-9]*$)", response["tableRange"]).group())
            update_request_list = []
            i = 0
            if "updatedRows" in response["updates"]:
                while i < response["updates"]["updatedRows"]:
                    checkbox = self.get_checkbox(start_row + i, self.assetsColumnMap.DELETE_ASSET, sheet_id)
                    update_request_list.append(checkbox)
                    i += 1

                sort = self.get_sort_request(5,0, sheet_id, 0, 3)
                update_request_list.append(sort)

                try:
                    self.batch_update_requests(update_request_list, spreadsheet_id)
                except Exception as e:
                    print(f"Unable to update Sheet rows: {str(e)}")


    def update_asset_group_sheet_output(self, results, sheet_name, spreadsheet_id):
        """Write exisitng asset groups to asset group list sheet
        
        Args:
            results: Array of array containing the existing asset groups in Google Ads.
            sheet_name: Name of the sheet to write the results to.
            spreadsheet_id: Google spreadsheet id.
        """
        asset_group_values = self._get_sheet_values(
            sheet_name + "!C:C", spreadsheet_id)

        sheet_output = []
        index = 0
        for row in results:
            if [str(row.asset_group.id)] not in asset_group_values:
                sheet_output.append([None] * len(self.assetGroupListColumnMap))
                sheet_output[index][0] = str(row.customer.id) + "_" + str(row.campaign.id) + "_" + str(row.asset_group.id) + "_" + row.asset_group.name
                sheet_output[index][1] = row.asset_group.name
                sheet_output[index][2] = row.asset_group.id
                sheet_output[index][3] = row.campaign.name
                sheet_output[index][4] = row.campaign.id
                sheet_output[index][5] = row.customer.descriptive_name
                sheet_output[index][6] = row.customer.id

                index += 1

        # The ID of the spreadsheet to update.
        range_ = sheet_name + "!A:I"
        value_input_option = "USER_ENTERED"
        insert_data_option = "INSERT_ROWS"
        value_range_body = {
            "values": sheet_output
        }

        try:
            request = self._sheets_service.values().append(spreadsheetId=spreadsheet_id, range=range_, valueInputOption=value_input_option, insertDataOption=insert_data_option, body=value_range_body)
            response = request.execute()
        except Exception as e:
            print(f"Unable to update Sheet rows: {str(e)}")

        sheet_id = self.get_sheet_id(sheet_name, spreadsheet_id)
        update_request_list = []
        sort = self.get_sort_request(5,0, sheet_id, 0, 2)
        update_request_list.append(sort)

        try:
            self.batch_update_requests(update_request_list, spreadsheet_id)
        except Exception as e:
            print(f"Unable to update Sheet rows: {str(e)}")