import base64
import auth
from cloudevents.http import CloudEvent
import functions_framework
import yaml

# Configuration Variables, global variables with constant values. 
# Can be changed in parralel to the same changes to the spreadsheet sheet names.
_ASSET_SHEET_NAME = "Assets"

class pmaxCampaignManager:
    """Class to perform pMax API operations.

    This class contains the main logic to execute pMax campaign operations
    on the Google Ads API. Including Campaign, Asset Group and Asset creation.

    Attributes:
    credentials: An OAuth Credentials object for the authenticated user.
    google_spreadsheet_id: The Google spreadsheet ID powering the application.
    google_customer_id: The relevant Google Ads Customer ID.
    """

    def __init__(self, cfg):
        """Initializes an instance of pmaxCampaignManager.

        Args:
        cfg: Object containing the configuration variables for the application/authentication.
        """

        # Generate API credentials.
        self.credentials = auth.get_credentials(
            cfg["token"], cfg["refresh_token"], cfg["client_id"], cfg["client_secret"])

        # Configuration input values.
        self.google_spreadsheet_id = cfg["spreadsheet_id"]
        self.google_customer_id = cfg["customer_id"]

    def refresh_spreadsheet(self):
        """Method to retrieve existing campaigns, asset groups & assets.
        """
        # PLACEHOLDER
        print("Refresh Placeholder")

    def upload_to_google_Ads(self):
        """Method to upload campaigns, asset groups & assets to Google Ads.
        """
        # PLACEHOLDER
        print("Upload Placeholder")


@functions_framework.cloud_event
def pub_sub_entry(cloud_event: CloudEvent) -> None:
    """Listener method for PubSub Events.

    Args:
    cloud_event: Message Object containing the PubSub Request details from the Function Trigger.
    """

    if cloud_event:
        # Print out the data from Pub/Sub, to prove that it worked
        message_data = base64.b64decode(
            cloud_event.data["message"]["data"]).decode()

        print(f"------- START {message_data} EXECUTION -------")

        # Retrieve configuration values from config.yaml.
        with open("config.yaml", "r") as ymlfile:
            cfg = yaml.safe_load(ymlfile)

        # Initialize the main() class
        pmax_operations = pmaxCampaignManager(cfg)

        if message_data == "REFRESH":
            # Trigger to refresh the spreadsheet with Google Ads data.
            pmax_operations.refresh_spreadsheet()

        elif message_data == "UPLOAD":
            # Trigger to update Google Ads with spreadsheet input.
            pmax_operations.upload_to_google_Ads()

        print(f"------- END {message_data} EXECUTION -------")
