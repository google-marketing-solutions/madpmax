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

from collections.abc import Mapping, MutableMapping, Sequence
import re
from typing import TypeAlias
from absl import logging
import ads_api
import data_references
from google.ads.googleads import client
from googleapiclient import discovery
from googleapiclient import errors
import yaml

_SHEET_HEADER_SIZE = 5
_RequestNote: TypeAlias = Mapping[
    str, Mapping[str, str | int | Sequence | Mapping[str, str]]
]
_CheckboxCell: TypeAlias = Mapping[str, Mapping[str, str] | Sequence]
_DropdownCell: TypeAlias = Mapping[str, str | int | bool | Mapping[str, str]]
_Thumbnail: TypeAlias = Mapping[str, str | Sequence | Mapping[str, str]]


class SheetsService:
  """Creates sheets service to read and write sheets.

  Attributes:
    spread_sheet_id: Google Spreadsheet id.
    customer_id_inclusion_list: String representation of list of Google Ads
      customer ids.
    login_customer_id: Google Ads customer id of MCC level.
    google_ads_client: Google Ads API client.
    google_ads_service: Google Ads method class.
    _sheets_service: Google Sheets API method class.
  """

  def __init__(
      self,
      credentials: Mapping[str, str],
      google_ads_client: client.GoogleAdsClient,
      google_ads_service: ads_api.AdService,
  ) -> None:
    """Creates a instance of sheets service to handle requests.

    Args:
      credentials: API OAuth credentials object.
      google_ads_client: Google Ads API client.
      google_ads_service: Google Ads method class.
    """
    with open("config.yaml", "r") as ymlfile:
      cfg = yaml.safe_load(ymlfile)

    self.spread_sheet_id = cfg["spreadsheet_id"]
    self.customer_id_inclusion_list = cfg["customer_id_inclusion_list"]
    self.login_customer_id = cfg["login_customer_id"]
    self.google_ads_service = google_ads_service
    self.google_ads_client = google_ads_client
    self._sheets_service = discovery.build(
        "sheets", "v4", credentials=credentials
    ).spreadsheets()

  def get_sheet_values(self, cell_range: str) -> Sequence[Sequence[str | int]]:
    """Retrieves values from sheet.

    Args:
      cell_range: String representation of sheet range. For example,
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

  def _set_cell_value(self, value: str, cell_range: str) -> None:
    """Sets Cell value on sheet.

    Args:
      value: The string value as input for the cell.
      cell_range: String representation of cell range. For example,
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

  def get_sheet_row(
      self,
      key: str,
      sheet_values: Sequence[Sequence[str | int]],
      sheet_name: str,
  ) -> Sequence[str | int]:
    """Returns the values of the sheet row matching the alias.

    Args:
      key: The string value of the unique key for the row.
      sheet_values: Array of arrays representation of sheet_name.
      sheet_name: Enum input with type from Sheets Enum.

    Returns:
      Array of row values, or None.
    """
    result = None
    row_key = None

    for row in sheet_values:
      if sheet_name == data_references.SheetNames.customers:
        row_key = row[data_references.CustomerList.customer_name]
      if sheet_name == data_references.SheetNames.campaigns:
        row_key = (
            row[data_references.CampaignList.customer_name]
            + ";"
            + row[data_references.CampaignList.campaign_name]
        )
      if (
          sheet_name == data_references.SheetNames.new_campaigns
          and len(row) > data_references.NewCampaigns.campaign_name
      ):
        row_key = (
            row[data_references.NewCampaigns.customer_name]
            + ";"
            + row[data_references.NewCampaigns.campaign_name]
        )
      if sheet_name == data_references.SheetNames.asset_groups:
        row_key = (
            row[data_references.AssetGroupList.customer_name]
            + ";"
            + row[data_references.AssetGroupList.campaign_name]
            + ";"
            + row[data_references.AssetGroupList.asset_group_name]
        )
      if (
          sheet_name == data_references.SheetNames.new_asset_groups
          and len(row)
          > data_references.newAssetGroupsColumnMap.ASSET_GROUP_NAME.value
      ):
        row_key = (
            row[data_references.newAssetGroupsColumnMap.CUSTOMER_NAME.value]
            + ";"
            + row[data_references.newAssetGroupsColumnMap.CAMPAIGN_NAME.value]
            + ";"
            + row[
                data_references.newAssetGroupsColumnMap.ASSET_GROUP_NAME.value
            ]
        )

      if row_key == key:
        result = row
        break

    return result

  def batch_update_requests(self, request_lists: _RequestNote) -> None:
    """Batch update row with requests in target sheet.

    Args:
      request_lists: Request data list.
    """
    batch_update_spreadsheet_request_body = {"requests": request_lists}
    self._sheets_service.batchUpdate(
        spreadsheetId=self.spread_sheet_id,
        body=batch_update_spreadsheet_request_body,
    ).execute()

  def get_sheet_id_by_name(self, sheet_name: str) -> str:
    """Get sheet id by sheet name.

    Args:
      sheet_name: Sheet name.

    Returns:
      sheet_id: Id of the sheet with the given name. Not a spreadsheet id.
    """
    spreadsheet = self._sheets_service.get(
        spreadsheetId=self.spread_sheet_id
    ).execute()
    for sheet in spreadsheet["sheets"]:
      if sheet["properties"]["title"] == sheet_name:
        return sheet["properties"]["sheetId"]

  def get_status_note(
      self, row_index: int, col_index: int, input_value: str, sheet_id: str
  ) -> _RequestNote:
    """Retrieves target cells to update error note in the Sheet.

    Args:
      row_index: Row index.
      col_index: Column index.
      input_value: Cell input value (string)
      sheet_id: Sheet id for the Sheet.

    Returns:
      error_note: Cell information for updating error note.
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

  def get_checkbox(
      self, row_index: int, col_index: int, sheet_id: str
  ) -> _CheckboxCell:
    """Retrieves target cells to update checkbox in the Sheet.

    Args:
      row_index: Row index of the target cell.
      col_index: Column index of the target cell.
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

  def get_dropdown(
      self, row_index: int, col_index: int, input_value: str, sheet_id: str
  ) -> _DropdownCell:
    """Retrieves target cells to update checkbox in the Sheet.

    Args:
      row_index: Row index of the target cell.
      col_index: Column index of the target cell.
      input_value: Comma seperated string with dropdown values.
      sheet_id: Sheet id for the Sheet.

    Returns:
      dropdown: Cell information for updating dropdown.
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

  def get_thumbnail(
      self, row_index: int, col_index: int, sheet_id: str
  ) -> _Thumbnail:
    """Retrieves target cells to update checkbox in the Sheet.

    Args:
      row_index: Row index of the target cell.
      col_index: Column index of the target cell.
      sheet_id: Sheet id for the Sheet.

    Returns:
      thumbnail: Cell information for updating cell with image formula.
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
      self,
      row_index: int,
      col_index: int,
      sheet_id: str,
      sort_col_1: int,
      sort_col_2: int,
  ) -> Mapping[str, Mapping[str, str] | Sequence]:
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
      row_index: int,
      sheet_id: str,
      status_col_id: int,
      upload_status: str,
      error_message: str = "",
      message_col_id: int = None,
      resource_name: str = "",
      resource_col_id: int = None,
  ) -> None:
    """Update status and error message (if provided) in the sheet.

    Args:
      row_index: Index of sheet row.
      sheet_id: Sheet id.
      status_col_id: Row of status position.
      upload_status: Status of API operation.
      error_message: Optional string value with error message.
      message_col_id: Column of error messgae position.
      resource_name: Optional Google Ads resource name.
      resource_col_id: Column index of resource name.

    Raises:
      Exception: If unknown error occurs while updating rows.
    """
    update_request_list = []

    request = self.get_status_note(
        row_index + _SHEET_HEADER_SIZE, status_col_id, upload_status, sheet_id
    )
    update_request_list.append(request)

    if message_col_id:
      request = self.get_status_note(
          row_index + _SHEET_HEADER_SIZE,
          message_col_id,
          error_message,
          sheet_id,
      )
      update_request_list.append(request)

    if resource_col_id:
      request = self.get_status_note(
          row_index + _SHEET_HEADER_SIZE,
          message_col_id,
          error_message,
          sheet_id,
      )
      update_request_list.append(request)

    try:
      self.batch_update_requests(update_request_list)
    except errors.HttpError as e:
      logging.error("Unable to update Sheet rows: %s", str(e))
      raise e

  def bulk_update_sheet_status(
      self,
      sheet_name: str,
      status_col_id: int,
      message_col_id: int,
      asset_resource_col_id: int,
      results: Mapping[str, str | Mapping[str, str]],
  ) -> None:
    """Update status and error message in the sheet.

    Args:
      sheet_name: Name of the sheet.
      status_col_id: Column number of the status on the sheet.
      message_col_id: Column number of the error message on the sheet.
      asset_resource_col_id: Column number of the error message on the sheet.
      results: Array of containing status, error messages and asset resources.

    Raises:
      Exception: If unknown error occurs while updating rows.
    """
    update_request_list = []
    sheet_id = self.get_sheet_id(sheet_name)

    for row in results:
      row_to_update = row + _SHEET_HEADER_SIZE
      status = self.get_status_note(
          row_to_update, status_col_id, results[row]["status"], sheet_id
      )
      update_request_list.append(status)

      message = self.get_status_note(
          row_to_update, message_col_id, results[row]["message"], sheet_id
      )
      update_request_list.append(message)

      asset_resource = self.get_status_note(
          row_to_update,
          asset_resource_col_id,
          results[row]["asset_group_asset"],
          sheet_id,
      )
      update_request_list.append(asset_resource)

    try:
      if update_request_list:
        self.batch_update_requests(update_request_list)
    except errors.HttpError as e:
      logging.error("Unable to update Sheet rows: %s", str(e))
      raise e

  def get_sheet_id(self, sheet_name: str) -> str:
    """Get sheet id of provided sheet name.

    Args:
      sheet_name: Google Sheet name.

    Returns:
      sheet_id: Sheet id correlated to the sheet name.

    Raises:
      Exception: If error occurs while retrieving the Sheet ID.
    """
    sheet_id = None
    try:
      sheet_id = self.get_sheet_id_by_name(sheet_name)
    except errors.HttpError as e:
      logging.error("Error while retrieving the Sheet ID: %s", str(e))
    return sheet_id

  def add_new_asset_group_to_list_sheet(
      self, asset_group_sheetlist: Sequence[str]
  ) -> None:
    """Update error message in the sheet.

    Args:
        asset_group_sheetlist: Array containing the information of the new asset
          group.

    Raises:
        Exception: If unknown error occurs while updating rows in the Time
          Managed Sheet.
    """
    resource = {"majorDimension": "ROWS", "values": [asset_group_sheetlist]}
    sheet_range = (
        data_references.SheetNames.asset_groups
        + "!"
        + data_references.SheetRanges.asset_groups
    )

    try:
      self._sheets_service.values().append(
          spreadsheetId=self.spread_sheet_id,
          range=sheet_range,
          body=resource,
          valueInputOption="USER_ENTERED",
      ).execute()
    except errors.HttpError as e:
      logging.error("Couldn't update Assets Group to a sheet \n %s", str(e))
      raise e

  def add_new_campaign_to_list_sheet(
      self, campaign_sheetlist: Sequence[str]
  ) -> None:
    """Update error message in the sheet.

    Args:
        campaign_sheetlist: Array containing the information of the new asset
          group.

    Raises:
        Exception: If unknown error occurs while updating rows.
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
    except errors.HttpError as e:
      logging.error("Unable to update Sheet rows: %s ", str(e))
      raise e

  def update_asset_sheet_output(
      self,
      results: Sequence[Sequence[str | int]],
      account_map: Mapping[str, Mapping[str, str]],
  ) -> None:
    """Write exisitng assets to asset sheet.

    Args:
      results: Array of array containing the existing assets in Google Ads.
      account_map: Google Ads account map, account ids and names.
    """
    sheet_output = []

    asset_resource_column = "!L:L"
    sheet_range = data_references.SheetNames.assets + "!A:L"

    asset_group_asset_values = self.get_sheet_values(
        data_references.SheetNames.assets + asset_resource_column
    )

    index = 0
    for row in results:
      resource_name = row.asset_group_asset.resource_name

      if [resource_name] not in asset_group_asset_values:
        # Create empty list of lists with lenght of sheet row.
        sheet_output.append(
            [None] * (data_references.Assets.asset_group_asset + 1)
        )
        sheet_output = self.create_sheet_output_for_writing_into(
            row, resource_name, sheet_output, index
        )

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
      response = request.execute()
    except errors.HttpError as e:
      logging.error("Unable to update Sheet rows: %s ", str(e))
      raise e

    self.update_assets_columns(response, sheet_output, account_map)

  def create_sheet_output_for_writing_into(
      self,
      row: Sequence[str | int],
      resource_name: str,
      sheet_output: Sequence[Sequence[str | int]],
      index: int,
  ) -> Sequence[Sequence[str, int]]:
    """Create output array for writing into spreadsheet.

    Args:
      row: Array containing the asset infortmation for writing into spreadsheet.
      resource_name: Asset resource name.
      sheet_output: Output array for spreadsheet write.
      index: Index of the row where data should be populated.

    Returns:
      Array of arrays representing an index and row data.
    """
    asset_type = row.asset_group_asset.field_type.name

    sheet_output[index][
        data_references.Assets.asset_group_name
    ] = row.asset_group.name
    sheet_output[index][data_references.Assets.asset_thumbnail] = ""
    sheet_output[index][data_references.Assets.type] = asset_type

    sheet_output[index][data_references.Assets.status] = "UPLOADED"
    sheet_output[index][data_references.Assets.delete_asset] = ""
    sheet_output[index][
        data_references.Assets.customer_name
    ] = row.customer.descriptive_name
    sheet_output[index][
        data_references.Assets.campaign_name
    ] = row.campaign.name

    sheet_output[index][data_references.Assets.error_message] = ""
    sheet_output[index][
        data_references.Assets.asset_group_asset
    ] = resource_name

    if asset_type in [
        data_references.AssetTypes.headline,
        data_references.AssetTypes.description,
        data_references.AssetTypes.long_headline,
        data_references.AssetTypes.business_name,
    ]:
      sheet_output[index][
          data_references.Assets.asset_text
      ] = row.asset.text_asset.text
      sheet_output[index][data_references.Assets.asset_call_to_action] = ""
      sheet_output[index][data_references.Assets.asset_url] = ""

    if asset_type in [
        data_references.AssetTypes.marketing_image,
        data_references.AssetTypes.square_image,
        data_references.AssetTypes.portrait_marketing_image,
        data_references.AssetTypes.square_logo,
        data_references.AssetTypes.landscape_logo,
    ]:
      sheet_output[index][data_references.Assets.asset_text] = row.asset.name
      sheet_output[index][data_references.Assets.asset_call_to_action] = ""
      sheet_output[index][
          data_references.Assets.asset_url
      ] = row.asset.image_asset.full_size.url

    if asset_type == data_references.AssetTypes.call_to_action:
      sheet_output[index][data_references.Assets.asset_text] = row.asset.name
      sheet_output[index][data_references.Assets.asset_call_to_action] = (
          self.google_ads_client.enums.CallToActionTypeEnum(
              row.asset.call_to_action_asset.call_to_action
          ).name
      )
      sheet_output[index][data_references.Assets.asset_url] = ""

    if asset_type == data_references.AssetTypes.youtube_video:
      sheet_output[index][data_references.Assets.asset_text] = row.asset.name
      sheet_output[index][data_references.Assets.asset_call_to_action] = ""
      sheet_output[index][data_references.Assets.asset_url] = (
          "https://www.youtube.com/watch?v="
          + row.asset.youtube_video_asset.youtube_video_id
      )
    return sheet_output

  def update_sitelink_sheet_output(
      self,
      results: Sequence[Sequence[str | int]],
      account_map: Mapping[str, Mapping[str, str]],
  ) -> None:
    """Write exisitng assets to asset sheet.

    Args:
      results: Array of array containing the existing assets in Google Ads.
      account_map: Google Ads account map, account ids and names.
    """
    sheet_output = []
    sheet_range = (
        data_references.SheetNames.sitelinks
        + "!"
        + data_references.SheetRanges.sitelinks
    )

    asset_group_asset_values = self.get_sheet_values(
        data_references.SheetNames.sitelinks + "!J:J"
    )

    index = 0
    for row in results:
      resource_name = row.campaign_asset.resource_name

      if [resource_name] not in asset_group_asset_values:
        # Create empty list of lists with lenght of sheet row.
        sheet_output.append(
            [None] * (data_references.Sitelinks.sitelink_resource + 1)
        )

        sheet_output[index][
            data_references.Sitelinks.upload_status
        ] = "UPLOADED"
        sheet_output[index][data_references.Sitelinks.delete_sitelink] = ""
        sheet_output[index][
            data_references.Sitelinks.customer_name
        ] = row.customer.descriptive_name
        sheet_output[index][
            data_references.Sitelinks.campaign_name
        ] = row.campaign.name

        sheet_output[index][data_references.Sitelinks.error_message] = ""
        sheet_output[index][
            data_references.Sitelinks.sitelink_resource
        ] = resource_name

        sheet_output[index][data_references.Sitelinks.final_urls] = (
            row.asset.final_urls[0]
        )
        sheet_output[index][
            data_references.Sitelinks.link_text
        ] = row.asset.sitelink_asset.link_text
        sheet_output[index][
            data_references.Sitelinks.description1
        ] = row.asset.sitelink_asset.description1
        sheet_output[index][
            data_references.Sitelinks.description2
        ] = row.asset.sitelink_asset.description2
        sheet_output[index][
            data_references.Sitelinks.sitelink_resource
        ] = row.campaign_asset.resource_name

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
      response = request.execute()
    except errors.HttpError as e:
      logging.error("Unable to update Sheet rows: %s ", str(e))
      raise e

    self.update_sitelinks_columns(
        response,
        sheet_output,
        account_map,
    )

  def update_assets_columns(
      self,
      response: ads_api.ApiResponse,
      sheet_output: Sequence[Sequence[str]],
      account_map: Mapping[str, Mapping[str, str]],
  ) -> None:
    """Update custom columns in Assets Sheet.

    Args:
      response: API response object for Asset Sheet update.
      sheet_output: Input sheet object with the relevant new sheet values.
      account_map: Google Ads account map, account ids and names.
    """
    if response["tableRange"]:
      sheet_id = self.get_sheet_id(data_references.SheetNames.assets)
      start_row = int(re.search("([0-9]*$)", response["tableRange"]).group())
      update_request_list = []
      i = 0
      if "updatedRows" in response["updates"]:
        customer_list = list(account_map.keys())
        while i < response["updates"]["updatedRows"]:
          update_request_list.append(
              self.get_checkbox(
                  start_row + i, data_references.Assets.delete_asset, sheet_id
              )
          )
          update_request_list.append(
              self.get_thumbnail(
                  start_row + i,
                  data_references.Assets.asset_thumbnail,
                  sheet_id,
              )
          )
          update_request_list.append(
              self.get_dropdown(
                  start_row + i,
                  data_references.Assets.customer_name,
                  customer_list,
                  sheet_id,
              )
          )
          if sheet_output[i][data_references.Assets.customer_name]:
            campaign_list = list(
                account_map[
                    sheet_output[i][data_references.Assets.customer_name]
                ].keys()
            )
            update_request_list.append(
                self.get_dropdown(
                    start_row + i,
                    data_references.Assets.campaign_name,
                    campaign_list,
                    sheet_id,
                )
            )

          if account_map[sheet_output[i][data_references.Assets.customer_name]][
              sheet_output[i][data_references.Assets.campaign_name]
          ]:
            asset_group_list = account_map[
                sheet_output[i][data_references.Assets.customer_name]
            ][sheet_output[i][data_references.Assets.campaign_name]]
            update_request_list.append(
                self.get_dropdown(
                    start_row + i,
                    data_references.Assets.asset_group_name,
                    asset_group_list,
                    sheet_id,
                )
            )

          i += 1

        sort = self.get_sort_request(_SHEET_HEADER_SIZE, 0, sheet_id, 0, 3)
        update_request_list.append(sort)

        try:
          self.batch_update_requests(update_request_list)
        except errors.HttpError as e:
          logging.error("Unable to update Sheet rows: %s ", str(e))
          raise e

  def update_sitelinks_columns(
      self,
      response: ads_api.ApiResponse,
      sheet_output: Sequence[Sequence[str]],
      account_map: Mapping[str, Mapping[str, str]],
  ) -> None:
    """Update custom columns in Assets Sheet.

    Args:
      response: API response object for Asset Sheet update.
      sheet_output: Input sheet object with the relevant new sheet values.
      account_map: Google Ads account map, account ids and names.
    """
    if response.get("tableRange"):
      sheet_id = self.get_sheet_id(data_references.SheetNames.sitelinks)
      start_row = int(re.search("([0-9]*$)", response["tableRange"]).group())
      update_request_list = []
      i = 0
      if "updatedRows" in response["updates"]:
        customer_list = list(account_map.keys())
        while i < response["updates"]["updatedRows"]:
          update_request_list.append(
              self.get_checkbox(
                  start_row + i,
                  data_references.Sitelinks.delete_sitelink,
                  sheet_id,
              )
          )
          update_request_list.append(
              self.get_dropdown(
                  start_row + i,
                  data_references.Sitelinks.customer_name,
                  customer_list,
                  sheet_id,
              )
          )
          if sheet_output[i][data_references.Sitelinks.customer_name]:
            campaign_list = list(
                account_map[
                    sheet_output[i][data_references.Sitelinks.customer_name]
                ].keys()
            )
            update_request_list.append(
                self.get_dropdown(
                    start_row + i,
                    data_references.Sitelinks.campaign_name,
                    campaign_list,
                    sheet_id,
                )
            )

          i += 1

        sort = self.get_sort_request(_SHEET_HEADER_SIZE, 0, sheet_id, 0, 3)
        update_request_list.append(sort)

        try:
          self.batch_update_requests(update_request_list)
        except errors.HttpError as e:
          logging.error("Unable to update Sheet rows: %s ", str(e))
          raise e

  def refresh_spreadsheet(self) -> None:
    """Update spreadsheet with exisitng assets, asset groups and campaigns."""
    account_map = {}
    results = self.google_ads_service.retrieve_all_customers(
        self.login_customer_id, self.customer_id_inclusion_list
    )
    account_map = self.update_sheet_lists(
        results, data_references.SheetNames.customers, "!B:B", account_map
    )

    for row in results:
      customer_id = str(row.customer_client.id)

      if customer_id:
        results = self.google_ads_service.retrieve_all_campaigns(customer_id)
        if results:
          account_map = self.update_sheet_lists(
              results, data_references.SheetNames.campaigns, "!D:D", account_map
          )
        results = self.google_ads_service.retrieve_all_asset_groups(customer_id)
        if results:
          account_map = self.update_sheet_lists(
              results,
              data_references.SheetNames.asset_groups,
              "!F:F",
              account_map,
          )

        results = self.google_ads_service.retrieve_all_assets(customer_id)
        if results:
          self.update_asset_sheet_output(results, account_map)

        results = self.google_ads_service.retrieve_sitelinks(customer_id)
        if results:
          self.update_sitelink_sheet_output(results, account_map)

    self._set_cell_value(
        "=SORT(UNIQUE({CustomerList!$A$5:$A}))", "DropDownConfig!N3"
    )

  def refresh_campaign_list(
      self,
  ) -> MutableMapping[str, MutableMapping[str, Sequence[str]]]:
    """Update spreadsheet with Campaign list."""
    account_map = {}
    results = self.google_ads_service.retrieve_all_customers(
        self.login_customer_id, self.customer_id_inclusion_list
    )
    account_map = self.update_sheet_lists(
        results, data_references.SheetNames.customers, "!B:B", account_map
    )

    for row in results:
      customer_id = str(row.customer_client.id)

      if customer_id:
        results = self.google_ads_service.retrieve_all_campaigns(customer_id)
        account_map = self.update_sheet_lists(
            results, data_references.SheetNames.campaigns, "!D:D", account_map
        )

    return account_map

  def refresh_asset_group_list(self) -> None:
    """Update spreadsheet with Asset Group list."""
    results = self.google_ads_service.retrieve_all_customers(
        self.login_customer_id, self.customer_id_inclusion_list
    )
    account_map = self.refresh_campaign_list()

    for row in results:
      customer_id = str(row.customer_client.id)

      if customer_id:
        results = self.google_ads_service.retrieve_all_asset_groups(customer_id)
        self.update_sheet_lists(
            results,
            data_references.SheetNames.asset_groups,
            "!F:F",
            account_map,
        )

  def refresh_assets_list(self) -> None:
    """Update spreadsheet with Assets list."""
    account_map = {}
    results = self.google_ads_service.retrieve_all_customers(
        self.login_customer_id, self.customer_id_inclusion_list
    )
    account_map = self.update_sheet_lists(
        results, data_references.SheetNames.customers, "!B:B", account_map
    )

    for row in results:
      customer_id = str(row.customer_client.id)

      if customer_id:
        results = self.google_ads_service.retrieve_all_assets(customer_id)
        self.update_asset_sheet_output(results, account_map)

  def refresh_sitelinks_list(self) -> None:
    """Update spreadsheet with Sitelinks list."""
    account_map = {}
    results = self.google_ads_service.retrieve_all_customers(
        self.login_customer_id, self.customer_id_inclusion_list
    )
    account_map = self.update_sheet_lists(
        results, data_references.SheetNames.customers, "!B:B", account_map
    )

    for row in results:
      customer_id = str(row.customer_client.id)

      if customer_id:
        results = self.google_ads_service.retrieve_sitelinks(customer_id)
        self.update_sitelink_sheet_output(results, account_map)

  def refresh_customer_id_list(self) -> None:
    """Update spreadsheet with customer id list."""
    results = self.google_ads_service.retrieve_all_customers(
        self.login_customer_id, self.customer_id_inclusion_list
    )
    self.update_sheet_lists(
        results, data_references.SheetNames.customers, "!B:B", {}
    )

    self._set_cell_value(
        "=SORT(UNIQUE({CustomerList!$A$5:$A}))", "DropDownConfig!N3"
    )

  def update_sheet_lists(
      self,
      results: Sequence[Sequence[int | str]],
      sheet_name: str,
      column: str,
      account_map: Mapping[str, Mapping[str, str]],
  ) -> Mapping[str, Mapping[str, str]]:
    """Write exisitng customer list, campaigns, asset groups, assets and sitelinks to spreadsheet.

    Args:
      results: Array of array containing the existing asset groups in Google
        Ads.
      sheet_name: Name of the sheet to write the results to.
      column: String value representation of sheet column, with unique id.
      account_map: Google Ads account map, account ids and names.
    """
    existing_values = self.get_sheet_values(sheet_name + column)
    sheet_range = ""
    sheet_output = []
    index = 0
    for row in results:
      if sheet_name == data_references.SheetNames.customers:
        if row.customer_client.descriptive_name not in account_map:
          account_map[row.customer_client.descriptive_name] = {}
        row_item_id = str(row.customer_client.id)
        sheet_range = sheet_name + "!A:B"
      elif sheet_name == data_references.SheetNames.campaigns:
        if row.campaign.name not in account_map[row.customer.descriptive_name]:
          account_map[row.customer.descriptive_name][row.campaign.name] = []
        row_item_id = str(row.campaign.id)
        sheet_range = sheet_name + "!A:D"
      elif sheet_name == data_references.SheetNames.asset_groups:
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
      if sheet_output:
        request = self._sheets_service.values().append(
            spreadsheetId=self.spread_sheet_id,
            range=sheet_range,
            valueInputOption=value_input_option,
            insertDataOption=insert_data_option,
            body=value_range_body,
        )
        request.execute()
    except errors.HttpError as e:
      logging.error("Unable to update Sheet rows: %s ", str(e))
      raise e

    return account_map

  def generate_list_sheet_output(
      self, row: Sequence[int | str], sheet_name: str
  ) -> Sequence[str]:
    """Compile list of sheet output for Google Ads resources.

    Args:
      row: API result row from search query.
      sheet_name: Name of the sheet for which data is processed.

    Returns:
      Array of sheet values.
    """
    output = []
    if sheet_name == data_references.SheetNames.customers:
      output = [None] * (data_references.CustomerList.customer_id + 1)
      output[data_references.CustomerList.customer_name] = (
          row.customer_client.descriptive_name
      )
      output[data_references.CustomerList.customer_id] = row.customer_client.id
    if sheet_name == data_references.SheetNames.campaigns:
      output = [None] * (data_references.CampaignList.campaign_id + 1)
      output[data_references.CampaignList.campaign_name] = row.campaign.name
      output[data_references.CampaignList.campaign_id] = row.campaign.id
      output[data_references.CampaignList.customer_name] = (
          row.customer.descriptive_name
      )
      output[data_references.CustomerList.customer_id] = row.customer.id
    if sheet_name == data_references.SheetNames.asset_groups:
      output = [None] * (data_references.AssetGroupList.asset_group_id + 1)
      output[data_references.AssetGroupList.asset_group_name] = (
          row.asset_group.name
      )
      output[data_references.AssetGroupList.asset_group_id] = row.asset_group.id
      output[data_references.AssetGroupList.campaign_name] = row.campaign.name
      output[data_references.AssetGroupList.camapign_id] = row.campaign.id
      output[data_references.AssetGroupList.customer_name] = (
          row.customer.descriptive_name
      )
      output[data_references.AssetGroupList.customer_id] = row.customer.id

    return output
