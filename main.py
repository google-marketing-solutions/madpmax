from google.ads import googleads
from google.api_core import protobuf_helpers
from google.ads.googleads.errors import GoogleAdsException

import enum
import auth
import sheet_api
import ads_api
import yaml

class main():

    # Input column map, descripting the column names for the input data from the
    # RawData sheet.
    class assetsColumnMap(enum.IntEnum):
        ASSET_GROUP_ALIAS = 0,
        ASSET_TYPE = 1,
        ASSET_TEXT = 2,
        ASSET_URL = 3,
        STATUS = 4

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

        # asset_service = self._google_ads_client.get_service("AssetService")
        # all operations across multiple assetGroups where the key is an assetGroup 
        asset_operations={}
        # Loop through of the input values in the provided spreadsheet / sheet.
        for row in values:
            asset_group_alias = row[self.assetsColumnMap.ASSET_GROUP_ALIAS]
            # TODO: Retrieve AssetGroup Resource name.
            asset_group_details = self.sheetService._get_sheet_row(row[self.assetsColumnMap.ASSET_GROUP_ALIAS], "AssetGroups", self.googleSheetId)
            asset_group_id = asset_group_details[self.assetGroupsColumnMap.ASSET_GROUP_ID]
            customer_id = asset_group_details[self.assetGroupsColumnMap.CUSTOMER_ID]
            # Generate the performance max campaign object.
            # pmax_campaign_resource = self.googleAdsService._get_campaign_resource_name(self.customerId, asset_group_details[self.assetGroupsColumnMap.CAMPAIGN_ID])
            # asset_group_resource = self.googleAdsService._get_asset_group_resource_name(self.customerId, asset_group_details[self.assetGroupsColumnMap.ASSET_GROUP_ID])
            
            # TODO: Read Customer ID from INPUT SHEET VALUE
            # TODO: IMPLEMENT FUNCTIONALITY FOR LOGO AND DIFFERENT IMAGE SIZES (PORTRAIT / SQUARE). 
            # Add image to AssetGroup
            # if row[self.assetsColumnMap.ASSET_TYPE] == "IMAGE" and len(row) == 4:
            #     image_url = row[self.assetsColumnMap.ASSET_URL]
            #     self.googleAdsService._add_asset_to_asset_group(asset_group_resource, image_url, self.customerId)
            #     # TODO: WRITE RESULTS TO SPREADSHEET
            #     self.sheetService._set_cell_value(self.assetGroupsUploadStatus.COMPLETED, self.sheetName+"!E"+row, self.googleSheetId)


            # TODO: IMPLEMENT VIDEO FUNCTIONALITY. 
            #youtubeId = row[self.assetsColumnMap.ASSET_URL]
            # if row[self.assetsColumnMap.TYPE] == self.assetTypes.YOUTUBE_VIDEO:
            #     # TODO: Retrieve YT ID from YT URL row[self.assetsColumnMap.ASSET_URL]
                
            #     videoAsset = getVideoByYouTubeId(youtubeId)

            #     # Check if the video is already a Google Ads Asset, if not create the asset.
            #     if not videoAsset:
            #         videoAsset = createVideoAsset(youtubeId)

            #     assetGroup.addAsset(videoAsset, assetTypes.VIDEO)


            
            if asset_group_alias not in asset_operations:
                asset_operations[asset_group_alias] = []

            if self.assetsColumnMap.ASSET_URL.value < len(row):
                asset_url = row[self.assetsColumnMap.ASSET_URL]
            else:
                asset_url = ""

            asset_type = row[self.assetsColumnMap.ASSET_TYPE]
            # Asset name / asset type
            asset_text = row[self.assetsColumnMap.ASSET_TEXT]
            
            if asset_type == "IMAGE" or asset_type ==  "LOGO":
                #TODO add removal of images if needed 
                #TODO add check feedback for the amount of images 

                asset_mutate_operation, asset_resource, field_type = self.googleAdsService._create_image_asset(asset_url, asset_text + " #{uuid4()}", asset_type, customer_id)
                asset_operations[asset_group_alias].append(asset_mutate_operation)

                asset_mutate_operation = self.googleAdsService._add_asset_to_asset_group(asset_resource, asset_group_id, field_type, customer_id)
                asset_operations[asset_group_alias].append(asset_mutate_operation)
            elif asset_type == "HEADLINE" or asset_type ==  "LONG_HEADLINE" or asset_type ==  "DESCRIPTION" or asset_type == "BUSINESS_NAME":
                asset_mutate_operation, asset_resource, field_type = self.googleAdsService._create_text_asset(asset_text, asset_type, customer_id)
                asset_operations[asset_group_alias].append(asset_mutate_operation)

                asset_mutate_operation = self.googleAdsService._add_asset_to_asset_group(asset_resource, asset_group_id, field_type, customer_id)
                asset_operations[asset_group_alias].append(asset_mutate_operation)
               # case "YOUTUBE_VIDEO":
               # case "CALL_TO_ACTION":   

        # Blob linking of assets and asset groups 
        for asset_group_asset_operations in asset_operations:
            try:
                asset_group_response = self.googleAdsService._bulk_mutate(asset_operations[asset_group_asset_operations], customer_id)
            except GoogleAdsException as ex:
                print(
                    f'Request with ID "{ex.request_id}" failed with status '
                    f'"{ex.error.code().name}" and includes the following errors:'
                )
                for error in ex.failure.errors:
                    print(f'\tError with message "{error.message}".')
                    if error.location:
                        for field_path_element in error.location.field_path_elements:
                            print(f"\t\tOn field: {field_path_element.field_name}")
                sys.exit(1)
            else:
                self.googleAdsService.print_results(asset_group_response, asset_operations[asset_group_asset_operations])

            # TODO: WRITE RESULTS TO SPREADSHEET FROM results
            # self.sheetService._set_cell_value(self.assetGroupsUploadStatus.COMPLETED, self.sheetName+"!E"+row, self.googleSheetId)
                   

cp = main()
cp.assetUpload()