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


class newCampaignsColumnMap(enum.IntEnum):
  CAMPAIGN_UPLOAD_STATUS = 0
  CUSTOMER_NAME = 1
  CAMPAIGN_NAME = 2
  CAMPAIGN_BUDGET = 3
  BUDGET_DELIVERY_METHOD = 4
  CAMPAIGN_STATUS = 5
  BIDDING_STRATEGY = 6
  CAMPAIGN_TARGET_ROAS = 7
  CAMPAIGN_TARGET_CPA = 8
  CUSTOMER_START_DATE = 9
  CUSTOMER_END_DATE = 10
  ERROR_MESSAGE = 11
