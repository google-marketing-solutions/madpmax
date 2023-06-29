from google.ads import googleads
from google.api_core import protobuf_helpers
from google.ads.googleads.errors import GoogleAdsException
from uuid import uuid4

import enum
import auth
import sheet_api
import ads_api
import yaml


class main():

    # Input column map, descripting the column names for the input data from the
    # RawData sheet.
    class newAssetsColumnMap(enum.IntEnum):
        ASSET_GROUP_ALIAS = 0,
        ASSET_TYPE = 1,
        ASSET_TEXT = 2,
        ASSET_CALL_TO_ACTION = 3,
        ASSET_URL = 4,
        STATUS = 5,
        MESSAGE = 6

    class assetGroupListColumnMap(enum.IntEnum):
        ASSET_GROUP_ALIAS = 0,
        ASSET_GROUP_NAME = 1,
        ASSET_GROUP_ID = 2,
        CAMPAIGN_NAME = 3,
        CAMPAIGN_ID = 4,
        CUSTOMER_NAME = 5,
        CUSTOMER_ID = 6

    class newAssetGroupsColumnMap(enum.IntEnum):
        ASSET_GROUP_ALIAS = 0,
        CAMPAIGN_ALIAS = 1,
        ASSET_CHECK = 2,
        ASSET_GROUP_NAME = 3,
        FINAL_URL = 4,
        MOBILE_URL = 5,
        PATH1 = 6,
        PATH2 = 7,
        CAMPAIGN_STATUS = 8,
        STATUS = 9,
        MESSAGE = 10

    class newCampaignsColumnMap(enum.IntEnum):
        CAMPAIGN_ALIAS = 0,
        CAMPAIGN_SETTINGS_ALIAS = 1,
        CAMPAIGN_NAME = 2,
        START_DATE = 3,
        END_DATE = 4,
        CUSTOMER_ID = 5

    class campaignListColumnMap(enum.IntEnum):
        CAMPAIGN_ALIAS = 0,
        CAMPAIGN_NAME = 1,
        CAMPAIGN_ID = 2,
        CUSTOMER_NAME = 3,
        CUSTOMER_ID = 4

    class assetGroupsUploadStatus(enum.Enum):
        COMPLETED = "COMPLETED"

    def __init__(self):
        # Configuration input values.
        self.includeVideo = False
        self.sheetName = "NewAssets"
        # Sample spreadsheet https://docs.google.com/spreadsheets/d/16Gn5ImKQqf7p0tNUVtciJLWCCxC6etN1H9RIdzqlHxE/edit#gid=755896892
        self.googleSpreadSheetId = "16Gn5ImKQqf7p0tNUVtciJLWCCxC6etN1H9RIdzqlHxE"
        self.rowLimit = 2000
        with open('google-ads.yaml', 'r') as ymlfile:
            cfg = yaml.safe_load(ymlfile)

        credentials = auth.get_credentials_from_file(
            cfg['oauth_token'], cfg['refresh_token'], cfg['client_id'], cfg['client_secret'])

        self.sheetService = sheet_api.SheetsService(credentials)
        self.googleAdsService = ads_api.AdService("google-ads.yaml")

    """Reads the campaigns and asset groups from the input sheet, creates assets
    for the assets provided. Removes the provided placeholder assets, and writes
    the results back to the spreadsheet."""

    def create_api_operations(self):
        """
        TODO
        """
        # Get Values from input sheet
        asset_values = self.sheetService._get_sheet_values(
            self.sheetName+"!A6:G", self.googleSpreadSheetId)

        # all operations across multiple assetGroups where the key is an assetGroup
        asset_operations = {}
        asset_group_operations = {}
        asset_group_text_operations = {}
        asset_group_headline_operations = {}
        asset_group_description_operations = {}
        asset_group_sheetlist = {}

        # The map used to store all the API results and error messages.
        sheet_results = {}

        # map to link sheet input rows to the asset operations for status and error handling.
        row_to_operations_mapping = {}
        sheet_row_index = 0

        # Loop through of the input values in the provided spreadsheet / sheet.
        for row in asset_values:
            new_asset_group = False
            mutate_operations = []
            asset_group_details = None

            # Skip to next row in case Status is Success.
            if self.newAssetsColumnMap.STATUS < len(row) and row[self.newAssetsColumnMap.STATUS] == "SUCCESS":
                sheet_row_index += 1
                continue

            asset_group_alias = row[self.newAssetsColumnMap.ASSET_GROUP_ALIAS]

            # Use the Asset Group Alias to get Asset Group info from the Google sheet.
            asset_group_details = self.sheetService._get_sheet_row(
                row[self.newAssetsColumnMap.ASSET_GROUP_ALIAS], "AssetGroupList", "!A6:H", self.googleSpreadSheetId)

            if asset_group_details:
                asset_group_id = asset_group_details[self.assetGroupListColumnMap.ASSET_GROUP_ID]
                customer_id = asset_group_details[self.assetGroupListColumnMap.CUSTOMER_ID]

                if asset_group_alias not in asset_operations:
                    asset_operations[asset_group_alias] = []

            # Check if Asset Group already exists in Google Ads. If not create Asset Group operation.
            elif not asset_group_details:
                new_asset_group = True
                # GENERATE ASSET GROUP OPERATION.
                new_asset_group_details = self.sheetService._get_sheet_row(
                    row[self.newAssetsColumnMap.ASSET_GROUP_ALIAS], "NewAssetGroups", "!A6:I", self.googleSpreadSheetId)
                
                campaign_details = self.sheetService._get_sheet_row(
                    new_asset_group_details[self.newAssetGroupsColumnMap.CAMPAIGN_ALIAS], "CampaignList", "!A6:E", self.googleSpreadSheetId)
                
                if not campaign_details or not new_asset_group_details:
                    continue

                customer_id = campaign_details[self.campaignListColumnMap.CUSTOMER_ID]
                campaign_id = campaign_details[self.campaignListColumnMap.CAMPAIGN_ID]

                if asset_group_alias not in asset_group_operations:
                    asset_group_operations[asset_group_alias] = []
                    asset_group_headline_operations[asset_group_alias] = []
                    asset_group_description_operations[asset_group_alias] = []
                    asset_group_mutate_operation, asset_group_id = self.googleAdsService._create_asset_group(
                        new_asset_group_details, campaign_id, customer_id)
                    mutate_operations.append(
                        asset_group_mutate_operation)
                    
                    # Create AssetGroupList Sheet array.
                    asset_group_sheetlist[asset_group_alias] = [asset_group_alias, new_asset_group_details[self.newAssetGroupsColumnMap.ASSET_GROUP_NAME], asset_group_id] + campaign_details[1:]

            # Check if sheet results for the input sheet row already exists. If not create a new empty map.
            if sheet_row_index not in sheet_results:
                sheet_results[sheet_row_index] = {}

            # Preset the default map values for Status and Message.
            sheet_results[sheet_row_index]["status"] = None
            sheet_results[sheet_row_index]["message"] = None

            if self.newAssetsColumnMap.ASSET_URL.value < len(row):
                asset_url = row[self.newAssetsColumnMap.ASSET_URL]
            else:
                asset_url = ""

            # Asset name / asset type
            asset_type = row[self.newAssetsColumnMap.ASSET_TYPE]
            asset_name_or_text = row[self.newAssetsColumnMap.ASSET_TEXT]
            asset_action_selection = row[self.assetsColumnMap.ASSET_CALL_TO_ACTION]

            if asset_type == "YOUTUBE_VIDEO":    
               asset_mutate_operation, asset_resource, field_type = self.googleSheetId._create_video_asset(asset_url, asset_type, customer_id)
               asset_operations[asset_group_alias].append(asset_mutate_operation)

               asset_mutate_operation = self.googleAdsService._add_asset_to_asset_group(asset_resource, asset_group_id, field_type, customer_id)
               asset_operations[asset_group_alias].append(asset_mutate_operation)
            elif asset_type == "IMAGE" or asset_type == "LOGO":
                # TODO add removal of images if needed
                # TODO add image error handling
                asset_mutate_operation, asset_resource, field_type = self.googleAdsService._create_image_asset(
                    asset_url, asset_name_or_text + f" #{uuid4()}", asset_type, customer_id)
                mutate_operations.append(
                    asset_mutate_operation)

                asset_mutate_operation = self.googleAdsService._add_asset_to_asset_group(
                    asset_resource, asset_group_id, field_type, customer_id)
                mutate_operations.append(
                    asset_mutate_operation)
            elif asset_type == "HEADLINE" or asset_type == "DESCRIPTION":
                create_asset_operation, asset_resource, field_type = self.googleAdsService._create_text_asset(
                    asset_name_or_text, asset_type, customer_id)
                mutate_operations.append(
                    create_asset_operation)

                if not new_asset_group:
                    add_asset_operation = self.googleAdsService._add_asset_to_asset_group(
                        asset_resource, asset_group_id, field_type, customer_id)
                    mutate_operations.append(
                        add_asset_operation)
            elif asset_type == "LONG_HEADLINE" or asset_type == "BUSINESS_NAME":
                create_asset_operation, asset_resource, field_type = self.googleAdsService._create_text_asset(
                    asset_name_or_text, asset_type, customer_id)
                mutate_operations.append(
                    create_asset_operation)

                add_asset_operation = self.googleAdsService._add_asset_to_asset_group(
                    asset_resource, asset_group_id, field_type, customer_id)
                mutate_operations.append(
                    add_asset_operation)
            elif asset_type == "CALL_TO_ACTION":   
                asset_mutate_operation, asset_resource, field_type = self.googleAdsService._create_call_to_action_asset(asset_action_selection, customer_id)
                asset_operations[asset_group_alias].append(asset_mutate_operation)

                asset_mutate_operation = self.googleAdsService._add_asset_to_asset_group(asset_resource, asset_group_id, field_type, customer_id)
                asset_operations[asset_group_alias].append(asset_mutate_operation)

            # Check if asset operation for the Asset Group already exists. If not create a new list.
            if not new_asset_group:
                asset_operations[asset_group_alias] += mutate_operations
            elif new_asset_group:
                if asset_type == "HEADLINE":
                    asset_group_headline_operations[asset_group_alias].append(
                        create_asset_operation)
                if asset_type == "DESCRIPTION":
                    asset_group_description_operations[asset_group_alias].append(
                        create_asset_operation)
                asset_group_operations[asset_group_alias] += mutate_operations

            # Add reource name index and sheet row number to map, for processing error and status messages to sheet.
            row_to_operations_mapping[asset_resource] = sheet_row_index

            sheet_row_index += 1

        # Update Assets only in Google Ads
        self.process_api_operations(
            "ASSETS", asset_operations, sheet_results, row_to_operations_mapping, asset_group_sheetlist, customer_id)

        # Create a new Asset Group and Update Assets.
        headlines = self.googleAdsService._create_multiple_text_assets(
            asset_group_headline_operations, customer_id)
        descriptions = self.googleAdsService._create_multiple_text_assets(
            asset_group_description_operations, customer_id)
        asset_group_operations, row_to_operations_mapping = self.googleAdsService.compile_asset_group_operations(
            asset_group_operations, headlines, descriptions, row_to_operations_mapping, customer_id)
        self.process_api_operations(
            "ASSET_GROUPS", asset_group_operations, sheet_results, row_to_operations_mapping, asset_group_sheetlist, customer_id)

    def process_api_operations(self, mutate_type, mutate_operations, sheet_results, row_to_operations_mapping, asset_group_sheetlist, customer_id):
        """Logic to process API bulk operations based on type.

        Based on the request type, the bulk API requests will be send to the API. Corresponding API response will be
        parsed and processed both as terminal output and as output to the Google Sheet.
        """
        # Bulk requests are grouped by Asset Group Alias and are processed one by one in bulk.
        for asset_group_alias in mutate_operations:
            # Send the bulk request to the API and retrieve the API response object and the compiled Error message for asset Groups.
            asset_group_response, asset_group_error_message = self.googleAdsService._bulk_mutate(mutate_type,
                                                                                                 mutate_operations[asset_group_alias], customer_id)

            # Check if a successful API response, if so, process output.
            if asset_group_response:
                
                sheet_results.update(self.googleAdsService.process_asset_results(
                    asset_group_response, mutate_operations[asset_group_alias], row_to_operations_mapping))
                
                if mutate_type == "ASSET_GROUPS":
                    row_number = self.sheetService._get_row_number(
                        asset_group_alias, "NewAssetGroups", "!A6:I", self.googleSpreadSheetId)
                    sheet_id = self.sheetService.get_sheet_id("NewAssetGroups", self.googleSpreadSheetId)

                    self.sheetService.update_asset_group_sheet_status(
                        "SUCCESS", row_number, sheet_id, self.googleSpreadSheetId)
                    
                    asset_group_sheetlist[asset_group_alias][2] = asset_group_response.mutate_operation_responses[0].asset_group_result.resource_name.split("/")[-1]
                    sheet_id = self.sheetService.get_sheet_id("AssetGroupList", self.googleSpreadSheetId)

                    self.sheetService.add_new_asset_group_to_list_sheet(
                            asset_group_sheetlist[asset_group_alias], sheet_id, self.googleSpreadSheetId)
            # In case Asset Group creation returns an error string, updated the results object and process to sheet.
            elif asset_group_error_message and mutate_type == "ASSET_GROUPS":
                sheet_results.update(self.googleAdsService.process_asset_group_results(
                    asset_group_error_message, mutate_operations[asset_group_alias], row_to_operations_mapping))
                row_number = self.sheetService._get_row_number(
                    asset_group_alias, "NewAssetGroups", "!A6:I", self.googleSpreadSheetId)
                
                sheet_id = self.sheetService.get_sheet_id("NewAssetGroups", self.googleSpreadSheetId)

                self.sheetService.update_asset_group_sheet_status(
                    asset_group_error_message, row_number, sheet_id, self.googleSpreadSheetId)

        self.sheetService.update_asset_sheet_status(sheet_results, self.sheetService.get_sheet_id(
            self.sheetName, self.googleSpreadSheetId), self.googleSpreadSheetId)


cp = main()
cp.create_api_operations()
