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
"""Provides functionality to create sitelinks."""

from enums.campaign_list_column_map import campaignListColumnMap
from enums.sheets import sheets
from enums.sitelink_column_map import sitelinksColumnMap

# Using global variable as per the code sample to assign temp ids to asest operations.
# https://github.com/googleads/google-ads-python/blob/310a10b18f3ce91fc5c885f63ba090641972fbe1/examples/advanced_operations/add_performance_max_campaign.py
_ASSET_TEMP_ID = -1


class SitelinkService:
  """Class for Sitelink Creation.

  Contains all methods to create pMax Campaings in Google Ads.
  """

  def __init__(self, google_ads_service, sheet_service, google_ads_client):
    """Constructs the CampaignService instance.

    Args:
      google_ads_service: instance of the google_ads_service for dependancy
        injection.
      sheet_service: instance of sheet_service for dependancy injection.
      google_ads_client: Instance of Google Ads API client.
    """

    self._google_ads_client = google_ads_client
    self.google_ads_service = google_ads_service
    self.sheet_service = sheet_service
    self.sheet_name = "Sitelinks"

  def _create_sitelink(self, customer_id, campaign_id, row):
    """Set up mutate object for creating campaign and budget for the campaign.

    Args:
      customer_id: Google ads customer id.
      campaign_id: Name for the campaign.
      row: Array of string values to create sitelink.

    Returns:
      mutate_operations, resource_name
    """
    asset_service = self._google_ads_client.get_service("AssetService")
    resource_name = asset_service.asset_path(customer_id, _ASSET_TEMP_ID)
    _ASSET_TEMP_ID -= 1

    sitelink_operation = self._google_ads_client.get_type("MutateOperation")

    sitelink_asset = sitelink_operation.asset_operation.create
    sitelink_asset.final_urls.append(row[sitelinksColumnMap.FINAL_URLS.value])
    sitelink_asset.resource_name = resource_name
    sitelink_asset.sitelink_asset.description1 = row[
        sitelinksColumnMap.DESCRIPTION1.value
    ]
    sitelink_asset.sitelink_asset.description2 = row[
        sitelinksColumnMap.DESCRIPTION2.value
    ]
    sitelink_asset.sitelink_asset.link_text = row[sitelinksColumnMap.LINK_TEXT.value]
    return (sitelink_operation, resource_name)

  def process_sitelink_data(self, sitelink_data, campaign_data):
    """Creates campaigns via google API based.

    Args:
      sitelink_data: Array for creating new sitelinks.
      campaign_data: Array of existing Campaigns in Google Ads.
    """
    sheet_id = self.sheet_service.get_sheet_id(self.sheet_name)
    sitelink_operations = {}
    row_to_operations_mapping = {}
    sheet_row_index = 0
    # The map used to store all the API results and error messages.
    sheet_results = {}

    for row in sitelink_data:

      search_key = (
          row[sitelinksColumnMap.CUSTOMER_NAME.value]
          + ";"
          + row[sitelinksColumnMap.CAMPAIGN_NAME.value]
      )

      campaign_details = self.sheet_service.get_sheet_row(
          search_key, campaign_data, sheets.CAMPAIGN.value
      )

      if campaign_details:

        customer_id = campaign_details[campaignListColumnMap.CUSTOMER_ID.value]
        campaign_id = campaign_details[campaignListColumnMap.CAMPAIGN_ID.value]
        campaign_name = row[sitelinksColumnMap.CAMPAIGN_NAME.value]
        customer_name = row[sitelinksColumnMap.CUSTOMER_NAME.value]

        if (
            row[sitelinksColumnMap.STATUS.value] != "UPLOADED"
            and len(row) > sitelinksColumnMap.DESCRIPTION2.value
        ):

          sitelink_alias = (
              row[sitelinksColumnMap.CUSTOMER_NAME.value]
              + ";"
              + row[sitelinksColumnMap.CAMPAIGN_NAME.value]
              + ";"
              + row[sitelinksColumnMap.LINK_TEXT.value]
              + ";"
              + row[sitelinksColumnMap.FINAL_URLS.value]
              + ";"
              + row[sitelinksColumnMap.DESCRIPTION1.value]
              + ";"
              + row[sitelinksColumnMap.DESCRIPTION2.value]
          )

          if customer_id not in sitelink_operations:
            sitelink_operations[customer_id] = {}

          if sitelink_alias not in sitelink_operations[customer_id]:
            sitelink_operations[customer_id][sitelink_alias] = []

          # Check if sheet results for the input sheet row already exists. If not
          # create a new empty map.
          if sheet_row_index not in sheet_results:
            sheet_results[sheet_row_index] = {}

          # Preset the default map values for Status and Message.
          sheet_results[sheet_row_index]["status"] = None
          sheet_results[sheet_row_index]["message"] = None
          sheet_results[sheet_row_index]["asset_group_asset"] = None

          row_number = self.sheet_service.get_row_number_by_value(
              [
                  row[sitelinksColumnMap.CUSTOMER_NAME.value],
                  row[sitelinksColumnMap.CAMPAIGN_NAME.value],
              ],
              sitelink_data,
              sitelinksColumnMap.CUSTOMER_NAME.value,
          )

          sitelink_operation, resource_name = self._create_sitelink(
              customer_id, campaign_id, row
          )
          sitelink_operations[customer_id][sitelink_alias].append(
              sitelink_operation
          )

          link_asset_campaign_operation = self.link_sitelink_to_campaign(
              customer_id, campaign_id, resource_name
          )
          sitelink_operations[customer_id][sitelink_alias].append(
              link_asset_campaign_operation
          )

          # Add reource name index and sheet row number to map, for
          # processing error and status messages to sheet.
          if not resource_name in row_to_operations_mapping:
            row_to_operations_mapping[resource_name] = []
          row_to_operations_mapping[resource_name].append(sheet_row_index)

      sheet_row_index += 1

    if len(sitelink_operations) > 0:

      self.sheet_service.process_api_operations(
          "SITELINKS",
          sitelink_operations,
          sheet_results,
          row_to_operations_mapping,
          None,
          self.sheet_name,
      )

  def link_sitelink_to_campaign(self, customer_id, campaign_id, resource_name):
    """Creates sitelink assets, which can be added to campaigns.

    Args:
      customer_id: The customer ID for which to add the keyword.
      campaign_id: The campaign to which sitelinks will be added.
      resource_name: sitelink asset resource name.
    """
    campaign_service = self._google_ads_client.get_service("CampaignService")
    operation = self._google_ads_client.get_type("MutateOperation")
    campaign_asset = operation.campaign_asset_operation.create
    campaign_asset.asset = resource_name
    campaign_asset.campaign = campaign_service.campaign_path(
        customer_id, campaign_id
    )
    campaign_asset.field_type = (
        self._google_ads_client.enums.AssetFieldTypeEnum.SITELINK
    )
    return operation
