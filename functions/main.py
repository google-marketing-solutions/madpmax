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
from cloudevents.http import CloudEvent
import functions_framework
from google.ads import googleads
import pubsub
import yaml


class main:
  # Input column map, descripting the column names for the input data from the
  # RawData sheet.

  def __init__(self):
    with open("config.yaml", "r") as config_file:
      config = yaml.safe_load(config_file)

    self.google_ads_client = googleads.client.GoogleAdsClient.load_from_storage(
        "config.yaml", version="v14"
    )

    self.pubsub_utils = pubsub.PubSub(config, self.google_ads_client)


@functions_framework.cloud_event
def pmax_trigger(cloud_event: CloudEvent):
  """Listener function for pubsub trigger.

  Based on trigger message activate corresponding mad Max
  function.

  Args:
    cloud_event: Cloud event class for pubsub event.
  """
  if cloud_event:
    # Print out the data from Pub/Sub, to prove that it worked
    print(
        "------- START "
        + base64.b64decode(cloud_event.data["message"]["data"]).decode()
        + " EXECUTION -------"
    )

    cp = main().pubsub_utils
    message_data = base64.b64decode(
        cloud_event.data["message"]["data"]
    ).decode()

    match message_data:
      case "REFRESH":
        cp.refresh_spreadsheet()
      case "UPLOAD":
        cp.create_api_operations()
      case "REFRESH_CUSTOMER_LIST":
        cp.refresh_customer_id_list()
      case "REFRESH_CAMPAIGN_LIST":
        cp.refresh_campaign_list()
      case "REFRESH_ASSET_GROUP_LIST":
        cp.refresh_asset_group_list()
      case "REFRESH_ASSETS_LIST":
        cp.refresh_assets_list()
      case "REFRESH_SITELINK_LIST":
        cp.refresh_sitelinks_list()

    print(
        "------- END "
        + base64.b64decode(cloud_event.data["message"]["data"]).decode()
        + " EXECUTION -------"
    )


if __name__ == "__main__":
  # GoogleAdsClient will read the google-ads.yaml configuration file in the
  # home directory if none is specified.
  pmax_operations = main().pubsub_utils
  pmax_operations.create_api_operations()

  with open("config.yaml", "r") as ymlfile:
    cfg = yaml.safe_load(ymlfile)
