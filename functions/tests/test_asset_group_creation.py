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
from unittest import mock
from asset_group_creation import AssetGroupService


class TestAssetGroupService(unittest.TestCase):

  def setUp(self):
    self.google_ads_service = mock.Mock()
    self._google_ads_client = mock.Mock()
    self.sheet_service = mock.MagicMock()
    self.asset_service = mock.Mock()
    self.asset_group_service = AssetGroupService(self.google_ads_service,
                                                 self.sheet_service,
                                                 self.asset_service,
                                                 self._google_ads_client
                                                 )



  def test_compile_campaign_alias_return_alias_when_get_data(self):
    input_sheet_row = ["", "SUCCESS", "customer1", "test_camapign", "AssetGroup1", "ENABLED", "http://example"]
    result = self.asset_group_service.compile_campaign_alias(input_sheet_row)

    self.assertEqual(result, "customer1;test_camapign")