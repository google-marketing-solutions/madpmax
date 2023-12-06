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
"""Main function, Used to run the mad pMax Creative Management tools."""

import base64
import auth
from cloudevents.http import CloudEvent
import functions_framework
from google.ads import googleads
import pubsub
import yaml


class main:
  # Input column map, descripting the column names for the input data from the
  # RawData sheet.

  def __init__(self):
    with open("config.yaml", "r") as ymlfile:
      cfg = yaml.safe_load(ymlfile)

    credentials = auth.get_credentials_from_file(
        cfg["access_token"],
        cfg["refresh_token"],
        cfg["client_id"],
        cfg["client_secret"],
    )
    self.google_ads_client = googleads.client.GoogleAdsClient.load_from_storage(
        "config.yaml", version="v14"
    )

    # Configuration input values.
    self.google_spread_sheet_id = cfg["spreadsheet_id"]

    self.customer_id = cfg["customer_id"]
    self.login_customer_id = cfg["login_customer_id"]

    self.pubsub_utils = pubsub.PubSub(credentials, self.google_ads_client)


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

    if message_data == "REFRESH":
      cp.refresh_spreadsheet()
    if message_data == "UPLOAD":
      cp.create_api_operations()
    if message_data == "REFRESH_CUSTOMER_LIST":
      cp.refresh_customer_id_list()
    if message_data == "REFRESH_CAMPAIGN_LIST":
      cp.refresh_campaign_list()
    if message_data == "REFRESH_ASSET_GROUP_LIST":
      cp.refresh_asset_group_list()
    if message_data == "REFRESH_ASSETS_LIST":
      cp.refresh_assets_list()
    if message_data == "REFRESH_SITELINK_LIST":
      cp.refresh_sitelinks_list()

    print(
        "------- END "
        + base64.b64decode(cloud_event.data["message"]["data"]).decode()
        + " EXECUTION -------"
    )


if __name__ == "__main__":
  # GoogleAdsClient will read the google-ads.yaml configuration file in the
  # home directory if none is specified.
  pmax_operations = main()
  pmax_operations.refresh_spreadsheet()
  pmax_operations.create_api_operations()
