import base64
from cloudevents.http import CloudEvent
import functions_framework


@functions_framework.cloud_event
def pubSubEntry(cloud_event: CloudEvent) -> None:
    """ Listener method for PubSub Events.

    Args:
    cloud_event: Message Object containing the PubSub Request details from the Function Trigger.
    """

    if cloud_event:
        # Print out the data from Pub/Sub, to prove that it worked
        message_data = base64.b64decode(
            cloud_event.data["message"]["data"]).decode()

        print(f"------- START {message_data} EXECUTION -------")

        if message_data == "REFRESH":
            # Placeholder for function call to trigger asset upload to Google Ads.
            print("Refresh Placeholder")
        elif message_data == "UPLOAD":
            # Placeholder for function call to trigger asset upload to Google Ads.
            print("Upload Placeholder")

        print(f"------- END {message_data} EXECUTION -------")
