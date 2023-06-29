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


class SheetsService():
    """Creates sheets service to read and write sheets.
    Attributes:
      _sheets_services: service that is used for making Sheets API calls.
      _spreadsheet_id: id of the spreadsheet to read from and write to.
    """
    class newAssetsColumnMap(enum.IntEnum):
        ASSET_GROUP_ALIAS = 0,
        ASSET_TYPE = 1,
        ASSET_TEXT = 2,
        CALL_TO_ACTION = 3,
        ASSET_URL = 4,
        STATUS = 5,
        MESSAGE = 6

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

    def __init__(self, credentials):
        """Creates a instance of sheets service to handle requests."""
        self._sheets_service = discovery.build(
            'sheets', 'v4', credentials=credentials).spreadsheets()

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
        return result.get('values', [])

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
        batch_update_spreadsheet_request_body = {'requests': request_lists}
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
        for _sheet in spreadsheet['sheets']:
            if _sheet['properties']['title'] == sheet_name:
                return _sheet['properties']['sheetId']

    def get_status_note(self, row_index, col_index, input_values, sheet_id):
        """Gets target cells to update error note in the Sheet.
        Args:
        update_row: error note content.
        update_index: row index of the target cell.
        sheet_id: Sheet id for the Sheet.
        Returns:
        error_note: cell information for updating error note.
        """
        error_note = {
            'updateCells': {
                'start': {
                    'sheetId': sheet_id,
                    'rowIndex': row_index + 5,
                    'columnIndex': col_index
                },
                'rows': [{
                    'values': [{
                        'userEnteredValue': {
                            'stringValue': input_values["status"]
                        }
                    }, {
                        'userEnteredValue': {
                            'stringValue': input_values["message"]
                        }
                    }]
                }],
                'fields': 'userEnteredValue'
            }
        }
        return error_note

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
            error_note = self.get_status_note(row_index, self.newAssetsColumnMap.STATUS, sheet_results[row_index],
                                              sheet_id)
            update_request_list.append(error_note)
        try:
            self.batch_update_requests(update_request_list, spreadsheet_id)
        except Exception as e:
            print(f'Unable to update Sheet rows: {str(e)}')

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
            print(f'Error while retrieving the Sheet ID: {str(e)}')
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

        if error_message != "SUCCESS":
            sheet_results = {
                "status": "FAILED",
                "message": error_message
            }
        else:
            sheet_results = {
                "status": "SUCCESS",
                "message": ""
            }

        error_note = self.get_status_note(row_index, self.newAssetGroupsColumnMap.STATUS, sheet_results,
                                          sheet_id)
        update_request_list.append(error_note)

        try:
            self.batch_update_requests(update_request_list, spreadsheet_id)
        except Exception as e:
            print(f'Unable to update Sheet rows: {str(e)}')

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
            print(f'Unable to update Sheet rows: {str(e)}')