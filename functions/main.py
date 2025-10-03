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
"""Main trigger, Used to run the mad pMax Creative Management tools."""

import base64
from typing import Final
from absl import logging
from cloudevents.http import CloudEvent
from data_references import ConfigFile
import functions_framework
from google.ads.googleads import client
import pubsub
import yaml

_CONFIG_FILE_NAME: Final[str] = "config.yaml"
_API_VERSIONAPI_VERSION: Final[str] = "v21"


def retrieve_config(config_name: str) -> ConfigFile:
  """Retreive configuration for using Google API.

  Args:
      config_name: Name of a config file containing API access data.

  Returns:
      ConfigFile object representing JSON structure of config file.
  """
  try:
    with open(config_name, "r") as config_file:
      return ConfigFile(**yaml.safe_load(config_file))
  except (ValueError, TypeError) as ex:
    raise TypeError("Wrong structure or type of config file.") from ex


@functions_framework.cloud_event
def pmax_trigger(cloud_event: CloudEvent) -> None:
  """Listener function for pubsub trigger.

  Based on trigger message activate corresponding mad Max
  function.

  Args:
    cloud_event: Cloud event class for pubsub event.
  """
  google_ads_client = client.GoogleAdsClient.load_from_storage(
      _CONFIG_FILE_NAME, version=_API_VERSIONAPI_VERSION
  )
  config = retrieve_config(_CONFIG_FILE_NAME)
  pubsub_utils = pubsub.PubSub(config, google_ads_client)
  if cloud_event:
    logging.info(
        "------- START %s EXECUTION -------",
        base64.b64decode(cloud_event.data["message"]["data"]).decode()
    )
    message_data = base64.b64decode(
        cloud_event.data["message"]["data"]
    ).decode()
    match message_data:
      case "REFRESH":
        pubsub_utils.refresh_spreadsheet()
      case "UPLOAD":
        pubsub_utils.create_api_operations()
      case "DELETE":
        pubsub_utils.delete_api_operations()
      case "REFRESH_CUSTOMER_LIST":
        pubsub_utils.refresh_customer_id_list()
      case "REFRESH_CAMPAIGN_LIST":
        pubsub_utils.refresh_campaign_list()
      case "REFRESH_ASSET_GROUP_LIST":
        pubsub_utils.refresh_asset_group_list()
      case "REFRESH_ASSETS":
        pubsub_utils.refresh_assets_list()
      case "REFRESH_SITELINKS":
        pubsub_utils.refresh_sitelinks_list()

    logging.info(
        "------- END %s EXECUTION -------",
        base64.b64decode(cloud_event.data["message"]["data"]).decode()
    )
