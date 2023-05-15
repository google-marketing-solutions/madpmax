from google.ads import googleads
from google.api_core import protobuf_helpers
from google.ads.googleads.errors import GoogleAdsException
from enum import Enum

import auth
import sheet_api
import ads_api
import yaml


class main():

    # Input column map, descripting the column names for the input data from the
    # RawData sheet.
    class inputColumnMap(Enum):
        CAMPAIGN = 0,
        ASSET_GROUP = 1,
        IMAGE_URL = 2,
        YOUTUBE_ID = 3,
        STATUS = 4

    class assetTypes(Enum):
        SQUARE = "SQUARE_MARKETING_IMAGE",
        LANDSCAPE = "MARKETING_IMAGE",
        PORTRAIT = "PORTRAIT_MARKETING_IMAGE",
        VIDEO = "YOUTUBE_VIDEO",
        IMAGE = "IMAGE"

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
        self.inputSheetName = "YOUR_SHEET_NAME"
        self.inputGoogleSheetId = "YOUR_SHEET_ID"
        self.rowLimit = 2000
        
        with open('google-ads.yaml', 'r') as ymlfile:
            cfg = yaml.safe_load(ymlfile)

        credentials = auth.get_credentials_from_file(
            cfg['oauth_token'], cfg['refresh_token'], cfg['client_id'], cfg['client_secret'])

        self.sheetService = sheet_api.SheetsService(credentials)
        self.googleAdsService = ads_api.AdService("google-ads.yaml")

    def get_campain_resource(self, campaign_id=None, campaign_name=None):
        
        # TODO : Update function to return resource name.
        
        if campaign_id:
            print(self.googleAdsService._get_campaign_by_id(campaign_id, "8958116280"))
        if campaign_name:
            print(self.googleAdsService._get_campaign_by_name(campaign_name, "8958116280"))
        

    """Reads the campaigns and asset groups from the input sheet, creates assets
    for the assets provided. Removes the provided placeholder assets, and writes
    the results back to the spreadsheet."""
    def campaigns(self):
        # Get Values from input sheet
        range = self.sheetService.get_spreadsheet_values(
            self.inputSheetName+"!A:C", self.inputGoogleSheetId)
        values = range.getValues()
        assetGroup = None
        performanceMaxCampaign = None
        imageUrl = ""
        youtubeId = ""
        imagesRemoved = {}
        videosRemoved = False
        [imageName, imageType] = [None, None]

        # Loop through of the input values in the provided spreadsheet / sheet.
        for row in values:
            # Break loop when encounting a first empty row.
            while values[row][self.inputColumnMap.CAMPAIGN] != "":
                if values[row][self.inputColumnMap.STATUS] == "":
                    status = "SUCCESS"

                imageUrl = values[row][self.inputColumnMap.IMAGE_URL]
                youtubeId = values[row][self.inputColumnMap.YOUTUBE_ID]

                # Generate the performance max campaign object.
                if performanceMaxCampaign == None or performanceMaxCampaign.getName() != values[row][self.inputColumnMap.CAMPAIGN]:
                    performanceMaxCampaign = getPerformanceMaxCampaignByName(
                        values[row][inputColumnMap.CAMPAIGN])

                # Generate the assetGroup object for each of the unique Campaign/Asset
                # group combination. Prevent duplication of the request in case of
                # multiple asset per asset group.
                if (assetGroup == null or
                    assetGroup.getName() != values[row][inputColumnMap.ASSET_GROUP]):
                    # TODO: add the getAssetGroupByName function
                    assetGroup = getAssetGroupByName(
                    performanceMaxCampaign,
                    values[row][inputColumnMap.ASSET_GROUP]
                    )
                    imagesRemoved.SQUARE = False
                    imagesRemoved.LANDSCAPE = False
                    videosRemoved = False

                # CONTINUE WITH THE ASSETGROUP
                if imageUrl:
                    # Add image
                    [imageName, imageType] = parseImageUrl(imageUrl)
                    image = createImageAsset(imageName, imageUrl)

                    if not image:
                        status = "ERROR: " + "404 Image not found"
                    else:
                        assetGroup.addAsset(image, imageType)

                if youtubeId and includeVideo:
                    videoAsset = getVideoByYouTubeId(youtubeId)

                    if not videoAsset:
                        videoAsset = createVideoAsset(youtubeId)

                    assetGroup.addAsset(videoAsset, assetTypes.VIDEO)

                # Check whether preview or prod-run. Only write status to sheet when prod-run.
                if  not AdsApp.getExecutionInfo().isPreview():
                    cell = sheet.getRange(Number(row) + 2, inputColumnMap.STATUS + 1)
                    cell.setValue(status)

                # Check whether the placeholder assets need to be removed.
                if imagesRemoved.LANDSCAPE == False and removeExistingImages == true and imageType == assetTypes.LANDSCAPE and status == "SUCCESS":
                    # Remove the images in case the flag is set to true. Loop through the
                    # input of image names and remove asset by name.
                    # TODO REPLACE FUNCTION BELOW TO REMOVE IMAGES
                    #placeholderImageNames.forEach((element)=> {
                    #removeImageFromAssetGroup(assetGroup, element, imageType); })
                    imagesRemoved.LANDSCAPE = True

                # Check whether the placeholder assets need to be removed.
                if imagesRemoved.SQUARE == False and removeExistingImages == True and imageType == assetTypes.SQUARE and status == "SUCCESS":
                    # Remove the images in case the flag is set to true. Loop through the
                    # input of image names and remove asset by name.
                    # TODO REPLACE FUNCTION BELOW TO REMOVE IMAGES
                    # placeholderImageNames.forEach((element)=> {
                    # removeImageFromAssetGroup(assetGroup, element, imageType); })
                    imagesRemoved.SQUARE = True
                if videosRemoved == False and removeExistingVideo == True and status == "SUCCESS":
                    """ Remove the videos in case the flag is set to true. Loop through the
                    input of video ids and remove asset by youtube id."""
                    # TODO REPLACE FUNCTION BELOW TO REMOVE VIDEOS
                    # placeholderYoutudeIds.forEach((element)=> {
                    # removeVideoFromAssetGroup(assetGroup, element); })
                    videosRemoved = True

                console.log(status, imageName, imageType)

cp = main()
cp.get_campain_resource(campaign_id="19646273945")
cp.get_campain_resource(campaign_name="Performance Max campaign #dc35d162-782e-4531-8582-fb014e9bcf37")