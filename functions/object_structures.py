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
"""Module containing all data mappings.

Mad pMax works with a spreadsheet as data source, when changes are made to the
spreadsheet template, or sheetnames, they need to be updated here.
"""
import dataclasses


@dataclasses.dataclass()
class ConfigFile:
    """Instance with mapping of the config file.

    Attributes:
        use_proto_plus: Whether or not to use proto-plus messages.
        developer_token: Developer token from Google Ads MCC level.
        client_id: OAuth cleint id.
        client_secret: OAuth secret.
        access_token: Access token for Google Ads API access.
        refresh_token: Refresh token for Google Ads API access.
        login_customer_id: Google Ads customer id of MCC level.
        customer_id: Google Ads customer id under MCC level.
        spreadsheet_id: Id of spreadsheet to work with. Consist of numbers and letters. Eg take form the link to your template spreadsheet https://docs.google.com/spreadsheets/d/{spreadsheet_id}
    """
    use_proto_plus: bool
    developer_token: str
    client_id: str
    client_secret: str
    access_token: str
    refresh_token: str
    login_customer_id: int
    customer_id: int
    spreadsheet_id: str
