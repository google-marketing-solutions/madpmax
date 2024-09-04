# Copyright 2024 Google LLC
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
"""Provides functionality to delete Asset Group Assets in Google Ads."""

from collections.abc import Mapping, Sequence
from typing import TypeAlias
from absl import logging
import ads_api
import data_references
from google.ads.googleads import client
from sheet_api import SheetsService
import utils

ApiResponse: TypeAlias = Mapping[str, bool | Mapping[str, str]]
AssetGroupAssetOperation: TypeAlias = Mapping[str, str]


class AssetDeletionService:
  """Class for Asset deletion.

  Contains all methods to delete assets in Google Ads pMax Asset Groups.
  """

  def __init__(
      self,
      google_ads_client: client.GoogleAdsClient,
      google_ads_service: ads_api.AdService,
      sheet_service: SheetsService,
  ) -> None:
    """Constructs the AssetDeletionService instance.

    Args:
      google_ads_client: Google Ads API client, dependency injection.
      google_ads_service: Ads Service Class dependency injection.
      sheet_service: Google Sheets API method class.
    """
    self._google_ads_client = google_ads_client
    self._google_ads_service = google_ads_service
    self.sheet_service = sheet_service

  def delete_asset(
      self, asset_resource: str
  ) -> AssetGroupAssetOperation:
    """Set up mutate object for deleting an asset.

    Args:
      asset_resource: Resource name of the Asset Groups Asset to be deleted.

    Returns:
      asset group asset delete operation
    """
    mutate_operation = None

    if asset_resource:
      mutate_operation = self._google_ads_client.get_type("MutateOperation")
      mutate_operation.asset_group_asset_operation.remove = asset_resource

    return mutate_operation

  def process_asset_deletion_input(
      self,
      asset_data: Sequence[str | int]
  ) -> tuple[Mapping[str, list[AssetGroupAssetOperation]], Mapping[
      str, list[int]]]:
    """Process data from the sheet to delete assets.

    Args:
      asset_data: Array of Asset data from the sheeet.

    Returns:
      The API mutate operations, organized by Customer Id, and the Sheet Rows
      these API mutrations are referring to.

      (
          {"customerid": [AssetGroupAssetOperation]},
          {"customerid": [0]}
      )
    """
    operations = {}
    row_to_operations_mapping = {}
    customer_mapping = {}

    for sheet_row_index, asset in enumerate(asset_data):
      if (
          asset[data_references.Assets.status]
          == data_references.RowStatus.uploaded and
          asset[data_references.Assets.delete_asset] == "TRUE"
      ):
        customer_name = asset[data_references.Assets.customer_name]
        if customer_name not in customer_mapping:
          customer_mapping[customer_name] = utils.retrieve_customer_id(
              customer_name, self.sheet_service)
        customer_id = customer_mapping[customer_name]

        asset_operation = None
        if data_references.Assets.asset_group_asset < len(asset) and asset[
            data_references.Assets.asset_group_asset]:
          asset_operation = self.delete_asset(
              asset[data_references.Assets.asset_group_asset]
          )

        if asset_operation:
          if (
              customer_id not in operations.keys()
              or not operations[customer_id]
          ):
            operations[customer_id] = []
          operations[customer_id].append(asset_operation)

          # map the index of the row to the resource that is process for
          # allocating errors from the API call later
          if (
              customer_id not in row_to_operations_mapping.keys()
              or not row_to_operations_mapping[customer_id]
          ):
            row_to_operations_mapping[customer_id] = []
          row_to_operations_mapping[
              customer_id].append(sheet_row_index)

    return operations, row_to_operations_mapping

  def process_api_deletion_operations(
      self,
      operations: Mapping[str, Mapping[str, str]],
      row_to_operations_mapping: Mapping[str, str],
  ) -> None:
    """Uploading asset results to the sheet.

    Args:
      operations: List of operations from asset deletion.
      row_to_operations_mapping: Mapping of the resourse name and related row
          for uploading to the sheet.

    Returns:
      A tuple containing a list with all row numbers of successfully processed
      API requests, and a Mapping between the row in the sheet and error
      message from the response for the rows that failed.
    """
    error_rows = []
    all_rows = []
    error_sheet_output = {}

    for customer_id in operations:
      all_rows.extend(row_to_operations_mapping[customer_id])
      response, error_message = self._google_ads_service.bulk_mutate(
          operations[customer_id], customer_id, True
      )
      if error_message:
        raise ValueError(f"Couldn't update Assets \n {error_message}")
      if response:
        customer_sheet_output = self.process_asset_errors(
            response, row_to_operations_mapping[customer_id],
            operations[customer_id])
        error_sheet_output.update(customer_sheet_output)
        error_rows.extend(list(customer_sheet_output.keys()))

    rows_for_removal = list(set(all_rows) - set(error_rows))
    rows_for_removal.sort(reverse=True)

    return rows_for_removal, error_sheet_output

  def process_asset_errors(
      self,
      response: ApiResponse,
      row_to_operations_mapping: list[int],
      operations: list[Mapping[str, Mapping[str, str]]],
  ) -> Mapping[str, Mapping[str, str]]:
    """Captures partial failure errors and success messages from a response.

    Args:
      response:  A ApiResponse message instance.
      row_to_operations_mapping: Mapping of the resourse name and related row
          for uploading to the sheet.
      operations: List of operations from asset deletion.

    Returns:
      Mapping between the row in the sheet and status and error message from the
      response.
    """
    error_obj = {}
    # Check for existence of any partial failures in the response.
    if self._google_ads_service.is_partial_failure_error_present(response):
      partial_failure = getattr(response, "partial_failure_error", None)
      # partial_failure_error.details is a repeated field and iterable
      error_details = getattr(partial_failure, "details", [])

      for error_detail in error_details:
        # Retrieve an instance of the GoogleAdsFailure class from the client
        failure_message = self._google_ads_client.get_type("GoogleAdsFailure")
        # Parse the string into a google_ads_failure message instance.
        # To access class-only methods on the message we retrieve its type.
        google_ads_failure = type(failure_message)
        failure_object = google_ads_failure.deserialize(error_detail.value)
        for error in failure_object.errors:
          # Construct a list that details which element in
          # the above ad_group_operations list failed (by index number)
          # as well as the error message and error code.
          row_number = row_to_operations_mapping[
              error.location.field_path_elements[0].index]

          # In case it is the first error for the row create the error object.
          if row_number not in error_obj:
            resource_name = operations[
                error.location.field_path_elements[
                    0].index].asset_group_asset_operation.remove
            error_obj[row_number] = {
                "status": data_references.RowStatus.uploaded,
                "message": (f"Error message: {error.message}\n"
                            f"\tError code: {str(error.error_code).strip()}"),
                "asset_group_asset": resource_name
            }
          # In case of multiple errors for one row, append the error message to
          # the object.
          else:
            error_obj[row_number]["message"] = (
                error_obj[row_number]["message"] + "\n"
                f"Error message: {error.message}\n"
                f"\tError code: {str(error.error_code).strip()}")
    else:
      logging.info(
          "All operations completed successfully. No partial failure to show."
      )
    return error_obj
