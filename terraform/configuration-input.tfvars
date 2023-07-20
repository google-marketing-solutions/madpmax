# Copyright 2023 Google LLC
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     https://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Google Ads 
# To optain Google Ads Developer token refer to:
#   https://developers.google.com/google-ads/api/docs/first-call/dev-token
# To obtain client_id and client_secret generate OAuth2 Credentials for Web Application, for guidance refer to:
#   https://developers.google.com/google-ads/api/docs/oauth/cloud-project
#  In initial setup, under "oauth consent screen", make sure to select "Internal"

# Config variables for the Google Ads Yaml file.
developer_token   = "" # Google Ads API Developer Token
client_id         = "" # "pmax-api" Client ID (from Cloud OAuth credentials)
client_secret     = "" # "pmax-api" Client Secret (from Cloud OAuth credentials)
oauth_token       = "" # https://developers.google.com/google-ads/api/docs/oauth/playground#generate_tokens
refresh_token     = "" # https://developers.google.com/google-ads/api/docs/oauth/playground#generate_tokens
login_customer_id = "" # [Optional] only if you setup under manager account
customer_id       = "" # Google Ads Customer ID
spreadsheet_id    = "" # Google Spreadsheet ID

# General Cloud Configuration
project_id            = ""   # defaults to current project. Project id were the solution will run.
cloud_function_name   = ""   # defaults to current project. Project id were the solution will run.
cloud_function_region = ""   # Cloud Region where the solutions will run.
cloud_storage_region  = ""   # or US
solution_user_list    = [""] # Comma separated list of solution users e.g. ["user:example@example.com"] (gives permissions to publish the pubsub trigger)