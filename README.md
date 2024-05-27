# Mad PMax: PMax Asset Automation

## Instructions

The Performance Max Asset Automation solution can be deployed on Google Cloud through Terraform. See the steps below. This will require roughly 2-4 hours to deploy.

1. ### Access the repository

    Check that you have access to the [solutions_pmax_asset_automation-readers](https://groups.google.com/a/professional-services.goog/g/Solutions_pmax_asset_automation-readers) Google group (with your company email address). This is necessary to clone the project repository into your Google Cloud Project (you should have Project Owner or Project Editor permissions).  If you don’t have access or you are not sure, contact your Google representatives or email <mad-pmax@google.com>

2. ### Make a copy of [Template sheet](https://docs.google.com/spreadsheets/d/1TBzqzp6dvlNGRjsuFlfBbErBC_BSHlzQPzRcBahxn-Q/copy)

     See usage instructions in the [Template Sheet Guide](#template-sheet-guide) section.

3. ### Create a new or Select an existing Google Cloud Project

      Select an **existing Cloud Project** to deploy the solution, or follow the next steps to **create a new cloud project**.

      1. Navigate to [Create a Project](https://console.cloud.google.com/projectcreate) in Google Cloud Console.
      2. In the **Project Name** field, enter a descriptive name for your project.
      3. When deploying within a Cloud organisation, you will need to select the **Billing account** and the **Organisation** to deploy your new project.
      4. In the **Location** field, click Browse to display potential locations for your project.
      5. Click **Create**.

4. ### Enable the following APIs

      Navigate to the [API Library](https://console.cloud.google.com/apis/library) and enable the following APIs

      * [Google Drive API](https://console.cloud.google.com/apis/library/drive.googleapis.com)
      * [Google Sheets API](https://console.cloud.google.com/apis/library/sheets.googleapis.com)
      * [Google Ads API](https://console.cloud.google.com/apis/library/googleads.googleapis.com)
      * [Compute Engine API](https://console.cloud.google.com/apis/library/compute.googleapis.com)
      * [Identity and Access Management (IAM) API](https://console.cloud.google.com/apis/library/iam.googleapis.com)
      * [Cloud Resource Manager API](https://console.cloud.google.com/apis/library/cloudresourcemanager.googleapis.com)
      * [Service Usage API](https://console.cloud.google.com/apis/library/serviceusage.googleapis.com)
      * [Cloud Pub/Sub API](https://console.cloud.google.com/apis/library/pubsub.googleapis.com)

5. ### Generate OAuth Credentials

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
    6. [**pmax-trigger**] Navigate to the Apps Script Code Editor, and copy values for the **Client ID** and **Client Secret** to the respective variables in the `Config.gs` file.
    7. [**pmax-api**] Generate access and refresh token:

        [Follow these steps](https://developers.google.com/google-ads/api/docs/oauth/playground#generate_tokens) to generate OAuth tokens. Make sure to include the following scopes when generating the tokens:
        * <https://www.googleapis.com/auth/drive>
        * <https://www.googleapis.com/auth/spreadsheets>
        * <https://www.googleapis.com/auth/adwords>

        **Important**: Make sure to use the **Client ID** and **Client Secret** generated in step 4 for [pmax-api] to generate the tokens.

6. ### Terraform Deployment

    1. Open the cloud project where you want to deploy the solution and open the [Cloud Editor](https://shell.cloud.google.com/?show=ide%2Cterminal). Make sure to select the project where you want to deploy the solution using `gcloud config set project [PROJECT_ID]`
    2. Create a cookie for the Git client to use by visiting <https://professional-services.googlesource.com/new-password> and following the instructions.
    3. In the terminal, run

        ```bash
        git clone https://professional-services.googlesource.com/solutions/pmax_asset_automation
        ```

    4. Run

        ```bash
        cd pmax_asset_automation/terraform
        ```

    5. Open `/terraform/configuration-input.tfvars` file and complete all required input variables in the `configuration-input.tfvars` file.

    6. Run

        ```bash
        terraform init
        ```

    7. Run

        ```bash
        terraform plan -var-file="configuration-input.tfvars"
        ```

    8. Run

        ```bash
        terraform apply -var-file="configuration-input.tfvars"
        ```

    9. Wait for terraform to deploy the solution.

    10. In case you want to **delete** the service, run

        ```bash
        terraform destroy -var-file="configuration-input.tfvars"
        ```

    **Note**: To obtain Google Ads Developer token refer to Apply for access to the Google Ads API.

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

```text
## Disclaimer
Copyright 2023 Google LLC. This solution, including any related sample code or data, is made available on an “as is,” “as available,” and “with all faults” basis, solely for illustrative purposes, and without warranty or representation of any kind. This solution is experimental, unsupported and provided solely for your convenience. Your use of it is subject to your agreements with Google, as applicable, and may constitute a beta feature as defined under those agreements. To the extent that you make any data available to Google in connection with your use of the solution, you represent and warrant that you have all necessary and appropriate rights, consents and permissions to permit Google to use and process that data. By using any portion of this solution, you acknowledge, assume and accept all risks, known and unknown, associated with its usage, including with respect to your deployment of any portion of this solution in your systems, or usage in connection with your business, if at all.
```
