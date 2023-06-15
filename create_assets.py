from google.ads import googleads
from google.api_core import protobuf_helpers
from google.ads.googleads.errors import GoogleAdsException
from uuid import uuid4

import enum
import auth
import sheet_api
import ads_api
import yaml
import pprint


class main():

    # Input column map, descripting the column names for the input data from the
    # RawData sheet.
    class assetsColumnMap(enum.IntEnum):
        ASSET_GROUP_ALIAS = 0,
        ASSET_TYPE = 1,
        ASSET_TEXT = 2,
        ASSET_URL = 3,
        STATUS = 4,
        MESSAGE = 5

    class assetGroupsColumnMap(enum.IntEnum):
        ASSET_GROUP_ALIAS = 0,
        ASSET_GROUP_NAME = 1,
        ASSET_GROUP_ID = 2,
        CAMPAIGN_NAME = 3,
        CAMPAIGN_ID = 4,
        START_DATE = 5,
        CUSTOMER_NAME = 6,
        CUSTOMER_ID = 7

    class assetGroupsUploadStatus(enum.Enum):
        COMPLETED = "COMPLETED"

    def __init__(self):
        # Configuration input values.
        self.includeVideo = False
        self.sheetName = "Assets"
        # Sample spreadsheet https://docs.google.com/spreadsheets/d/16Gn5ImKQqf7p0tNUVtciJLWCCxC6etN1H9RIdzqlHxE/edit#gid=755896892
        self.googleSheetId = "16Gn5ImKQqf7p0tNUVtciJLWCCxC6etN1H9RIdzqlHxE"
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

    def assetUpload(self):
        # Get Values from input sheet
        values = self.sheetService._get_sheet_values(
            self.sheetName+"!A6:E", self.googleSheetId)

        # all operations across multiple assetGroups where the key is an assetGroup
        asset_operations = {}
        sheet_results = {}

        # map to link sheet input rows to the asset operations for status and error handling.
        row_to_operations_mapping = {}
        index = 0

        # Loop through of the input values in the provided spreadsheet / sheet.
        for row in values:
            process_row = False
            if len(row) <= self.assetsColumnMap.STATUS:
                process_row = True
            elif self.assetsColumnMap.STATUS < len(row) and row[self.assetsColumnMap.STATUS] == "FAILED":
                process_row = True

            if process_row:
                asset_group_alias = row[self.assetsColumnMap.ASSET_GROUP_ALIAS]
                # TODO: Retrieve AssetGroup Resource name.
                asset_group_details = self.sheetService._get_sheet_row(
                    row[self.assetsColumnMap.ASSET_GROUP_ALIAS], "AssetGroups", self.googleSheetId)
                asset_group_id = asset_group_details[self.assetGroupsColumnMap.ASSET_GROUP_ID]
                customer_id = asset_group_details[self.assetGroupsColumnMap.CUSTOMER_ID]
                # Generate the performance max campaign object.
                # pmax_campaign_resource = self.googleAdsService._get_campaign_resource_name(self.customerId, asset_group_details[self.assetGroupsColumnMap.CAMPAIGN_ID])
                # asset_group_resource = self.googleAdsService._get_asset_group_resource_name(self.customerId, asset_group_details[self.assetGroupsColumnMap.ASSET_GROUP_ID])

                if asset_group_alias not in asset_operations:
                    asset_operations[asset_group_alias] = []
                if index not in sheet_results:
                    sheet_results[index] = {}
                sheet_results[index]["status"] = "SUCCESS"
                sheet_results[index]["message"] = ""

                if self.assetsColumnMap.ASSET_URL.value < len(row):
                    asset_url = row[self.assetsColumnMap.ASSET_URL]
                else:
                    asset_url = ""

                asset_type = row[self.assetsColumnMap.ASSET_TYPE]
                # Asset name / asset type
                asset_text = row[self.assetsColumnMap.ASSET_TEXT]

                if asset_type == "IMAGE" or asset_type == "LOGO":
                    # TODO add removal of images if needed
                    # TODO add image error handling
                    asset_mutate_operation, asset_resource, field_type = self.googleAdsService._create_image_asset(
                        asset_url, asset_text + f" #{uuid4()}", asset_type, customer_id)
                    asset_operations[asset_group_alias].append(
                        asset_mutate_operation)

                    asset_mutate_operation = self.googleAdsService._add_asset_to_asset_group(
                        asset_resource, asset_group_id, field_type, customer_id)
                    asset_operations[asset_group_alias].append(
                        asset_mutate_operation)
                elif asset_type == "HEADLINE" or asset_type == "LONG_HEADLINE" or asset_type == "DESCRIPTION" or asset_type == "BUSINESS_NAME":
                    asset_mutate_operation, asset_resource, field_type = self.googleAdsService._create_text_asset(
                        asset_text, asset_type, customer_id)
                    asset_operations[asset_group_alias].append(
                        asset_mutate_operation)

                    asset_mutate_operation = self.googleAdsService._add_asset_to_asset_group(
                        asset_resource, asset_group_id, field_type, customer_id)
                    asset_operations[asset_group_alias].append(
                        asset_mutate_operation)
                # case "YOUTUBE_VIDEO":
                # case "CALL_TO_ACTION":

                row_to_operations_mapping[asset_resource] = index
            index += 1

        # Blob linking of assets and asset groups
        for asset_group_asset_operations in asset_operations:
            try:
                asset_group_response = self.googleAdsService._bulk_mutate(
                    asset_operations[asset_group_asset_operations], customer_id)
            except GoogleAdsException as ex:
                print(
                    f'Request with ID "{ex.request_id}" failed with status '
                    f'"{ex.error.code().name}" and includes the following errors:'
                )
                for error in ex.failure.errorss:
                    print(f'\tError with message "{error.message}".')
                    if error.location:
                        for field_path_element in error.location.field_path_elements:
                            print(
                                f"\t\tOn field: {field_path_element.field_name}")
                sys.exit(1)
            else:
                sheet_results.update(self.googleAdsService.print_results(
                    asset_group_response, asset_operations[asset_group_asset_operations], row_to_operations_mapping))

        self.sheetService.update_sheet_status(sheet_results, self.sheetService.get_sheet_id(self.sheetName, self.googleSheetId), self.googleSheetId)

cp = main()
cp.assetUpload()
