# Copyright 2024 Google LLC

# Licensed under the Apache License, Version 2.0 (the "License")
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

# https: // www.apache.org / licenses / LICENSE - 2.0


# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for Asset Deletion."""

from typing import Final
from unittest import mock
from asset_deletion import AssetDeletionService
import data_references
import pytest


_CUSTOMER_ID: Final[str] = "customer_id_1"
_CAMPAIGN_ID: Final[str] = "campaign_id_1"
_VALID_SHEET_DATA: Final[list[list[str]]] = [
    [
        "UPLOADED",
        "TRUE",
        "Test Customer 1",
        "Test Campaign 1",
        "Test Asset Group 1",
        "HEADLINE",
        "Test Headline 1",
        "",
        "",
        "",
        "",
        "customers/1234567890/assetGroupAssets/1234567890~1234567890~HEADLINE",
    ],
    [
        "",
        "TRUE",
        "Test Customer 1",
        "Test Campaign 1",
        "Test Asset Group 1",
        "HEADLINE",
        "Test Headline 1",
        "",
        "",
        "",
        "",
        "",
    ],
    [
        "UPLOADED",
        "FALSE",
        "Test Customer 2",
        "Test Campaign 2",
        "Test Asset Group 1",
        "HEADLINE",
        "Test Headline 1",
        "",
        "",
        "",
        "",
        "customers/1234567890/assetGroupAssets/1234567890~1234567890~HEADLINE",
    ],
    [
        "UPLOADED",
        "TRUE",
        "Test Customer 2",
        "Test Campaign 2",
        "Test Asset Group 1",
        "HEADLINE",
        "Test Headline 1",
        "",
        "",
        "",
        "",
        "",
    ]
]


class DotDict(dict):
  """Class to convert dictionary to dot notation."""
  __setattr__ = dict.__setitem__
  __delattr__ = dict.__delitem__

  def __init__(self, data):
    if isinstance(data, str):
      data = json.loads(data)

    for name, value in data.items():
      setattr(self, name, self._wrap(value))

  def __getattr__(self, attr):
    def _traverse(obj, attr):
      if self._is_indexable(obj):
        try:
          return obj[int(attr)]
        except:
          return None
      elif isinstance(obj, dict):
        return obj.get(attr, None)
      else:
        return attr

    if "." in attr:
      return reduce(_traverse, attr.split("."), self)
    return self.get(attr, None)

  def _wrap(self, value):
    if self._is_indexable(value):
      # (!) recursive (!)
      return type(value)([self._wrap(v) for v in value])
    elif isinstance(value, dict):
      return DotDict(value)
    else:
      return value

  @staticmethod
  def _is_indexable(obj):
    return isinstance(obj, (tuple, list, set, frozenset))

# Dictionary Template mocking the Google Ads API response class.
MockMutateGoogleAdsResponse = {
    "partial_failure_error": {
        "code": None,
        "message": None,
        "details": [
            {
                "value": {
                    "errors": [{
                        "error_code": None,
                        "location": {
                            "field_path_elements": [{"index": None}]
                        },
                        "message": None
                    }]
                }
            }
        ]
    },
    "mutate_operation_responses": []
}


@pytest.fixture
def service_mocks():
  """Fixture to set up your mocks."""
  google_ads_client = mock.MagicMock()
  google_ads_service = mock.Mock()
  sheet_service = mock.MagicMock()

  return google_ads_client, google_ads_service, sheet_service


class MockGoogleAdsFailure:
  """Mock Google Ads API Failure Object, required for testing."""
  errors: []
  request_id: str

  def deserialize(self):
    return self


@pytest.mark.parametrize(
    "row_num, asset_group_asset",
    [(
        0,
        "customers/1234567890/assetGroupAssets/1234567890~1234567890~HEADLINE")
     ])
@mock.patch("asset_deletion.AssetDeletionService.delete_asset")
@mock.patch("utils.retrieve_customer_id")
def test_process_asset_deletion_input(mock_retrieve_customer_id,
    mock_delete_asset, service_mocks, row_num, asset_group_asset):
  """Test process_asset_deletion_input method in AssetDeletionService.

  Verifying wheter the returns the expected data.
  """
  google_ads_client, google_ads_service, sheet_service = service_mocks
  asset_service = AssetDeletionService(
      google_ads_client, google_ads_service, sheet_service)

  mock_delete_asset.return_value = {
      "remove": asset_group_asset
  }
  mock_retrieve_customer_id.return_value = _CUSTOMER_ID
  operations, row_mapping = asset_service.process_asset_deletion_input(
      _VALID_SHEET_DATA
  )
  expected_operations = {
      _CUSTOMER_ID: [
          {
              "remove": asset_group_asset
          }
      ]
  }
  expected_row_mapping = {_CUSTOMER_ID: [row_num]}

  assert operations == expected_operations, "%s != %s" % (
      operations, expected_operations)
  assert row_mapping == expected_row_mapping, "%s != %s" % (
      row_mapping, expected_row_mapping)


@pytest.mark.parametrize(
    "asset_group_asset",
    [(
        "customers/1234567890/assetGroupAssets/1234567890~1234567890~HEADLINE"),
     (None)
    ])
