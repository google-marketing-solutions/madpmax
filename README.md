# Performance Max (pMax) Asset Swap Automation

Mad Max is a spreadsheet based Asset management tool for Performance Max campaigns in Google Ads.

Client will fill in actions in a spreadsheet and this tool will automatically
download/upload Assets, and update your pMax assets in your campaigns.

**NOTE**: This script is _not_ compatible with the Google Ads Scripts legacy editor (version).

## Requirements
    *   Spreadsheet containing Asset details
    *   Access to Google Ads Accounts

## Configuration
1.  Make a copy of [Template sheet](https://docs.google.com/spreadsheets/d/1powA-U1aq3c2t4B5eSZ6NrthKlw45LhvYYc_GZAs4ns/copy)

2. Copy the Ads Script code

Manually copy the Code.gs file the code from the ads-scripts folder in the revelant Script editor for your MCC/CID Ads account.

Here's a link where you can locate the Script editor: https://developers.google.com/google-ads/scripts/docs/getting-started

2a. Fill in the missing details and press save in the UI
```
const includeVideo = false;
 // Set to true in case provided video assets should be removed from the asset group.
const removeExistingVideo = false;
// Leave empty in case removeExistingVideo = false.
const placeholderYoutudeIds = ["YT_ID_1", "YT_ID_2"];
 // Set to true in case provided image assets should be removed from the asset group.
const removeExistingImages = false;
// Leave empty in case removeExistingImages = false.
const placeholderImageNames = ["YOUR_ASSET_1", "YOUR_ASSET_2"];
const inputSheetUrl = "YOUR_SPREADSHEET_URL";
const inputSheetName = "YOUR_SHEET_NAME";
const rowLimit = 2000;
```


## Using the Ads Script
1. Preview the script
There's an option to preview the script in Google Ads Scripts UI.
It will log all of the changes it is going to make without actually making them.
This is good to gain understanding of the process and make sure it works as intended.
Note: it needs the newly created sheets in the master spreadsheet (step1 above)
Those sheets will be used for preview of the remaining actions.

2. Run the script
Once you're happy with the script press the run button.

3. Schedule (optionally)
If you want the script to be scheduled you can also do that too at X+2 hours.

Here's an article to help you how to achieve that: https://support.google.com/google-ads/answer/188712?hl=en
