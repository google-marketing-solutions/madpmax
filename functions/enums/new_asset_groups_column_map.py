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

class newAssetGroupsColumnMap(enum.IntEnum):
    ASSET_GROUP_ALIAS = 0,
    CAMPAIGN_ALIAS = 1,
    STATUS = 2,
    ASSET_CHECK = 3,
    ASSET_GROUP_NAME = 4,
    FINAL_URL = 5,
    MOBILE_URL = 6,
    PATH1 = 7,
    PATH2 = 8,
    CAMPAIGN_STATUS = 9,
    MESSAGE = 10