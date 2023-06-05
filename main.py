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

    def __init__(self):
        # Configuration input values.
        self.includeVideo = False
        # Set to true in case provided video assets should be removed from the asset group.
        self.removeExistingVideo = False
        # Leave empty in case removeExistingVideo = false.
        self.placeholderYoutudeIds = ["YT_ID_1", "YT_ID_2"]
        # Set to true in case provided image assets should be removed from the asset
        # group.
        self.removeExistingImages = False;
        # Leave empty in case removeExistingImages = false.
        self.placeholderImageNames = ["YOUR_ASSET_1", "YOUR_ASSET_2"]
        self.sheetName = "Assets"
        # Sample spreadsheet https://docs.google.com/spreadsheets/d/16Gn5ImKQqf7p0tNUVtciJLWCCxC6etN1H9RIdzqlHxE/edit#gid=755896892
        self.googleSheetId = "REPLACE_WITH_SPREADSHEET_ID"
        self.customerId = "REPLACE_WITH_GOOGLE_ADS_CUSTOMER_ID"
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

        # Loop through of the input values in the provided spreadsheet / sheet.
        for row in values:
            # TODO: Retrieve AssetGroup Resource name.
            asset_group_details = self.sheetService._get_sheet_row(row[self.assetsColumnMap.ASSET_GROUP_ALIAS], "AssetGroups", self.googleSheetId)

            # Generate the performance max campaign object.
            pmax_campaign_resource = self.googleAdsService._get_campaign_resource_name(self.customerId, asset_group_details[self.assetGroupsColumnMap.CAMPAIGN_ID])
            
            # TODO: Read Customer ID from INPUT SHEET VALUE
            # TODO: IMPLEMENT FUNCTIONALITY FOR LOGO AND DIFFERENT IMAGE SIZES (PORTRAIT / SQUARE). 
            # Add image to AssetGroup
            if row[self.assetsColumnMap.ASSET_TYPE] == "IMAGE" and len(row) == 4:
                asset_group_resource = self.googleAdsService._get_asset_group_resource_name(self.customerId, asset_group_details[self.assetGroupsColumnMap.ASSET_GROUP_ID])
                image_url = row[self.assetsColumnMap.ASSET_URL]
                self.googleAdsService._add_asset_to_asset_group(asset_group_resource, image_url, self.customerId)
                # TODO: WRITE RESULTS TO SPREADSHEET


            # TODO: IMPLEMENT VIDEO FUNCTIONALITY. 
            #youtubeId = row[self.assetsColumnMap.ASSET_URL]
            # if row[self.assetsColumnMap.TYPE] == self.assetTypes.YOUTUBE_VIDEO:
            #     # TODO: Retrieve YT ID from YT URL row[self.assetsColumnMap.ASSET_URL]
                
            #     videoAsset = getVideoByYouTubeId(youtubeId)

            #     # Check if the video is already a Google Ads Asset, if not create the asset.
            #     if not videoAsset:
            #         videoAsset = createVideoAsset(youtubeId)

            #     assetGroup.addAsset(videoAsset, assetTypes.VIDEO)

cp = main()
cp.assetUpload()