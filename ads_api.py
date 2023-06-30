# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Provides functionality to interact with Google Ads platform."""

from google.ads import googleads
from google.api_core import protobuf_helpers
from google.ads.googleads.errors import GoogleAdsException
from PIL import Image
from io import BytesIO
from uuid import uuid4

import enum
import requests

_ASSET_TEMP_ID = -10000
_ASSET_GROUP_TEMP_ID = -1000
_CAMPAIGN_TEMP_ID = -1


class AdService():
    """Provides Google ads API service to interact with Ads platform."""

    class newAssetsColumnMap(enum.IntEnum):
        ASSET_GROUP_ALIAS = 0,
        ASSET_STATUS = 1,
        DELETE_ASSET = 2,
        ASSET_TYPE = 3,
        ASSET_TEXT = 4,
        ASSET_CALL_TO_ACTION = 5,
        ASSET_URL = 6,
        ERROR_MESSAGE = 7

    class assetGroupListColumnMap(enum.IntEnum):
        ASSET_GROUP_ALIAS = 0,
        ASSET_GROUP_NAME = 1,
        ASSET_GROUP_ID = 2,
        CAMPAIGN_NAME = 3,
        CAMPAIGN_ID = 4,
        CUSTOMER_NAME = 5,
        CUSTOMER_ID = 6

    class newAssetGroupsColumnMap(enum.IntEnum):
        ASSET_GROUP_ALIAS = 0,
        CAMPAIGN_ALIAS = 1,
        ASSET_CHECK = 2,
        ASSET_GROUP_NAME = 3,
        FINAL_URL = 4,
        MOBILE_URL = 5,
        PATH1 = 6,
        PATH2 = 7,
        CAMPAIGN_STATUS = 8,
        STATUS = 9,
        MESSAGE = 10

    class newCampaignsColumnMap(enum.IntEnum):
        CAMPAIGN_ALIAS = 0,
        CAMPAIGN_SETTINGS_ALIAS = 1,
        CAMPAIGN_NAME = 2,
        START_DATE = 3,
        END_DATE = 4,
        CUSTOMER_ID = 5

    class campaignListColumnMap(enum.IntEnum):
        CAMPAIGN_ALIAS = 0,
        CAMPAIGN_NAME = 1,
        CAMPAIGN_ID = 2,
        CUSTOMER_NAME = 3,
        CUSTOMER_ID = 4

    class assetStatus(enum.Enum):
        UPLOADED = "UPLOADED",
        ERROR = "ERROR",
        NEW = "NEW"


    def __init__(self, ads_account_file):
        """Constructs the AdService instance.

        Args:
          ads_account_file: Path to Google Ads API account file.
        """
        self._google_ads_client = googleads.client.GoogleAdsClient.load_from_storage(
            ads_account_file, version='v14')
        self._cache_ad_group_ad = {}
        self.prev_image_asset_list = None
        self.prev_customer_id = None

    def _get_campaign_resource_name(self, customer_id, campaign_id):
        """Gets a campaign by customer id and campaign id.

        Args:
        customer_id: customer id.
        campaign_id: id of the campaign

        Returns:
        Campaign resource.
        """
        campaign_service = self._google_ads_client.get_service(
            "CampaignService")

        # Create campaign operation.
        return campaign_service.campaign_path(
            customer_id, campaign_id
        )

    def _get_asset_group_resource_name(self, customer_id, asset_group_id):
        """Generates the Ad group resource name based on input.

        Args:
        customer_id: customer id.
        asset_group_id: id of the ad group

        Returns:
        Asset group resource.
        """
        asset_group_service = self._google_ads_client.get_service(
            "AssetGroupService")

        # Create ad group operation.
        return asset_group_service.asset_group_path(
            customer_id, asset_group_id
        )
    # Creates image asset without linking

    def _create_image_asset(self, image_url, name, type, customer_id):
        """Generates the image asset and returns the resource name.

        Args:
        image_url: full url of the image file.
        name: the name of the image asset.
        type: The asset type for the image asset.
        customer_id: customer id.

        Returns:
        Asset operation, resource name or None.
        """
        global _ASSET_TEMP_ID

        # Download image from URL and determine the ratio.
        image_content = requests.get(image_url).content
        img = Image.open(BytesIO(image_content))
        img_ratio = img.width / img.height

        if img_ratio == 1 and type == "IMAGE":
            field_type = self._google_ads_client.enums.AssetFieldTypeEnum.SQUARE_MARKETING_IMAGE
        elif img_ratio < 1 and type == "IMAGE":
            field_type = self._google_ads_client.enums.AssetFieldTypeEnum.PORTRAIT_MARKETING_IMAGE
        elif img_ratio > 1 and type == "IMAGE":
            field_type = self._google_ads_client.enums.AssetFieldTypeEnum.MARKETING_IMAGE
        elif img_ratio == 1 and type == "LOGO":
            field_type = self._google_ads_client.enums.AssetFieldTypeEnum.LOGO
        elif img_ratio > 1 and type == "LOGO":
            field_type = self._google_ads_client.enums.AssetFieldTypeEnum.LANDSCAPE_LOGO
        else:
            # TODO: Add return for error message (not supported image size / field_type.)
            field_type = None

        asset_service = self._google_ads_client.get_service("AssetService")
        resource_name = asset_service.asset_path(customer_id, _ASSET_TEMP_ID)

        _ASSET_TEMP_ID -= 1

        if image_content:
            # Create and link the Marketing Image Asset.
            asset_operation = self._google_ads_client.get_type(
                "MutateOperation")
            asset = asset_operation.asset_operation.create
            asset.name = name
            asset.type = self._google_ads_client.enums.AssetTypeEnum.IMAGE
            asset.resource_name = resource_name
            asset.image_asset.full_size.url = image_url
            asset.image_asset.data = image_content

            return asset_operation, resource_name, field_type

        return None

    def _create_video_asset(self, video_url, field_type, customer_id):
        """Generates the image asset and returns the resource name.

        Args:
        video_url: full url of the image file.
        field_type: Google Ads field type, required for assigning asset to asset group.
        customer_id: customer id.

        Returns:
        Asset operation, resource name or None.
        """
        global _ASSET_TEMP_ID

        youtube_id = _retrieve_yt_id(video_url)

        asset_service = self._google_ads_client.get_service("AssetService")
        resource_name = asset_service.asset_path(customer_id, _ASSET_TEMP_ID)

        _ASSET_TEMP_ID -= 1

        if youtube_id:
            # Create and link the Marketing Image Asset.
            asset_operation = self._google_ads_client.get_type(
                "MutateOperation")
            asset = asset_operation.asset_operation.create
            asset.resource_name = resource_name
            asset.youtube_video_asset.youtube_video_title = "Marketing Video #{uuid4()}"
            asset.youtube_video_asset.youtube_video_id = youtube_id

            return asset_operation, resource_name, field_type

        return None

    def _retrieve_yt_id(self, video_url):
        """Retrieves the YouTube video id from the URL.

        Args:
        video_url: full url of the video on YT.

        Returns:
        String value containing the id, or None.
        """
        regex = "^.*(youtu\.be\/|v\/|u\/\w\/|embed\/|shorts\/|watch\?v=|\&v=)([^#\&\?]*).*"
        result = re.search(regex, video_url)
        if result:
            return result.group(2)

        return None

    def _create_text_asset(self, text, field_type, customer_id):
        """Generates the image asset and returns the resource name.

        Args:
        video_url: full url of the image file.
        field_type: Google Ads field type, required for assigning asset to asset group.
        customer_id: customer id.

        Returns:
        Asset operation, resource name or None.
        """
        global _ASSET_TEMP_ID

        asset_service = self._google_ads_client.get_service("AssetService")
        resource_name = asset_service.asset_path(customer_id, _ASSET_TEMP_ID)

        _ASSET_TEMP_ID -= 1

        # Create and link the Marketing Image Asset.
        asset_operation = self._google_ads_client.get_type("MutateOperation")
        asset = asset_operation.asset_operation.create
        asset.resource_name = resource_name
        asset.text_asset.text = text

        field_type_enum = self._google_ads_client.enums.AssetFieldTypeEnum[field_type]

        return asset_operation, resource_name, field_type_enum

    def _create_call_to_action_asset(self, action_selection, customer_id):
        """Generates the image asset and returns the resource name.

        Args:
        action_selection: selection from call to action ENUM
        customer_id: customer id.

        Returns:
        Asset operation, resource name or None.
        """
        global _ASSET_TEMP_ID

        asset_service = self._google_ads_client.get_service("AssetService")
        resource_name = asset_service.asset_path(customer_id, _ASSET_TEMP_ID)
        field_type = "CALL_TO_ACTION_SELECTION"

        _ASSET_TEMP_ID -= 1

        asset_operation = self._google_ads_client.get_type("MutateOperation")
        asset = asset_operation.asset_operation.create
        asset.resource_name = resource_name
        asset.call_to_action_type = action_selection
        asset.field_type = field_type

        return asset_operation, resource_name, field_type

    def _add_asset_to_asset_group(self, asset_resource, asset_group_id, field_type, customer_id):
        """Adds the asset resource to an asset group.

        Args:
        asset_resource: resource name of the asset group.
        image_url: full url of the image file.
        field_type: Google Ads field type, required for assigning asset to asset group.
        customer_id: customer id.
        """
        asset_group_service = self._google_ads_client.get_service(
            "AssetGroupService")

        asset_group_asset_operation = self._google_ads_client.get_type(
            "MutateOperation")
        asset_group_asset = asset_group_asset_operation.asset_group_asset_operation.create

        asset_group_asset.field_type = field_type
        asset_group_asset.asset_group = asset_group_service.asset_group_path(
            customer_id, asset_group_id,
        )
        asset_group_asset.asset = asset_resource

        return asset_group_asset_operation

    def _bulk_mutate(self, mutate_type, mutate_operations, customer_id):
        """Process Bulk Mutate operation via Google Ads API.

        Args:
        mutate_operations: Array of mutate operations.
        customer_id: customer id.

        Returns:
        Response API object.
        """
        response = None
        error_message = None

        googleads_service = self._google_ads_client.get_service(
            "GoogleAdsService")
        request = self._google_ads_client.get_type("MutateGoogleAdsRequest")
        request.customer_id = customer_id
        request.mutate_operations = mutate_operations
        if mutate_type == "ASSETS":
            request.partial_failure = True
            
            response = googleads_service.mutate(
                request=request
            )
        else:
            try:
                response = googleads_service.mutate(
                    request=request
                )
            except GoogleAdsException as ex:
                error_message = f'Request with ID "{ex.request_id}" failed and includes the following errors:'
                for error in ex.failure.errors:
                    if error.message != "Resource was not found.":
                        error_message = error_message + f'\n\tError message: "{error.message}".'
                print(error_message)

        return response, error_message

    def is_partial_failure_error_present(self, response):
        """Checks whether a response message has a partial failure error.
        In Python the partial_failure_error attr is always present on a response
        message and is represented by a google.rpc.Status message. So we can't
        simply check whether the field is present, we must check that the code is
        non-zero. Error codes are represented by the google.rpc.Code proto Enum:
        https://github.com/googleapis/googleapis/blob/master/google/rpc/code.proto
        Args:
            response:  A MutateAdGroupsResponse message instance.
        Returns: A boolean, whether or not the response message has a partial
            failure error.
        """
        partial_failure = getattr(response, "partial_failure_error", None)
        code = getattr(partial_failure, "code", None)
        return code != 0

    def process_asset_results(self, response, operations, row_mapping):
        """Prints partial failure errors and success messages from a response.
        This function shows how to retrieve partial_failure errors from a response
        message (in the case of this example the message will be of type
        MutateAdGroupsResponse) and how to unpack those errors to GoogleAdsFailure
        instances. It also shows that a response with partial failures may still
        contain successful requests, and that those messages should be parsed
        separately.
        """
        error_obj = {}

        # Check for existence of any partial failures in the response.
        if self.is_partial_failure_error_present(response):
            partial_failure = getattr(response, "partial_failure_error", None)
            # partial_failure_error.details is a repeated field and iterable
            error_details = getattr(partial_failure, "details", [])

            for error_detail in error_details:
                # Retrieve an instance of the GoogleAdsFailure class from the client
                failure_message = self._google_ads_client.get_type(
                    "GoogleAdsFailure")
                # Parse the string into a GoogleAdsFailure message instance.
                # To access class-only methods on the message we retrieve its type.
                GoogleAdsFailure = type(failure_message)
                failure_object = GoogleAdsFailure.deserialize(
                    error_detail.value)

                for error in failure_object.errors:
                    # Construct a list that details which element in
                    # the above ad_group_operations list failed (by index number)
                    # as well as the error message and error code.
                    error_obj[error.location.field_path_elements[0].index] = [
                        f"A partial failure creating a(n) {error.location.field_path_elements[1].field_name[:-10]} at index {error.location.field_path_elements[0].index} occurred",
                        f"Error message: {error.message}\n",
                        f"Error code: {str(error.error_code).strip()}\n",
                        f"Error trigger: {error.trigger.string_value}"]
        else:
            print(
                "All operations completed successfully. No partial failure "
                "to show."
            )

        # In the list of results, operations from the ad_group_operation list
        # that failed will be represented as empty messages. This loop detects
        # such empty messages and ignores them, while printing information about
        # successful operations.
        results = {}
        suffix = "_result"
        i = 0
        for result in response.mutate_operation_responses:
            for field_descriptor, value in result._pb.ListFields():
                if field_descriptor.name.endswith(suffix):
                    name = field_descriptor.name[: -len(suffix)]
                else:
                    name = field_descriptor.name
                
                # Check if the index also appears in the list of errors from the Bulk Mutate response.
                if i in error_obj:
                    # Retrieve the row number in the Google Sheet corresponding to the error message.
                    print(error_obj[i][0])
                    error_asset_resource = operations[i].asset_group_asset_operation.create.asset

                    for op in operations:
                        if op.asset_operation.create.resource_name == error_asset_resource:
                            sheet_row = row_mapping[op.asset_operation.create.resource_name]
                            if op.asset_operation.create.text_asset:
                                print(
                                    "\tText: " + op.asset_operation.create.text_asset.text)
                            if op.asset_operation.create.image_asset.full_size.url:
                                print("\tImage Name: " +
                                      op.asset_operation.create.name)
                                print(
                                    "\tImage URL: " + op.asset_operation.create.image_asset.full_size.url + "\n")
                    
                    if sheet_row not in results:
                        results[sheet_row] = {}

                    results[sheet_row]["status"] = self.assetStatus.ERROR.value[0]
                    results[sheet_row]["message"] = error_obj[i][1] + error_obj[i][2] + error_obj[i][3]

                else:
                    print(
                        f"Created a(n) {name} with "
                        f"{str(value).strip()}."
                    )
                    if operations[i].asset_group_asset_operation.create.asset and operations[i].asset_group_asset_operation.create.asset in row_mapping:
                        sheet_row = row_mapping[operations[i].asset_group_asset_operation.create.asset]

                        if sheet_row not in results:
                            results[sheet_row] = {}
                            results[sheet_row]["status"] = self.assetStatus.UPLOADED.value[0]
                            results[sheet_row]["message"] = ""

                i += 1
        return results
    
    def _create_asset_group(self, asset_group_details, campaign_id, customer_id):
        """Creates a list of MutateOperations that create a new asset_group.

        A temporary ID will be assigned to this asset group so that it can
        be referenced by other objects being created in the same Mutate request.

        Args:
            asset_group_details: A list of values required to setup an asset group in Google ads.
            customer_id: a pmax campaign ID.
            customer_id: a client customer ID.

        Returns:
            MutateOperation that create a new asset group.
        """
        global _ASSET_GROUP_TEMP_ID
        asset_group_id = _ASSET_GROUP_TEMP_ID
        _ASSET_GROUP_TEMP_ID -= 1

        asset_group_service = self._google_ads_client.get_service("AssetGroupService")
        campaign_service = self._google_ads_client.get_service("CampaignService")

        operations = []

        # Create the AssetGroup
        mutate_operation = self._google_ads_client.get_type("MutateOperation")
        asset_group = mutate_operation.asset_group_operation.create
        asset_group.name = asset_group_details[self.newAssetGroupsColumnMap.ASSET_GROUP_NAME]
        asset_group.campaign = campaign_service.campaign_path(
            customer_id, campaign_id
        )
        asset_group.final_urls.append(asset_group_details[self.newAssetGroupsColumnMap.FINAL_URL])
        asset_group.final_mobile_urls.append(asset_group_details[self.newAssetGroupsColumnMap.MOBILE_URL])
        asset_group.status = self._google_ads_client.enums.AssetGroupStatusEnum[asset_group_details[self.newAssetGroupsColumnMap.CAMPAIGN_STATUS]]
        asset_group.resource_name = asset_group_service.asset_group_path(
            customer_id, asset_group_id,
        )

        return mutate_operation, asset_group_id

    def _create_multiple_text_assets(self, operations, customer_id):
        """Creates multiple text assets and returns the list of resource names.
        Args:
            client: an initialized GoogleAdsClient instance.
            operations: a list of api operations, each of which will be used to create a text
            asset.
            customer_id: a client customer ID.
        Returns:
            asset_resource_names: a list of asset resource names.
        """
        # Here again we use the GoogleAdService to create multiple text
        # assets in a single request.
        googleads_service = self._google_ads_client.get_service("GoogleAdsService")
        
        asset_resource_names = {}
        
        for asset_group_alias in operations:
            # Send the operations in a single Mutate request.
            response = googleads_service.mutate(
                customer_id=customer_id, mutate_operations=operations[asset_group_alias],
            )

            asset_resource_names[asset_group_alias] = []
            index = 0
            for result in response.mutate_operation_responses:
                temp_id = operations[asset_group_alias][index].asset_operation.create.resource_name
                if result._pb.HasField("asset_result"):
                    asset_resource_names[asset_group_alias].append((result.asset_result.resource_name, temp_id))
                index += 1
            self.print_response_details(response)

        return asset_resource_names
    
    def print_response_details(self, response):
        """Prints the details of a MutateGoogleAdsResponse.
        Parses the "response" oneof field name and uses it to extract the new
        entity's name and resource name.
        Args:
            response: a MutateGoogleAdsResponse object.
        """
        # Parse the Mutate response to print details about the entities that
        # were created by the request.
        suffix = "_result"
        for result in response.mutate_operation_responses:
            for field_descriptor, value in result._pb.ListFields():
                if field_descriptor.name.endswith(suffix):
                    name = field_descriptor.name[: -len(suffix)]
                else:
                    name = field_descriptor.name
                print(
                    f"Created a(n) {name} with "
                    f"{str(value).strip()}."
                )

    def compile_asset_group_operations(self, asset_group_operations, headlines, descriptions, row_mapping, customer_id):

        asset_group_service = self._google_ads_client.get_service("AssetGroupService")

        for asset_group_alias in asset_group_operations:

            asset_group_id = asset_group_operations[asset_group_alias][0].asset_group_operation.create.resource_name

            #  Link the description assets.
            for resource_name in descriptions[asset_group_alias]:
                mutate_operation = self._google_ads_client.get_type("MutateOperation")
                asset_group_asset = mutate_operation.asset_group_asset_operation.create
                asset_group_asset.field_type = (
                    self._google_ads_client.enums.AssetFieldTypeEnum.DESCRIPTION
                )
                asset_group_asset.asset_group = asset_group_id
                asset_group_asset.asset = resource_name[0]
                asset_group_operations[asset_group_alias].insert(1, mutate_operation)
                row_mapping[resource_name[0]] = row_mapping[resource_name[1]]


            # Link the headline assets.
            for resource_name in headlines[asset_group_alias]:
                mutate_operation = self._google_ads_client.get_type("MutateOperation")
                asset_group_asset = mutate_operation.asset_group_asset_operation.create
                asset_group_asset.field_type = self._google_ads_client.enums.AssetFieldTypeEnum.HEADLINE
                asset_group_asset.asset_group = asset_group_id
                asset_group_asset.asset = resource_name[0]
                asset_group_operations[asset_group_alias].insert(1, mutate_operation)
                row_mapping[resource_name[0]] = row_mapping[resource_name[1]]
            
        return asset_group_operations, row_mapping

    def process_asset_group_results(self, error_message, operations, row_mapping):
            """Prints partial failure errors and success messages from a response.
            This function shows how to retrieve partial_failure errors from a response
            message (in the case of this example the message will be of type
            MutateAdGroupsResponse) and how to unpack those errors to GoogleAdsFailure
            instances. It also shows that a response with partial failures may still
            contain successful requests, and that those messages should be parsed
            separately.
            """

            # In the list of results, operations from the ad_group_operation list
            # that failed will be represented as empty messages. This loop detects
            # such empty messages and ignores them, while printing information about
            # successful operations.
            results = {}
            i = 0
            
            for op in operations:
                if op.asset_operation.create.resource_name in row_mapping:
                    sheet_row = row_mapping[op.asset_operation.create.resource_name]
            
                    if sheet_row not in results:
                        results[sheet_row] = {}

                    results[sheet_row]["status"] = "ERROR"
                    results[sheet_row]["message"] = error_message

            return results