def test_create_delete_asset_object(service_mocks, asset_group_asset):
  """Test delete_asset method in AssetDeletionService.

  Verify if return object contains expected structure and values.
  """
  google_ads_client, google_ads_service, sheet_service = service_mocks
  asset_service = AssetDeletionService(
      google_ads_client, google_ads_service, sheet_service)

  asset_resource = asset_group_asset

  delete_asset_operation = asset_service.delete_asset(
      asset_resource)

  if delete_asset_operation:
    output = delete_asset_operation.asset_group_asset_operation.remove
  else:
    output = delete_asset_operation

  assert output == asset_resource, "%s != %s" % (
      output, asset_resource)


@pytest.mark.parametrize(
    "row_num,asset_group_asset,error_message,error_code",
    [(0,
      "customers/1234567890/assetGroupAssets/1234567890~1234567890~HEADLINE",
      None,
      None),
     (0,
      "invalid_resource_name",
      "Error Message",
      "Error Code")
    ])
def test_process_asset_errors(
        service_mocks, row_num, asset_group_asset, error_message, error_code):
  """Test process_asset_errors method in AssetDeletionService.

  Verifying wheter the service output is in the expected format when there
  are not partial failures returned in the Google Ads API response.
  """
  google_ads_client, google_ads_service, sheet_service = service_mocks
  asset_service = AssetDeletionService(
      google_ads_client, google_ads_service, sheet_service)
  opererations_dict = {
      "asset_group_asset_operation": {
          "remove": asset_group_asset
      }
  }
  operations = [
      DotDict(opererations_dict)
  ]
  mock_response = DotDict(MockMutateGoogleAdsResponse.copy())

  expected_result = {
      row_num: {
          "status": data_references.RowStatus.uploaded,
          "message": (f"Error message: {error_message}"
                      f"\n\tError code: {error_code}"),
          "asset_group_asset": asset_group_asset
      }
  }

  if error_message:
    mock_response.partial_failure_error.details[0].value.errors[
        0].error_code = error_code
    mock_response.partial_failure_error.details[0].value.errors[
        0].message = error_message
    mock_response.partial_failure_error.details[0].value.errors[
        0].location.field_path_elements[0].index = row_num
  else:
    mock_response.partial_failure_error = None
    expected_result = {}

  google_ads_client.get_type.return_value = MockGoogleAdsFailure()

  result = asset_service.process_asset_errors(
      mock_response, [row_num], operations)

  # Assertions
  assert result == expected_result, "%s != %s" % (
      result, expected_result)


@pytest.mark.parametrize(
    "row_nums,asset_group_asset,expected_rows,expected_errors",
    [([0],
      "customers/1234567890/assetGroupAssets/1234567890~1234567890~HEADLINE",
      [0],
      {}),
     ([0],
      "invalid_resource_name",
      [],
      {0: {"message": "Error code: request_error: RESOURCE_NAME_MALFORMED"}}),
     ([],
      "",
      [],
      {})])
@mock.patch("asset_deletion.AssetDeletionService.process_asset_errors")
def test_process_api_deletion_operations(
        mock_process_asset_errors, service_mocks, row_nums, asset_group_asset,
        expected_rows, expected_errors):
  """Test process_api_deletion_operations method in AssetDeletionService.

  Verifying wheter the service calls the correct function.
  """
  google_ads_client, google_ads_service, sheet_service = service_mocks
  asset_service = AssetDeletionService(
      google_ads_client, google_ads_service, sheet_service)

  row_to_operations_mapping = {_CUSTOMER_ID: row_nums}
  operations = {
      _CUSTOMER_ID: [
          {
              "asset_group_asset_operation": {
                  "remove": asset_group_asset
              }
          }
      ]
  }

  google_ads_service.bulk_mutate.return_value = ("Partial Response", None)
  mock_process_asset_errors.return_value = expected_errors

  (
      rows_for_removal, error_sheet_output
  ) = asset_service.process_api_deletion_operations(
      operations, row_to_operations_mapping)

  assert rows_for_removal == expected_rows, "%s != %s" % (
      rows_for_removal, expected_rows)
  assert error_sheet_output == expected_errors, "%s != %s" % (
      error_sheet_output, expected_errors)


@pytest.mark.parametrize(
    "row_num, asset_group_asset",
    [(
        0,
        "customers/1234567890/assetGroupAssets/1234567890~1234567890~HEADLINE"
    )])
@mock.patch(
    "asset_deletion.AssetDeletionService.process_api_deletion_operations")
@mock.patch("asset_deletion.AssetDeletionService.process_asset_deletion_input")
def test_asset_deletion(
        mock_process_asset_deletion_input, mock_process_api_deletion_operations,
        service_mocks, row_num, asset_group_asset):
  """Test process_asset_deletion_input method in AssetDeletionService.

  Verifying wheter the returns the expected data.
  """
  google_ads_client, google_ads_service, sheet_service = service_mocks
  asset_service = AssetDeletionService(
      google_ads_client, google_ads_service, sheet_service)

  mock_process_asset_deletion_input.return_value = ({
      _CUSTOMER_ID: [
          {
              "remove": asset_group_asset
          }
      ]
  }, {_CUSTOMER_ID: [row_num]})

  mock_process_api_deletion_operations. return_value = (
      [row_num], {})

  asset_service.asset_deletion(_VALID_SHEET_DATA)
  sheet_service.remove_sheet_rows.assert_called_once_with(
      [row_num],
      data_references.SheetNames.assets
  )
