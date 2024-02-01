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
  STATUS = 0
  ASSET_CHECK = 1
  CUSTOMER_NAME = 2
  CAMPAIGN_NAME = 3
  ASSET_GROUP_NAME = 4
  ASSET_GROUP_STATUS = 5
  FINAL_URL = 6
  MOBILE_URL = 7
  PATH1 = 8
  PATH2 = 9
  HEADLINE1 = 10
  HEADLINE2 = 11
  HEADLINE3 = 12
  DESCRIPTION1 = 13
  DESCRIPTION2 = 14
  LONG_HEADLINE = 15
  BUSINESS_NAME = 16
  MARKETING_IMAGE = 17
  SQUARE_MARKETING_IMAGE = 18
  LOGO = 19
  MESSAGE = 20
