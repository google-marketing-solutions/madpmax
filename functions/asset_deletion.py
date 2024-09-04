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

from collections.abc import Mapping
from typing import TypeAlias
import ads_api
from google.ads.googleads import client
from sheet_api import SheetsService

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
