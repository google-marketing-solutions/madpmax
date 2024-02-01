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


class assetTypes(enum.StrEnum):
  LANDSCAPE_IMAGE = "MARKETING_IMAGE"
  SQUARE_IMAGE = "SQUARE_MARKETING_IMAGE"
  PORTRAIT_IMAGE = "PORTRAIT_MARKETING_IMAGE"
  SQUARE_LOGO = "LOGO"
  LANDSCAPE_LOGO = "LANDSCAPE_LOGO"
  YOUTUBE_VIDEO = "YOUTUBE_VIDEO"
  HEADLINE = "HEADLINE"
  DESCRIPTION = "DESCRIPTION"
  LONG_HEADLINE = "LONG_HEADLINE"
  BUSINESS_NAME = "BUSINESS_NAME"
  CALL_TO_ACTION = "CALL_TO_ACTION_SELECTION"
  SITELINK = "SITELINK"
