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
"""Provides functionality to interact with Google Drive platform."""

import io
import googleapiclient
import requests


# The format of Drive URL
_DRIVE_URL = "drive.google.com"


class DriveService():
  """Provides Drive APIs to download images from Drive.
  """

  def __init__(self, credential):
    """Creates a instance of drive service to handle requests.

    Args:
      credential: Drive APIs credentials.
    """
    self._drive_service = googleapiclient.discovery.build(
        "drive", "v3", credentials=credential)

  def _download_asset(self, url):
    """Downloads an asset based on url, from drive or the web.

    Args:
      url: url to fetch the asset from.

    Returns:
      asset data array.
    """
    if _DRIVE_URL in url:
      return self._download_drive_asset(url)
    else:
      response = requests.get(url)
    return io.BytesIO(response.content).read()

  def get_file_by_name(self, file_name):
    """Retrieves the file by name and returns id.

    Args:
      file_name: Name of the spreadsheet file to retrieve.

    Returns:
      file id of the spreadsheet.
    """
    try:
      file_id = None
      page_token = None
      while True:
        response = self._drive_service.files().list(
            q=f"name = '{file_name}'", spaces="drive",
            fields="nextPageToken, "
            "files(id)", pageToken=page_token).execute()
        for file in response.get("files", []):
          file_id = file.get("id")
          break
        page_token = response.get("nextPageToken", None)
        if page_token is None:
          break
    except googleapiclient.http.HttpError as error:
      print(F"An error occurred: {error}")
      file = None
    return file_id
