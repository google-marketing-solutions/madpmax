/**
 * Copyright 2023 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

// Configuration input values.
const includeVideo = false;
// Set to true in case provided video assets should be removed from the asset
// group.
const removeExistingVideo = false;
// Leave empty in case removeExistingVideo = false.
const placeholderYoutudeIds = ['YT_ID_1', 'YT_ID_2'];
// Set to true in case provided image assets should be removed from the asset
// group.
const removeExistingImages = false;
// Leave empty in case removeExistingImages = false.
const placeholderImageNames = ['YOUR_ASSET_1', 'YOUR_ASSET_2'];
const inputSheetUrl = 'YOUR_SPREADSHEET_URL';
const inputSheetName = 'YOUR_SHEET_NAME';
const rowLimit = 2000;


// Input column map, descripting the column names for the input data from the
// RawData sheet.
const inputColumnMap = {
  CAMPAIGN: 0,
  ASSET_GROUP: 1,
  IMAGE_URL: 2,
  YOUTUBE_ID: 3,
  STATUS: 4,
};

const assetTypes = {
  'SQUARE': 'SQUARE_MARKETING_IMAGE',
  'LANDSCAPE': 'MARKETING_IMAGE',
  'PORTRAIT': 'PORTRAIT_MARKETING_IMAGE',
  'VIDEO': 'YOUTUBE_VIDEO',
  'IMAGE': 'IMAGE',
};


/**
 * Reads the campaigns and asset groups from the input sheet, creates assets
 * for the assets provided. Removes the provided placeholder assets, and writes
 * the results back to the spreadsheet.
 */
function main() {
  // Get Values from input sheet
  const sheet = openSheetByName(inputSheetUrl, inputSheetName);
  const range = getSortedRange(sheet);
  const values = range.getValues();
  let assetGroup = null;
  let performanceMaxCampaign = null;
  let imageUrl = '';
  let youtubeId = '';
  let imagesRemoved = {};
  let videosRemoved = false;
  let [imageName, imageType] = [null, null];

  // Loop through of the input values in the provided spreadsheet / sheet.
  for (const row in values) {
    // Break loop when encounting a first empty row.
    if (values[row][inputColumnMap.CAMPAIGN] === '') {
      break;
    }

    if (values[row][inputColumnMap.STATUS] === '') {
      let status = 'SUCCESS';

      imageUrl = values[row][inputColumnMap.IMAGE_URL];
      youtubeId = values[row][inputColumnMap.YOUTUBE_ID];

      // Generate the performance max campaign object.
      if (performanceMaxCampaign === null ||
          performanceMaxCampaign.getName() !==
              values[row][inputColumnMap.CAMPAIGN]) {
        performanceMaxCampaign = getPerformanceMaxCampaignByName(
            values[row][inputColumnMap.CAMPAIGN]);
      }

      // Generate the assetGroup object for each of the unique Campaign/Asset
      // group combination. Prevent duplication of the request in case of
      // multiple asset per asset group.
      if (assetGroup === null ||
          assetGroup.getName() !== values[row][inputColumnMap.ASSET_GROUP]) {
        assetGroup = getAssetGroupByName(
            performanceMaxCampaign, values[row][inputColumnMap.ASSET_GROUP]);
        imagesRemoved.SQUARE = false;
        imagesRemoved.LANDSCAPE = false;
        videosRemoved = false;
      }

      // CONTINUE WITH THE ASSETGROUP
      if (imageUrl) {
        // Add image
        [imageName, imageType] = parseImageUrl(imageUrl);
        const image = createImageAsset(imageName, imageUrl);

        if (!image) {
          status = 'ERROR: ' +
              '404 Image not found';
        } else {
          assetGroup.addAsset(image, imageType);
        }
      }
      if (youtubeId && includeVideo) {
        let videoAsset = getVideoByYouTubeId(youtubeId);
        if (!videoAsset) {
          videoAsset = createVideoAsset(youtubeId);
        }
        assetGroup.addAsset(videoAsset, assetTypes.VIDEO);
      }

      // Check whether preview or prod-run. Only write status to sheet when
      // prod-run.
      if (!AdsApp.getExecutionInfo().isPreview()) {
        const cell = sheet.getRange(Number(row) + 2, inputColumnMap.STATUS + 1);
        cell.setValue(status);
      }

      // Check whether the placeholder assets need to be removed.
      if (imagesRemoved.LANDSCAPE === false && removeExistingImages === true &&
          imageType === assetTypes.LANDSCAPE && status == 'SUCCESS') {
        // Remove the images in case the flag is set to true. Loop through the
        // input of image names and remove asset by name.
        placeholderImageNames.forEach((element) => {
          removeImageFromAssetGroup(assetGroup, element, imageType);
        });
        imagesRemoved.LANDSCAPE = true;
      }

      // Check whether the placeholder assets need to be removed.
      if (imagesRemoved.SQUARE === false && removeExistingImages === true &&
          imageType === assetTypes.SQUARE && status == 'SUCCESS') {
        // Remove the images in case the flag is set to true. Loop through the
        // input of image names and remove asset by name.
        placeholderImageNames.forEach((element) => {
          removeImageFromAssetGroup(assetGroup, element, imageType);
        });
        imagesRemoved.SQUARE = true;
      }
      if (videosRemoved === false && removeExistingVideo === true &&
          status == 'SUCCESS') {
        // Remove the videos in case the flag is set to true. Loop through the
        // input of video ids and remove asset by youtube id.
        placeholderYoutudeIds.forEach((element) => {
          removeVideoFromAssetGroup(assetGroup, element);
        });
        videosRemoved = true;
      }

      console.log(status, imageName, imageType);
    }
  }
}


