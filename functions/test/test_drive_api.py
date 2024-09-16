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
"""Tests for Sheet Service."""

import unittest
from unittest import mock
import drive_api


class TestSheetService(unittest.TestCase):

  def setUp(self):
    super().setUp()
    self.credentials = mock.Mock()
    self._google_ads_client = mock.Mock()
    self.google_ads_service = mock.MagicMock()
    self.drive_service = drive_api.DriveService(self.credentials)

  @mock.patch("drive_api.DriveService._download_drive_asset")
  def test_call_drive_download_for_drive_url(self, mock_download_drive_asset):
    url = "https://drive.google.com/file/d/1Mhj67eq5PKL613GMwx-cd4fd_gu3Lg0nYG"
    self.drive_service.download_asset_content(url)
    mock_download_drive_asset.assert_has_calls([mock.call(url)])

  @mock.patch("requests.get")
  def test_call_make_request_for_non_drive(self, mock_requests):
    mock_response = mock.Mock()

    # Set the status code and other attributes as needed
    mock_response.status_code = 200
    mock_response.text = '{"key": "value"}'
    mock_response.content = b"Some binary content"
    mock_response.headers = {"Content-Type": "application/json"}
    url = "https://tpc.googlesyndication.com/simgad/11111111111111111111111"
    mock_requests.return_value = mock_response
    self.drive_service.download_asset_content(url)
    mock_requests.assert_has_calls([mock.call(url)])

  def test_extract_file_id(self):
    url = "https://drive.google.com/file/d/1Mhj67eq5PKL613GMwx-cd4fd_gu3Lg0nYG"
    file_id = self.drive_service.extract_file_id(url)
    self.assertEqual("1Mhj67eq5PKL613GMwx-cd4fd_gu3Lg0nYG", file_id)
