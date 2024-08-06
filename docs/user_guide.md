# MadPMax User Guide: Scale Your PMAX Campaigns

## Understanding pMax Execute Functions

Find the pMax execute button in the spreadsheet menu.

* **Refresh Spreadsheet**:
  * **Refresh All Sheets**: Imports all of your current information from Google Ads.
  * **Refresh Individual Tabs**: Update specific tabs (CustomerList, CampaignList, AssetGroupList) separately.
* **Upload to Google Ads**:
  * Uploads all new entries and re-tries any errors. Send any new campaigns, asset groups, or assets you've created in the sheet to Google Ads.

## Setting Up New Campaigns, Asset Groups, and Assets
> Note: You can create multiple campaigns, asset groups, and assets in bulk, before using the  “Upload to Google Ads” button.

Follow these steps for each component:

  **New Campaigns (NewCampaigns tab)**:
  1. Select the Google Ads account from the dropdown.
  2. Fill in the campaign details (name, budget, etc.).
  3. Click "Upload to Google Ads"

**New Asset Groups (NewAssetGroup tab)**:
 1. Select the account and campaign.
  Note: Pay attention to the minimum requirements for new asset groups (check column B).
 1. Enter the asset group details.
 2. Click "Upload to Google Ads"

**Assets (Assets tab)**:
 1. Select the account, campaign, and asset group.
 2. Choose the asset type (Text, Image, YouTube video, etc.).
 3. Enter the required information (Text, URLs, Call-to-action types).
 4. Click "Upload to Google Ads"
**Sitelinks**:
 1. Set up sitelinks using the same process as assets.

### Important Notes
* **Mandatory Fields**: The CustomerList tab must have at least one entry for campaigns to be created.
* **Minimum Requirements**: Be sure to meet the minimum requirements for asset groups (indicated in column B of the NewAssetGroup tab).
* **Errors**: Check the status column and the end of the row for error messages if an upload fails.
* **Do Not Modify**: Avoid modifying columns A and B, as well as the first five rows of each tab.

### Additional Tips
* Use the spreadsheet functions (drag down, copy/paste) for efficient data entry.
* For Image and YouTube assets, provide publicly accessible URLs (ideally from a CDN).
