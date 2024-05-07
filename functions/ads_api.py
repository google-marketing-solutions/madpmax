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
"""Provides functionality to interact with Google Ads platform."""

from collections.abc import Mapping, Sequence
import re
from typing import TypeAlias
from absl import logging
import data_references
from google.ads.googleads import client
from google.ads.googleads import errors

BudgetOperation: TypeAlias = Mapping[str, str | int]
CampaignOperation: TypeAlias = Mapping[str, str | bool | Mapping[str, int]]
SitelinkOperation: TypeAlias = Mapping[str, str | Sequence | Mapping[str, str]]
LinkSitelinkOperation: TypeAlias = Mapping[str, str]
ApiResponse: TypeAlias = Mapping[str, bool | Mapping[str, str]]
AssetOperation: TypeAlias = Mapping[str, str]
AssetToAssetGroupOperation: TypeAlias = Mapping[
    str, str | Mapping[str, str | int]
]
AssetGroupOperation = Mapping[str, str]


class AdService:
  """Provides Google ads API service to interact with Ads platform."""

  def __init__(self, google_ads_client: client.GoogleAdsClient):
    """Constructs the AdService instance.

    Args:
      google_ads_client: Google Ads API client, dependency injection.
    """
    self._google_ads_client = google_ads_client
    self._cache_ad_group_ad = {}
    self.prev_image_asset_list = None
    self.prev_customer_id = None

  def _get_campaign_resource_name(
      self, customer_id: str, campaign_id: str
  ) -> str:
    """Gets a campaign by customer id and campaign id.

    Args:
      customer_id: Customer id.
      campaign_id: Id of the campaign

    Returns:
      Campaign resource name.
    """
    campaign_service = self._google_ads_client.get_service("CampaignService")

    return campaign_service.campaign_path(customer_id, campaign_id)

  def _get_asset_group_resource_name(
      self, customer_id: str, asset_group_id: str
  ) -> str:
    """Generates the Ad group resource name based on input.

    Args:
      customer_id: Customer id.
      asset_group_id: Id of the ad group

    Returns:
      Asset group resource name.
    """
    asset_group_service = self._google_ads_client.get_service(
        "AssetGroupService"
    )

    return asset_group_service.asset_group_path(customer_id, asset_group_id)

  def _retrieve_yt_id(self, video_url: str) -> str | None:
    """Retrieves the YouTube video id from the URL.

    Args:
      video_url:  Full url of the video on YT.

    Returns:
      String value containing the id, or None.
    """
    regex = r"^.*(youtu\.be\/|v\/|u\/\w\/|embed\/|shorts\/|watch\?v=|\&v=)([^#\&\?]*).*"
    result = re.search(regex, video_url)
    if result:
      return result.group(2)

    return None

  def bulk_mutate(
      self,
      mutate_operations: Sequence[
          AssetToAssetGroupOperation
          | AssetGroupOperation
          | AssetOperation
          | BudgetOperation
          | CampaignOperation
      ],
      customer_id: str,
      partial_failure: bool = False,
  ) -> tuple[ApiResponse, str]:
    """Process Bulk Mutate operation via Google Ads API.

    Args:
      mutate_operations: Array of mutate operations.
      customer_id: Customer id.
      partial_failure: If we should accept partial failure from API.

    Returns:
      Response API object and error message.
    """
    response = None
    error_message = None

    googleads_service = self._google_ads_client.get_service("GoogleAdsService")
    request = self._google_ads_client.get_type("MutateGoogleAdsRequest")
    request.customer_id = customer_id
    request.mutate_operations = mutate_operations
    request.partial_failure = partial_failure

    try:
      response = googleads_service.mutate(request=request)
    except errors.GoogleAdsException as ex:
      error_message = (
          f'Request with ID "{ex.request_id}" failed and includes the'
          " following errors:"
      )
      for error in ex.failure.errors:
        if error.message != "Resource was not found.":
          error_message = (
              error_message + f'\n\tError message: "{error.message}".'
          )

      logging.error(error_message)

    return response, error_message

  def is_partial_failure_error_present(self, response: ApiResponse) -> bool:
    """Checks whether a response message has a partial failure error.

    In Python the partial_failure_error attr is always present on a response
    message and is represented by a google.rpc.Status message. So we can't
    simply check whether the field is present, we must check that the code is
    non-zero. Error codes are represented by the google.rpc.Code proto Enum:
    https://github.com/googleapis/googleapis/blob/master/google/rpc/code.proto

    Args:
      response: A MutateAdGroupsResponse message instance.

    Returns:
      A boolean, whether or not the response message has a partial
      failure error.
    """
    partial_failure = getattr(response, "partial_failure_error", None)
    code = getattr(partial_failure, "code", None)
    return code != 0

  def process_asset_results(
      self,
      response: ApiResponse,
      operations: Sequence[
          AssetToAssetGroupOperation
          | AssetGroupOperation
          | AssetOperation
          | BudgetOperation
          | CampaignOperation
      ],
      row_mapping: Mapping[int, str],
      mutate_type: str,
  ) -> Mapping[str, Mapping[str, str]]:
    """Prints partial failure errors and success messages from a response.

    Args:
      response:  A MutateAdGroupsResponse message instance.
      operations: API operations object of lists.
      row_mapping: Object with the mapping between rows and status messages.
      mutate_type: Type of API mutation  "ASSETS" "ASSET_GROUPS" or "SITELINKS"

    Returns:
      Mapping between the row in the sheet and status and error message from the
      response.
    """
    error_obj = {}

    # Check for existence of any partial failures in the response.
    if self.is_partial_failure_error_present(response):
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
          error_obj[error.location.field_path_elements[0].index] = [
              (
                  "A partial failure creating a(n)"
                  f" {error.location.field_path_elements[1].field_name[:-10]} at"
                  " index"
                  f" {error.location.field_path_elements[0].index} occurred"
              ),
              f"Error message: {error.message}\n",
              f"Error code: {str(error.error_code).strip()}\n",
              f"Error trigger: {error.trigger.string_value}",
          ]
    else:
      logging.info(
          "All operations completed successfully. No partial failure to show."
      )

    return self._map_results_and_errors_from_the_response_to_row_number(
        response, error_obj, operations, row_mapping, mutate_type
    )

  def _map_results_and_errors_from_the_response_to_row_number(
      self,
      response: ApiResponse,
      error_obj: Mapping[int, Sequence[str]],
      operations: Sequence[
          AssetToAssetGroupOperation
          | AssetGroupOperation
          | AssetOperation
          | BudgetOperation
          | CampaignOperation
      ],
      row_mapping: Mapping[int, str],
      mutate_type: str,
  ) -> Mapping[str, Mapping[str, str]]:
    """Prints results and errors from a response.

    Args:
      response:  A MutateAdGroupsResponse message instance.
      error_obj: Mapping of row index of operations and related errors.
      operations: API operations object of lists.
      row_mapping: Object with the mapping between rows and status messages.
      mutate_type: Type of API mutation  "ASSETS" "ASSET_GROUPS" or "SITELINKS"

    Returns:
      Mapping between the row in the sheet and status and error message from the
      response.
    """
    # In the list of results, operations from the ad_group_operation list
    # that failed will be represented as empty messages. This loop detects
    # such empty messages and ignores them, while printing information about
    # successful operations.
    results = {}
    suffix = "_result"
    i = 0
    row_status_key = "status"
    row_message_key = "message"
    row_asset_group_asset_key = "asset_group_asset"

    for result in response.mutate_operation_responses:
      for field_descriptor, value in result._pb.ListFields():
        if field_descriptor.name.endswith(suffix):
          name = field_descriptor.name[: -len(suffix)]
        else:
          name = field_descriptor.name

        # Check if the index also appears in the list of errors from the
        # Bulk Mutate response.
        if i in error_obj:
          results.update(
              self._map_error_object_to_corresponding_row(
                  operations, mutate_type, row_mapping, i, error_obj
              )
          )
        else:
          logging.info("Created a(n) %s with %s.", {name}, {str(value).strip()})

          operations_create = operations[
              i
          ].asset_group_asset_operation.create.asset
          if mutate_type == "SITELINKS":
            operations_create = operations[
                i
            ].campaign_asset_operation.create.asset

          if operations_create and operations_create in row_mapping:
            sheet_row = row_mapping[operations_create]

            if sheet_row not in results:
              results[sheet_row] = {}
            results[sheet_row][
                row_status_key
            ] = data_references.RowStatus.uploaded
            results[sheet_row][row_message_key] = ""
            results[sheet_row][row_asset_group_asset_key] = value.resource_name
        i += 1

    return results

  def _map_error_object_to_corresponding_row(
      self,
      operations: Sequence[
          AssetToAssetGroupOperation
          | AssetGroupOperation
          | AssetOperation
          | BudgetOperation
          | CampaignOperation
      ],
      mutate_type: str,
      row_mapping: Mapping[int, str],
      index: int,
      error_obj: Mapping[int, Sequence[str]],
  ) -> Mapping[str, Mapping[str, str]]:
    """Map errors from a response error object to the corresponding row in the sheet.

    Args:
      operations: List of API operations objects.
      mutate_type: Type of API mutation  "ASSETS" "ASSET_GROUPS" or "SITELINKS"
      row_mapping: Object with the mapping between rows and status messages.
      index: Index tracing sheet row.
      error_obj: Mapping of row index of operations and related errors.

    Returns:
      Mapping between the row in the sheet and status and error message from the
      response.
    """
    row_status_key = "status"
    row_message_key = "message"
    row_asset_group_asset_key = "asset_group_asset"
    results = {}
    sheet_row = None
    error_asset_resource = self._extract_asset_group_resource_from_operations(
        operations, mutate_type, index
    )
    for op in operations:
      if (
          hasattr(op, "asset_operation")
          and op.asset_operation.create.resource_name == error_asset_resource
      ):
        sheet_row = row_mapping[op.asset_operation.create.resource_name]
        self._log_operational_errors(op)
        break

    if not sheet_row:
      raise ValueError(
          "Couldn't find correlated asset to the error from the API"
      )

    if sheet_row not in results:
      results[sheet_row] = {}

    results[sheet_row][row_status_key] = data_references.RowStatus.error

    if row_message_key in results[sheet_row]:
      asset_message = results[sheet_row][row_message_key]
    else:
      asset_message = ""

    results[sheet_row][row_message_key] = (
        error_obj[index][1] + error_obj[index][2] + error_obj[index][3]
    )
    results[sheet_row][row_message_key] = (
        asset_message + results[sheet_row][row_message_key]
    )
    results[sheet_row][row_asset_group_asset_key] = ""

    return results

  def _extract_asset_group_resource_from_operations(
      self,
      operations: Sequence[
          AssetToAssetGroupOperation
          | AssetGroupOperation
          | AssetOperation
          | BudgetOperation
          | CampaignOperation
      ],
      mutate_type: str,
      index: int,
  ) -> str:
    """Retrieve resource name in the Google Sheet corresponding to error message.

    Args:
      operations: API operations object of lists.
      mutate_type: Type of API mutation  "ASSETS" "ASSET_GROUPS" or "SITELINKS"
      index: Index tracing sheet row.

    Returns:
      Asset resource name.
    """
    if not operations[index].asset_group_asset_operation.create.asset:
      index += 1

    error_asset_resource = operations[
        index
    ].asset_group_asset_operation.create.asset
    if mutate_type == data_references.SheetNames.sitelinks:
      error_asset_resource = operations[
          index
      ].campaign_asset_operation.create.asset

    return error_asset_resource

  def _log_operational_errors(
      self,
      operation: (
          AssetToAssetGroupOperation
          | AssetGroupOperation
          | AssetOperation
          | BudgetOperation
          | CampaignOperation
      ),
  ) -> None:
    """Logs information about which type of aseets has been created.

    Args:
      operation: API operation object.
    """
    if operation.asset_operation.create.text_asset:
      logging.info(
          "\tText: %s", operation.asset_operation.create.text_asset.text
      )
    if operation.asset_operation.create.image_asset.full_size.url:
      logging.info("\tImage Name: %s", operation.asset_operation.create.name)
      logging.info(
          "\tImage URL: %s \n",
          operation.asset_operation.create.image_asset.full_size.url,
      )

  def create_multiple_text_assets(
      self,
      operations: Sequence[
          AssetToAssetGroupOperation
          | AssetGroupOperation
          | AssetOperation
          | BudgetOperation
          | CampaignOperation
      ],
      customer_id: str,
  ) -> Sequence[str]:
    """Creates multiple text assets in a single request and returns the list of resource names.

    Args:
      operations: A list of api operations, each of which will be used to create
        a text asset.
      customer_id: Google Ads customer id.

    Returns:
      asset_resource_names: a list of asset resource names.
    """
    asset_resource_names = []

    googleads_service = self._google_ads_client.get_service("GoogleAdsService")
    request = self._google_ads_client.get_type("MutateGoogleAdsRequest")
    request.customer_id = customer_id
    request.mutate_operations = operations
    request.partial_failure = True

    try:
      response = googleads_service.mutate(request=request)
    except errors.GoogleAdsException as ex:
      error_message = (
          f'Request with ID "{ex.request_id}" failed and includes the'
          " following errors:"
      )
      for error in ex.failure.errors:
        if error.message != "Resource was not found.":
          error_message = (
              error_message + f'\n\tError message: "{error.message}".'
          )
      logging.error(error_message)
      raise ex

    if response:
      for result in response.mutate_operation_responses:
        if result._pb.HasField("asset_result"):
          asset_resource_names.append(result.asset_result.resource_name)
      self.print_response_details(response)

    return asset_resource_names

  def print_response_details(self, response: ApiResponse) -> None:
    """Prints the details of a MutateGoogleAdsResponse.

    Parses the "response" oneof field name and uses it to extract the new
    entity's name and resource name.

    Args:
        response: A MutateGoogleAdsResponse object.
    """
    suffix = "_result"
    for result in response.mutate_operation_responses:
      for field_descriptor, value in result._pb.ListFields():
        if field_descriptor.name.endswith(suffix):
          name = field_descriptor.name[: -len(suffix)]
        else:
          name = field_descriptor.name
        logging.info("Created a(n) %s with %s.", {name}, {str(value).strip()})

  def retrieve_all_assets(self, customer_id: str) -> ApiResponse:
    """Retrieve all active pMax assets from Google Ads.

    Args:
      customer_id: Google ads customer id.

    Returns:
      Results object with Google Ads api search results.
    """
    query = """SELECT
                  customer.id,
                  customer.descriptive_name,
                  campaign.id,
                  campaign.name,
                  campaign.resource_name,
                  asset_group.id,
                  asset_group.name,
                  asset_group.resource_name,
                  asset_group_asset.resource_name,
                  asset_group_asset.field_type,
                  asset.id,
                  asset.name,
                  asset.resource_name,
                  asset.text_asset.text,
                  asset.youtube_video_asset.youtube_video_id,
                  asset.lead_form_asset.business_name,
                  asset.call_to_action_asset.call_to_action,
                  asset.image_asset.full_size.url
                FROM asset_group_asset
                WHERE campaign.advertising_channel_type = 'PERFORMANCE_MAX'
                  AND asset_group.status != 'REMOVED'
                  AND campaign.status != 'REMOVED'
                  AND customer.status = 'ENABLED'
                ORDER BY
                  asset_group.id ASC,
                  asset_group_asset.field_type ASC"""

    return self._google_ads_client.get_service("GoogleAdsService").search(
        customer_id=customer_id, query=query
    )

  def retrieve_sitelinks(self, customer_id: str) -> ApiResponse:
    """Retrieve all active pMax asset groups from Google Ads.

    Args:
      customer_id: Google ads customer id.

    Returns:
      Results object with Google Ads api search results.
    """
    query = """SELECT
                  customer.id,
                  customer.descriptive_name,
                  campaign.id,
                  campaign.name,
                  campaign.resource_name,
                  campaign_asset.resource_name,
                  campaign_asset.field_type,
                  campaign.advertising_channel_type,
                  campaign.status,
                  asset.sitelink_asset.description1,
                  asset.sitelink_asset.description2,
                  asset.sitelink_asset.link_text,
                  asset.final_urls,
                  asset.final_url_suffix
                  FROM campaign_asset
                  WHERE campaign.advertising_channel_type = 'PERFORMANCE_MAX'
                  AND campaign_asset.primary_status NOT IN ('NOT_ELIGIBLE', 'REMOVED', 'UNKNOWN')
                  AND campaign_asset.field_type = 'SITELINK'
                  AND campaign.status != 'REMOVED'
                  AND customer.status = 'ENABLED'"""

    return self._google_ads_client.get_service("GoogleAdsService").search(
        customer_id=customer_id, query=query
    )

  def retrieve_all_asset_groups(self, customer_id: str) -> ApiResponse:
    """Retrieve all active pMax asset groups from Google Ads.

    Args:
      customer_id: Google ads customer id.

    Returns:
      Results object with Google Ads api search results.
    """
    query = """SELECT
                  asset_group.name,
                  asset_group.id,
                  campaign.name,
                  campaign.id,
                  customer.descriptive_name,
                  customer.id
                FROM asset_group
                WHERE campaign.advertising_channel_type = 'PERFORMANCE_MAX'
                  AND asset_group.status != 'REMOVED'
                  AND campaign.status != 'REMOVED'
                  AND customer.status = 'ENABLED'
                ORDER BY
                  campaign.id ASC,
                  asset_group.id ASC"""

    return self._google_ads_client.get_service("GoogleAdsService").search(
        customer_id=customer_id, query=query
    )

  def retrieve_all_campaigns(self, customer_id: str) -> ApiResponse:
    """Retrieve all active pMax campaigns from Google Ads.

    Args:
      customer_id: Google ads customer id.

    Returns:
      Results object with Google Ads api search results.
    """
    query = """
        SELECT
          campaign.name,
          campaign.id,
          customer.descriptive_name,
          customer.id
        FROM campaign
        WHERE campaign.advertising_channel_type = 'PERFORMANCE_MAX'
          AND campaign.status != 'REMOVED'
          AND customer.status = 'ENABLED'
        ORDER BY
          campaign.id ASC"""

    return self._google_ads_client.get_service("GoogleAdsService").search(
        customer_id=customer_id, query=query
    )

  def retrieve_all_customers(self, login_customer_id: str) -> ApiResponse:
    """Retrieve all active customers from Google Ads.

    Args:
      login_customer_id: Google ads customer id.

    Returns:
      Results object with Google Ads api search results.
    """
    query = f"""SELECT
                  customer.id,
                  customer_client.descriptive_name,
                  customer_client.id
                FROM customer_client
                WHERE customer_client.status = 'ENABLED'
                AND customer_client.id != {login_customer_id}
                ORDER BY
                  customer.id ASC"""

    return self._google_ads_client.get_service("GoogleAdsService").search(
        customer_id=login_customer_id, query=query
    )
