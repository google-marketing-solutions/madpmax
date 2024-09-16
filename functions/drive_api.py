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

from collections.abc import Mapping
import io
from absl import logging
from googleapiclient import discovery
from googleapiclient import errors
from googleapiclient import http
import requests


# The format of Drive URL
_DRIVE_URL = "drive.google.com"


class DriveService:
  """Provides Drive APIs to download images from Drive."""

  def __init__(self, credential: Mapping[str, str]) -> None:
    """Creates a instance of drive service to handle requests.

    Args:
      credential: Drive APIs credentials.
    """
    self._drive_service = discovery.build("drive", "v3", credentials=credential)

  def download_asset_content(self, url: str) -> bytes:
    """Downloads an asset based on url, from drive or the web.

    Args:
      url: Url to fetch the asset from.

    Returns:
      Asset data array.
    """
    if _DRIVE_URL in url:
      file_id = self.extract_file_id(url)
      return self._download_drive_asset(file_id)
    else:
      response = requests.get(url)
    return io.BytesIO(response.content).read()

  def extract_file_id(self, image_url: str) -> str:
    url_parameters = image_url.split("/")
    return url_parameters[url_parameters.index("d") + 1]

  def _download_drive_asset(self, file_id: str) -> bytes:
    try:
      request = self._drive_service.files().get_media(fileId=file_id)
      file = io.BytesIO()
      downloader = http.MediaIoBaseDownload(file, request)
      done = False
      while done is False:
        status, done = downloader.next_chunk()
        logging.info(f"Download {int(status.progress() * 100)}.")

    except errors.HttpError as error:
      logging.error(f"An error occurred: {error}")
      file = None

    return file.getvalue()

  def get_file_by_name(self, file_name: str) -> str:
    """Retrieves the file by name and returns id.

    Args:
      file_name: Name of the spreadsheet file to retrieve.

    Returns:
      File id of the spreadsheet.
    """
    file_id = None
    try:
      page_token = None
      while True:
        response = (
            self._drive_service.files()
            .list(
                q=f"name = '{file_name}'",
                spaces="drive",
                fields="nextPageToken, files(id)",
                pageToken=page_token,
            )
            .execute()
        )
        for file in response.get("files", []):
          file_id = file.get("id")
          break
        page_token = response.get("nextPageToken", None)
        if page_token is None:
          break
    except http.HttpError as error:
      logging.error("An error occurred: %s ", error)
    return file_id
