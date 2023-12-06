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

import enum


class assetsColumnMap(enum.IntEnum):
    ASSET_STATUS = 0,
    DELETE_ASSET = 1,
    CUSTOMER_NAME = 2,
    CAMPAIGN_NAME = 3,
    ASSET_GROUP_NAME = 4,
    ASSET_TYPE = 5,
    ASSET_TEXT = 6,
    ASSET_CALL_TO_ACTION = 7,
    ASSET_URL = 8,
    ASSET_THUMBNAIL = 9,
    ERROR_MESSAGE = 10,
    ASSET_GROUP_ASSET = 11