// Retrieve the assetGroup based on campaign and asset group name.
function getAssetGroupByName(performanceMaxCampaign, assetGroupName) {
  if (performanceMaxCampaign === null) {
    return null;
  }
  const assetGroupIterator =
      performanceMaxCampaign.assetGroups()
          .withCondition(`asset_group.name = "${assetGroupName}"`)
          .get();
  if (!assetGroupIterator.hasNext()) {
    throw new Error(`No asset group found with name ${assetGroupName}.`);
  }
  return assetGroupIterator.next();
}

// Retrieve the pmax campaign based on campaign name.
function getPerformanceMaxCampaignByName(campaignName) {
  const performanceMaxCampaignIterator =
      AdsApp.performanceMaxCampaigns()
          .withCondition(`campaign.name = "${campaignName}"`)
          .get();
  if (!performanceMaxCampaignIterator.hasNext()) {
    throw new Error(
        `No performance max campaign with name ${campaignName} found.`);
  }
  const performanceMaxCampaign = performanceMaxCampaignIterator.next();
  return performanceMaxCampaign;
}

// Format date input.
function formatDate(date) {
  return (date == null) ?
      'None' :
      zeroPad(date.year) + zeroPad(date.month) + zeroPad(date.day);
}

// Format date digits.
function zeroPad(number) {
  return Utilities.formatString('%02d', number);
}

// Retrieve video asset.
function getVideoByYouTubeId(youTubeVideoId) {
  // You can filter on the YouTubeVideoId if you already have that video in
  // your account to fetch the exact one you want right away.
  const videos = AdsApp.adAssets()
                     .assets()
                     .withCondition(
                         `asset.type = '${assetTypes.VIDEO}' AND ` +
                         `asset.youtube_video_asset.youtube_video_id = '${
                             youTubeVideoId}'`)
                     .get();
  if (videos.hasNext()) {
    return videos.next();
  }
  return null;
}

// Retrieve image asset.
function getImageByName(name) {
  const images = AdsApp.adAssets()
                     .assets()
                     .withCondition(
                         `asset.type = '${assetTypes.IMAGE}' AND ` +
                         `AssetName = '${name}'`)
                     .get();
  if (images.hasNext()) {
    return images.next();
  }
  return null;
}

// Retrieve the sheet.
function openSheetByName(SPREADSHEET_URL, SHEET_NAME) {
  // The code below opens a spreadsheet using its URL and logs the name for it.
  // Note that the spreadsheet is NOT physically opened on the client side.
  // It is opened on the server only (for modification by the script).

  const ss = SpreadsheetApp.openByUrl(SPREADSHEET_URL);
  const sheet = ss.getSheetByName(SHEET_NAME);

  return sheet;
}

