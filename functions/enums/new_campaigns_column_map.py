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
    CAMPAIGN_ALIAS = 0,
    CAMPAIGN_UPLOAD_STATUS = 1,
    CAMPAIGN_BUDGET = 2,
    BUDGET_DELIVERY_METHOD = 3,
    CAMPAIGN_STATUS = 4,
    BIDDING_STRATEGY = 5,
    CAMPAIGN_TARGET_ROAS = 6,
    CAMPAIGN_TARGET_CPA = 7,
    CUSTOMER_START_DATE = 8,
    CUSTOMER_END_DATE = 9,
    CUSTOMER_ID = 10,
    ERROR_MESSAGE =11