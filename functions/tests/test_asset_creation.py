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
"""Tests for Asset Creation"""

import unittest
from unittest.mock import MagicMock
from unittest.mock import Mock
from asset_creation import AssetService


class TestAssetService(unittest.TestCase):

  def setUp(self):
    self.google_ads_service = MagicMock()
    self._google_ads_client = Mock()
    self.sheet_service = MagicMock()
    self.asset_service = AssetService(
        self._google_ads_client, self.google_ads_service, self.sheet_service
    )

  def test_compile_asset_group_alias_return_alias_when_get_data(self):
    input_sheet_row = ["", "true", "customer1", "test_camapign", "AssetGroup1"]
    result = self.asset_service.compile_asset_group_alias(input_sheet_row)

    self.assertEqual(result, "customer1;test_camapign;AssetGroup1")

  def test_compile_asset_group_alias_return_none_when_no_data(self):
    input_sheet_row = ["", "true", "customer1", "test_camapign"]
    result = self.asset_service.compile_asset_group_alias(input_sheet_row)

    self.assertIsNone(result)


if __name__ == "__main__":
  unittest.main()
