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

    class assetGroupsColumnMap(enum.IntEnum):
        ASSET_GROUP_ALIAS = 0,
        ASSET_GROUP_NAME = 1,
        ASSET_GROUP_ID = 2,
        CAMPAIGN_NAME = 3,
        CAMPAIGN_ID = 4,
        START_DATE = 5,
        CUSTOMER_NAME = 6,
        CUSTOMER_ID = 7

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
    
    def _get_sheet_row(self, id, sheet_name, spreadsheet_id):
        """Returns the values of the sheetrow matching the id.
        
        Args:
          id: The string value as input for the cell.
          sheet_name: string representation of sheetname range.
          spreadsheet_id: string representation of the spreadsheet id.

        Returns:
        Array of row values, or None.
        """
        result = None
        values = self._get_sheet_values(sheet_name+"!A6:H", spreadsheet_id)
        for row in values:
          if row[self.assetGroupsColumnMap.ASSET_GROUP_ALIAS] == id:
            result = row
        return result
