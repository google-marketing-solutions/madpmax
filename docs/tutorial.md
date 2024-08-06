# Deploying Mad PMax

<walkthrough-metadata>
  <meta name="title" content="Deploying Mad PMax" />
  <meta name="description" content="A step by step guide on configuring cloud and deploying the solution." />
</walkthrough-metadata>

## Introduction

In this walkthrough, you'll generate OAuth credentials in preparation for the deployment of Mad PMax.

<walkthrough-tutorial-difficulty difficulty="2"></walkthrough-tutorial-difficulty>
<walkthrough-tutorial-duration duration="20"></walkthrough-tutorial-duration>

## Join Google Group to access Spreadsheet template

1. Use [this link](https://groups.google.com/g/mad-pmax-users) to access the Mad Pmax users group URL and click on "Join Group"

   ![join_group](https://services.google.com/fh/files/misc/join_mad_pmax_group.png)

1. Make a copy of the [Mad PMax Spreadsheet template](https://docs.google.com/spreadsheets/d/1uj1IA7Bf8W5av2h1Mw_WEAyhiWa6Rxu9KbFxKXW3v2k/copy)

Note: You can check usage instructions in the [User Guide page](https://github.com/google-marketing-solutions/madpmax/wiki/User-Guide).

## Google Cloud Project Setup

GCP organizes resources into projects. This allows you to
collect all of the related resources for a single application in one place.

Begin by creating a new project or selecting an existing project for this
solution.

<walkthrough-project-setup billing></walkthrough-project-setup>

For details, see
[Creating a project](https://cloud.google.com/resource-manager/docs/creating-managing-projects#creating_a_project).

### Enable Google Cloud APIs

Enable the APIs necessary to run the Mad PMax solution so that they're incorporated in the credentials you will generate in the next step.

<walkthrough-enable-apis apis="drive.googleapis.com,sheets.googleapis.com,googleads.googleapis.com,compute.googleapis.com,iam.googleapis.com,cloudresourcemanager.googleapis.com,serviceusage.googleapis.com,pubsub.googleapis.com">
</walkthrough-enable-apis>


## Switch Off Ephemeral Mode

First, let's switch off your shell's ephemeral mode.

Click <walkthrough-spotlight-pointer spotlightId="cloud-shell-more-button" target="cloudshell" title="Show me where">**More**</walkthrough-spotlight-pointer> and look for the `Ephemeral Mode` option. If it is turned on turn it off. This allows the Mad PMax code to persist across sessions.

## Authorize shell scripts commands

Copy the following command into the shell, press enter and follow the instructions:
```bash
cd
git clone https://github.com/google-marketing-solutions/madpmax.git
cd madpmax
gcloud auth login
```


## Configure OAuth Consent Screen

An authorization token is needed for the dashboard to communicate with Google Ads.

1.  Go to the **APIs & Services > OAuth consent screen** page in the Cloud
    Console. You can use the button below to find the section.

    <walkthrough-menu-navigation sectionId="API_SECTION;metropolis_api_consent"></walkthrough-menu-navigation>

1.  Choose the correct user type for your application.

    *   If you have an organization for your application, select **Internal**.
    *   If you don't have an organization configured for your application,
        select **External**.

1.  Click
    <walkthrough-spotlight-pointer cssSelector="button[type='submit']">**Create**</walkthrough-spotlight-pointer>
    to continue.

1.  Under *App information*, enter the **Application name** you want to display.
    You can copy the name below and enter it as the application name.

    ```
    MadPmax
    ```

1.  For the **Support email** dropdown menu, select the email address you want
    to display as a public contact. This email address must be your email
    address, or a Google Group you own.
2.  Under **Developer contact information**, enter a valid email address.

Click
    <walkthrough-spotlight-pointer cssSelector=".cfc-stepper-step-continue-button">**Save
    and continue**</walkthrough-spotlight-pointer>.

## Add Sensitive Scopes to Consent Screen

Scope the consent screen for Google Sheets API, Drive API, PubSub API and Google Ads API.

1. Click <walkthrough-spotlight-pointer locator="semantic({button 'Add or remove scopes'})">Add or remove scopes</walkthrough-spotlight-pointer>
1. Now in <walkthrough-spotlight-pointer locator="semantic({combobox 'Filter'})">Enter property name or value</walkthrough-spotlight-pointer> search for **Google Ads API**, check the box for the first option to choose it.
1. Do the same for
   * **Google Drive API** (select the `drive.readonly` option)
   * **Google Sheets API**
   * **Cloud Pub/Sub API**.
1. Click <walkthrough-spotlight-pointer locator="text('Update')">Update</walkthrough-spotlight-pointer>

## Creating OAuth Credentials

Create the credentials that are needed to generate a refresh token.

Make sure to **copy each of the credentials you create**, you will need them later.

1.  On the APIs & Services page, click the
    <walkthrough-spotlight-pointer cssSelector="#cfctest-section-nav-item-metropolis_api_credentials">**Credentials**</walkthrough-spotlight-pointer>
    tab.

1.  On the
    <walkthrough-spotlight-pointer cssSelector="[id$=action-bar-create-button]" validationPath="/apis/credentials">**Create
    credentials**</walkthrough-spotlight-pointer> drop-down list, select **OAuth
    client ID**.
1.  Under
    <walkthrough-spotlight-pointer cssSelector="[formcontrolname='typeControl']">**Application
    type**</walkthrough-spotlight-pointer>, select **Web application**.

1.  Add a
    <walkthrough-spotlight-pointer cssSelector="[formcontrolname='displayName']">**Name**</walkthrough-spotlight-pointer>
    for your OAuth client ID.

1. Click <walkthrough-spotlight-pointer locator="semantic({group 'Authorized redirect URIs'} {button 'Add URI'})">Authorized redirect URI</walkthrough-spotlight-pointer>
   and copy the following:
   ```
   https://developers.google.com/oauthplayground
   ```
1. Add a redirect URI fro your spreadsheet as well. Obtain your `Script ID` by navigating to your copy of the Template Spreadsheet. In the top menu, select "Extensions > Apps Script". The Apps Script editor will open in a new tab. Navigate on the left hand side to Project Settings and copy the Script ID.
   ```
   https://script.google.com/macros/d/<YOUR_APPS_SCRIPT_SCRIPT_ID>/usercallback
   ```
   ![App Script ID](https://services.google.com/fh/files/misc/madpmax_appscript_script_id.png)

1.  Click **Create**. Your OAuth client ID and client secret are generated and
    displayed on the OAuth client window.

After generating the client_id and client_secret keep the confirmation screen open and go to the next step.


## Generate Refresh Token

1. Go to the [OAuth2 Playground](https://developers.google.com/oauthplayground/#step1&scopes=https%3A//www.googleapis.com/auth/adwords,https%3A//www.googleapis.com/auth/drive,https%3A//www.googleapis.com/auth/spreadsheets&content_type=application/json&http_method=GET&useDefaultOauthCred=checked&oauthEndpointSelect=Google&oauthAuthEndpointValue=https%3A//accounts.google.com/o/oauth2/v2/auth&oauthTokenEndpointValue=https%3A//oauth2.googleapis.com/token&includeCredentials=unchecked&accessTokenType=bearer&autoRefreshToken=unchecked&accessType=offline&forceAprovalPrompt=checked&response_type=code) (opens in a new window)
2. On the right-hand pane, paste the `client_id` and `client_secret` in the appropriate fields ![paste credentials](https://services.google.com/fh/files/misc/pplayground_fields.png)
3. Then on the left hand side of the screen, click the blue **Authorize APIs** button ![Authorize APIs](https://services.google.com/fh/files/misc/authorize_sheets_ads_drive_apis.png)

   If you are prompted to authorize access, please choose your Google account that has access to Google Ads and approve.

5. Now, click the new blue button **Exchange authorization code for tokens** ![Exchange authorization code for tokens](https://services.google.com/fh/files/misc/exchange_authorization_code_for_token.png)

6. Finally, in the middle of the screen you'll see your refresh token on the last line.  Copy it and save it for future reference.  ![refresh_token](https://services.google.com/fh/files/misc/refresh_token.png) *Do not copy the quotation marks*


## Deploy Solution

Run the following command:

```bash
cd terraform
```
Open the `/terraform/configuration-input.tfvars` file and complete the required input variables
<walkthrough-editor-open-file filePath="madpmax/terraform/configuration-input.tfvars">Open
configuration-input.tfvars</walkthrough-editor-open-file>

Run the following command:

```bash
terraform init
```
With the providers downloaded and a project set, you're ready to use Terraform.
Go ahead!

```bash
terraform apply -var-file="configuration-input.tfvars"
```
Terraform will show you what it plans to do, and prompt you to accept. Type "yes" to accept the plan.

Terraform will now take some time to deploy the solution for you with the configuration specified in the configuration-input.tfvars file. Terraform will keep a state in this cloud shell environment, so if you update/change the configuration settings and run terrafom apply command again it will update all resources accordingly.

If you want to remove the deployed resources from Google Cloud Platform again you can run the following command.

```bash
terraform destroy -var-file="configuration-input.tfvars"
```
**Note**: To obtain Google Ads Developer token refer to [Apply for access to the Google Ads API](https://developers.google.com/google-ads/api/docs/get-started/dev-token#apply-token).

## Link your copy of the Template Sheet to the Google Cloud Project
1. Open the **Extensions** menu in your Template Sheet and click on **Apps Script**.
2. Navigate to the Apps Script Code Editor, and copy values for the **Client ID** and **Client Secret** to the respective variables in the `Config.gs` file. Then, find your **Google Cloud Project Name** from the Project Info section of your [Google Cloud Project Dashboard](https://console.cloud.google.com/home/dashboard) and copy its value to the respective variable in the same file.
3. Find the cog wheel icon, titled as **Project Settings**, on the left side of the screen and click on it.
4. Scroll down to the **Google Cloud Platform (GCP) Project** section and click on the button titled as **Change Project**.
![App script GCP Project number](https://services.google.com/fh/files/misc/madpmax_appscript_cloud_project.png)
1. In another tab of your browser, navigate to the Project Info section of your [Google Cloud Project Dashboard](https://console.cloud.google.com/home/dashboard) and copy the value for the **Project Number**.
2. Copy this value into your Template Sheet and click on the button titled as **Set Project** to complete the process.

## Conclusion

Congratulations. You've set up Mad PMax! How to use it? Check out the [User Guide](https://github.com/google-marketing-solutions/madpmax/wiki/User-Guide)

<walkthrough-conclusion-trophy></walkthrough-conclusion-trophy>

<walkthrough-inline-feedback></walkthrough-inline-feedback>