// Retrieve the sheet range.
function getSortedRange(sheet) {
  const range =
      sheet.getRange(2, 1, sheet.getLastRow() - 1, sheet.getLastColumn());

  // Sorts ascending by column A, B, and C
  range.sort([
    {column: 1, ascending: true}, {column: 2, ascending: true},
    {column: 3, ascending: true}
  ]);

  return range;
}

// Build the video asset based on Youtube Id.
function createVideoAsset(youTubeVideoId) {
  var assetName = 'YT_pMax_' + youTubeVideoId;
  var assetOperation = AdsApp.adAssets()
                           .newYouTubeVideoAssetBuilder()
                           .withName(assetName)
                           .withYouTubeVideoId(youTubeVideoId)
                           .build();
  return assetOperation.getResult();
}

// Remove video asset from assetgroup.
function removeVideoFromAssetGroup(assetGroup, youTubeVideoId) {
  const video = getVideoByYouTubeId(youTubeVideoId);
  assetGroup.removeAsset(video, assetTypes.VIDEO);
}

// Create image asset based on image url. Or returns null.
function createImageAsset(imageName, imageUrl) {
  let imageAsset = null;
  let myRequest = null;
  
  try{
    myRequest = UrlFetchApp.fetch(imageUrl, options).getResponseCode();
  }
  catch(e){
    Logger.log(imageName, e);
  }
  
  if (myRequest === 200) {
    const imageBlob = UrlFetchApp.fetch(imageUrl).getBlob();

    const assetOperation = AdsApp.adAssets()
                               .newImageAssetBuilder()
                               .withName(imageName)
                               .withData(imageBlob)
                               .build();

    if (assetOperation.isSuccessful()) {
      imageAsset = assetOperation.getResult();
    }
  }

  return imageAsset;
}

// Remove image asset from assetgroup.
function removeImageFromAssetGroup(assetGroup, imageName, imageType) {
  const image = getImageByName(imageName);

  const dimensions = image.getDimensions();
  const width = dimensions.getWidth();
  const height = dimensions.getHeight();

  const removalImageType = getImageType(width, height);

  if (image && imageType === removalImageType) {
    assetGroup.removeAsset(image, imageType);
  }
}

// Get Asset Type based on the image URL, or the image Object e.g.
function getImageType(width, height){
  if (Math.round(width / height) === 1) {
    return assetTypes.SQUARE;
  } else if (width > height) {
    return assetTypes.LANDSCAPE;
  } else  if (height > width) {
    return assetTypes.PORTRAIT;
  }

  return null;
}

// Get the image (file)name from the URL.
// https://bstatic.com/xdata/images/hotel/600x314/330657635.jpg
// https://bstatic.com/xdata/images/hotel/square300/362132197.jpg?k=9320c9671705a519b0649eef5f1fa6ecd3e2b88f7bc94c817b07b56463d6137d&o=
// https://q-xx.bstatic.com/xdata/images/xphoto/600x314/57584488.jpeg?k=d8d4706fc72ee789d870eb6b05c0e546fd4ad85d72a3af3e30fb80ca72f0ba57&o=
// https://q-xx.bstatic.com/xdata/images/xphoto/300x300/57584488.jpeg?k=d8d4706fc72ee789d870eb6b05c0e546fd4ad85d72a3af3e30fb80ca72f0ba57&o=
// https://q-xx.bstatic.com/xdata/images/xphoto/600x314/57584488.jpeg?k=d8d4706fc72ee789d870eb6b05c0e546fd4ad85d72a3af3e30fb80ca72f0ba57&o=
function parseImageUrl(imageUrl) {
  let imageType = null;
  const imageTypeFromPath = imageUrl.match(/images\/.*?\/(.*)?\//)[1];

  if(imageTypeFromPath.includes('square')){
    imageType = assetTypes.SQUARE;
  }
  else {
    const dimensions = imageTypeFromPath.split('x');
    imageType = getImageType(dimensions[0], dimensions[1]);
  }

  const imageName = imageType + '_' +
      imageUrl.substring(imageUrl.lastIndexOf('/') + 1)
          .replace(/\.[^/.]+$/, '');
  return [imageName, imageType];
}
