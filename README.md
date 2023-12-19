# Mad PMax : Asset Automation

## Instructions
Performance Max Campaign Manager can be deployed on Google Cloud through Terraform. See the steps below. This will require roughly 2-4 hours to deploy.

1.  Make a copy of [Template sheet](https://docs.google.com/spreadsheets/d/16Gn5ImKQqf7p0tNUVtciJLWCCxC6etN1H9RIdzqlHxE/copy)

2.  ### Create a new or Select an existing Google Cloud Project
    *   Select an existing Cloud Project to deploy the solution, or follow the next steps to create a new cloud project.
        1.  In the Google Cloud console, go to Menu menu > IAM & Admin > Create a Project. Go to Create a Project.
        2.  In the Project Name field, enter a descriptive name for your project. ...
        3.  In the Location field, click Browse to display potential locations for your project. ...
        4.  Click Create.

3.  ### Create OAuth Credentials
    To obtain client_id and client_secret generate OAuth2 Credentials for Web Application. 2 Seperate Credentials are required 1) for pMax API access permissions (pmax-api) and 2) for permissions to trigger the application to run (pmax-trigger).
    
    If you haven’t configured consent screen, setup consent screen first under “oauth consent screen”
        *   User Type: “Internal”
        *   Add following "scopes": 
            Google Ads API, Google Drive API, Google Sheets API, Cloud Pub/Sub API


    1.  Open [Cloud credentials](https://console.developers.google.com/apis/credentials)
    2.  Create credentials -> Create 'OAuth client ID' -> Web Application
    3.  Add the follwing 'Authorized redirect URIs' : 
        *   [**pmax-trigger**] 'https://script.google.com/macros/d/*YOUR_APP_SCRIPT_PROJECT_ID*/usercallback' 

         Obtain your App Script ID by navigating to Your Copy of the Spreadsheet *"Template > Extensions > Apps Script"*. The Apps Script editor will open in a new tab. Navigate on the left hand side to Project Settings and copy the Project ID.
        *   [**pmax-api**] 'https://developers.google.com/oauthplayground'
    4.  Copy the Client ID and Client Secret and store safely for use later in the configuration.
    5.  [**pmax-trigger**] Navigate to the Apps Script Code Editor, and copy values for the Client ID and Client Secret to the respective variables in the Service.gs file.
    6.  [**pmax-api**] Generate access and refresh token:
        Generate access and refresh token:
        Follow the steps in the following link to generate OAuth tokens, https://developers.google.com/google-ads/api/docs/oauth/playground#generate_tokens. Make sure to include the following scopes when generating the tokens:
        *   https://www.googleapis.com/auth/drive
        *   https://www.googleapis.com/auth/spreadsheets
        *   https://www.googleapis.com/auth/adwords

        **Important** Make sure to use the Client ID and Client Secret generated in step 4 for [pmax-api] to generate the tokens. 
    
    
4.  ### Terraform Deployment
    a. Open the cloud project where you want to deploy the solution and open the Cloud Editor.
    b. In the terminal, run ```git clone https://professional-services.googlesource.com/solutions/pmax_asset_automation```
    c. Run ```cd pmax_asset_automation/terraform```

    d. Open /terraform/configuration-input.tfvars file and complete all required input variables in the configuration-input.tfvars file.

    e. Run ```terraform init```
    f. Run ```terraform plan -var-file="configuration-input.tfvars"```
    g. Run ```terraform apply -var-file="configuration-input.tfvars"```
    h. Wait for terraform to deploy the solution.
    i. In case you want to delete the service, run ```terraform destroy -var-file="configuration-input.tfvars"```
 
    Note: To optain Google Ads Developer token refer to Apply for access to the Google Ads API.

5.  ### Using the tool
    Template spreadsheet contains *pMax Execute* menu option with two functions:
    * **Refresh Sheet** - loads all exisitng in your account Camapigns, Asset Groups and Assets into related pages in the spreadsheet
    * **Upload to Google ads** - uploads all new Campaigns, Asset Groups and Assets into your account. All errors will be shown on related pages in the last column 

    ### *Pages:*

    - **NewCampaigns** - creation of new Camapigns page
    - **CampaignList** - page showing exisitng Campaigns in your account after running *pMax Execute* -> *Refresh Sheet* 
    - **NewAssetGroup** - creation of new Asset Group
    - **AssetGroupList** - page showing exisitng Asset Groups in your account after running *pMax Execute* -> *Refresh Sheet* 
    - **Assets** - contains Assets to create and exisitng Assets in the account after running *pMax Execute* -> *Refresh Sheet* 

```

## Disclaimer
Copyright 2023 Google LLC. This solution, including any related sample code or data, is made available on an “as is,” “as available,” and “with all faults” basis, solely for illustrative purposes, and without warranty or representation of any kind. This solution is experimental, unsupported and provided solely for your convenience. Your use of it is subject to your agreements with Google, as applicable, and may constitute a beta feature as defined under those agreements. To the extent that you make any data available to Google in connection with your use of the solution, you represent and warrant that you have all necessary and appropriate rights, consents and permissions to permit Google to use and process that data. By using any portion of this solution, you acknowledge, assume and accept all risks, known and unknown, associated with its usage, including with respect to your deployment of any portion of this solution in your systems, or usage in connection with your business, if at all.