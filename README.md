# Mad PMax: PMax Asset Automation

[Performance Max (PMax)](https://support.google.com/google-ads/answer/10724817?hl=en-GB) uses the full power of Google AI to help advertisers drive conversions across Google Ads inventory. By optimizing workflows for the creation of PMax campaigns, asset groups, and asset uploads, PMax can scale even better.

Is there a solution to manage and upload PMax campaigns, asset groups and assets at scale?

Yes! Mad PMax combines the simplicity of Google Sheets with the power of Google Cloud. Just add
the details (like account name, campaign name, etc.) for your PMax campaigns, asset groups and assets into the ‘Mad PMax’ sheet, and with a single click, your changes are seamlessly uploaded to Google Ads.

![Mad Pmax Architecture](https://services.google.com/fh/files/misc/madpmax_architecture.png)

## Use Cases
* Replicate PMax campaigns at scale
* Upload PMax assets at scale
* Create asset groups for PMax at scale
* Prevent Pmax Setup errors

## Requirements
* Google Cloud Project
* Google Ads Developer Token
* Terraform deployment

## Instructions

The Mad Pmax: Performance Max Asset Automation solution can be deployed on Google Cloud through Terraform. See the steps below. This will require roughly 2-4 hours to deploy.

Use the interactive cloud tutorial to deploy the solution:

[![Open in Cloud Shell](https://gstatic.com/cloudssh/images/open-btn.png)](https://console.cloud.google.com/?cloudshell=true&cloudshell_git_repo=https://github.com/google-marketing-solutions/madpmax&cloudshell_tutorial=docs/tutorial.md)

Alternatively, you can find the [full deployment guide here](https://github.com/google-marketing-solutions/madpmax/wiki/Manual-Deployment-Guide).

## Using the tool

  Check out the full [User Guide](https://github.com/google-marketing-solutions/madpmax/wiki/User-Guide).

  In brief, you can find the **pMax Execute** menu option in the template spreadsheet with two functions:
  * **Refresh Sheet**: loads all existing in your account Campaigns, Asset Groups and Assets into related pages in the spreadsheet
  * **Upload to Google Ads**: uploads all new Campaigns, Asset Groups and Assets into your account. All errors will be shown on related pages in the last column

### Template Sheet guide

* **NewCampaigns**: creation of new Campaigns page
* **CampaignList**: page showing existing Campaigns in your account after running *pMax Execute* -> *Refresh Sheet*
* **NewAssetGroup**: creation of new Asset Group
* **AssetGroupList**: page showing existing Asset Groups in your account after running *pMax Execute* -> *Refresh Sheet*
* **Assets**: contains Assets to create and existing Assets in the account after running *pMax Execute* -> *Refresh Sheet*
* **Customer List**: list of cutomers for the application
* **Sitelinks**: page to see existing Sitelinks or create new ones

Choose customers you would like to use for the application in **Customer List**.
Use drop down menu on creation pages (NewCampaign, NewAssetGroup, Assets) to assign new Asset, Asset Group and Campaigns to the correct accounts and campaigns.

## Disclaimer
__This is not an officially supported Google product.__

Copyright 2024 Google LLC. This solution, including any related sample code or
data, is made available on an "as is", "as available", and "with all faults"
basis, solely for illustrative purposes, and without warranty or representation
of any kind. This solution is experimental, unsupported and provided solely for
your convenience. Your use of it is subject to your agreements with Google, as
applicable, and may constitute a beta feature as defined under those agreements.
To the extent that you make any data available to Google in connection with your
use of the solution, you represent and warrant that you have all necessary and
appropriate rights, consents and permissions to permit Google to use and process
that data. By using any portion of this solution, you acknowledge, assume and
accept all risks, known and unknown, associated with its usage, including with
respect to your deployment of any portion of this solution in your systems, or
usage in connection with your business, if at all.
