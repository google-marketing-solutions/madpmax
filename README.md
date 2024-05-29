# Mad PMax: PMax Asset Automation

## Instructions

The Mad Pmax: Performance Max Asset Automation solution can be deployed on Google Cloud through Terraform. See the steps below. This will require roughly 2-4 hours to deploy.

1. ### Make a copy of the [Mad pMax Template sheet](https://docs.google.com/spreadsheets/d/1uj1IA7Bf8W5av2h1Mw_WEAyhiWa6Rxu9KbFxKXW3v2k/copy)

     See usage instructions in the [Template Sheet Guide](#template-sheet-guide) section.

2. ### Create a new or Select an existing Google Cloud Project

      Select an **existing Cloud Project** to deploy the solution, or follow the next steps to **create a new cloud project**.

      1. Navigate to [Create a Project](https://console.cloud.google.com/projectcreate) in Google Cloud Console.
      2. In the **Project Name** field, enter a descriptive name for your project.
      3. When deploying within a Cloud organisation, you will need to select the **Billing account** and the **Organisation** to deploy your new project. If billing is not correctly set up you won't be able to enable the Compute Engine API below.
      4. In the **Location** field, click Browse to display potential locations for your project.
      5. Click **Create**.

3. ### Enable the following APIs

      Navigate to the [API Library](https://console.cloud.google.com/apis/library) and enable the following APIs either by searching them by name or by directly clicking on the links below and click on the **Enable** button:

      * [Google Drive API](https://console.cloud.google.com/apis/library/drive.googleapis.com)
      * [Google Sheets API](https://console.cloud.google.com/apis/library/sheets.googleapis.com)
      * [Google Ads API](https://console.cloud.google.com/apis/library/googleads.googleapis.com)
      * [Compute Engine API](https://console.cloud.google.com/apis/library/compute.googleapis.com)
      * [Identity and Access Management (IAM) API](https://console.cloud.google.com/apis/library/iam.googleapis.com)
      * [Cloud Resource Manager API](https://console.cloud.google.com/apis/library/cloudresourcemanager.googleapis.com)
      * [Service Usage API](https://console.cloud.google.com/apis/library/serviceusage.googleapis.com)
      * [Cloud Pub/Sub API](https://console.cloud.google.com/apis/library/pubsub.googleapis.com)

4. ### Generate OAuth Credentials

    The Credentials are required 1) for pMax API access permissions (pmax-api) and 2) for permissions to trigger the application to run (pmax-trigger).

    1. Navigate to the [Credentials](https://console.developers.google.com/apis/credentials) page
    2. If you haven’t configured a Consent Screen, configure a new [OAuth Consent Screen](https://console.cloud.google.com/apis/credentials/consent)
        * User Type: “Internal”
        * Add following "scopes":
            Google Ads API (.../auth/adwords), Google Drive API (.../auth/drive.readonly), Google Sheets API (.../auth/spreadsheets), Cloud Pub/Sub API (.../auth/pubsub)
    3. [Create 'OAuth client ID'](https://console.cloud.google.com/apis/credentials/oauthclient) with Application Type: 'Web application'
    4. Add the following 'Authorized redirect URIs' :
        * [**pmax-trigger**] `'https://script.google.com/macros/d/<YOUR_APPS_SCRIPT_SCRIPT_ID>/usercallback'`
         Obtain your **Script ID** by navigating to Your Copy of the Template Spreadsheet. In the top menu, select *"Extensions > Apps Script"*. The Apps Script editor will open in a new tab. Navigate on the left hand side to *Project Settings* and copy the **Script ID**.
        * [**pmax-api**] `'https://developers.google.com/oauthplayground'`
    5. Copy the **Client ID** and **Client Secret** and store safely for use later in the configuration.
    6. [**pmax-trigger**] Navigate to the Apps Script Code Editor, and copy values for the **Client ID** and **Client Secret** to the respective variables in the `Config.gs` file. Then, find your **Google Cloud Project Name** from the Project Info section of your [Google Cloud Project Dashboard](https://console.cloud.google.com/home/dashboard) and copy its value to the respective variable in the same file.
    7. [**pmax-api**] Generate access and refresh token:

        [Follow these steps](https://developers.google.com/google-ads/api/docs/oauth/playground#generate_tokens) to generate OAuth tokens. Make sure to include the following scopes when generating the tokens:
        * <https://www.googleapis.com/auth/drive>
        * <https://www.googleapis.com/auth/spreadsheets>
        * <https://www.googleapis.com/auth/adwords>

        **Important**: Make sure to use the **Client ID** and **Client Secret** generated in step 4 for [pmax-api] to generate the tokens.

5. ### Terraform Deployment

    1. Open the cloud project where you want to deploy the solution and open the [Cloud Editor](https://shell.cloud.google.com/?show=ide%2Cterminal). Make sure to select the project where you want to deploy the solution using `gcloud config set project [PROJECT_ID]`

    2. In the terminal, run

        ```bash
        git clone https://github.com/google-marketing-solutions/madpmax.git
        ```

    3. Run

        ```bash
        cd pmax_asset_automation/terraform
        ```

    4. Open `/terraform/configuration-input.tfvars` file and complete all required input variables in the `configuration-input.tfvars` file.

    5. Run

        ```bash
        terraform init
        ```

    6. Run

        ```bash
        terraform plan -var-file="configuration-input.tfvars"
        ```

    7. Run

        ```bash
        terraform apply -var-file="configuration-input.tfvars"
        ```

    8. Wait for terraform to deploy the solution.

    9. In case you want to **delete** the service, run

        ```bash
        terraform destroy -var-file="configuration-input.tfvars"
        ```

    **Note**: To obtain Google Ads Developer token refer to Apply for access to the Google Ads API.

6. ### Link your copy of the Template Sheet to the Google Cloud Project

    1. Open the **Extensions** menu in your Template Sheet and click on **Apps Script**.
    2. Find the cog wheel icon, titled as **Project Settings**, on the left side of the screen and click on it.
    3. Scroll down to the **Google Cloud Platform (GCP) Project** section and click on the button titled as **Change Project**.
    4. In another tab of your browser, navigate to the Project Info section of your [Google Cloud Project Dashboard](https://console.cloud.google.com/home/dashboard) and copy the value for the **Project Number**.
    5. Copy this value into your Template Sheet and click on the button titled as **Set Project** to complete the process.

7. ### Using the tool

    Template spreadsheet contains *pMax Execute* menu option with two functions:
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
