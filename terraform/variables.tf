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

variable "developer_token" {
  type        = string
  description = "developer_token"
}

variable "project_id" {
  type        = string
  description = "Project Id where the solutions will run"
}

variable "client_id" {
  type        = string
  description = "client_id"
}

variable "client_secret" {
  type        = string
  description = "client_secret"
}

variable "refresh_token" {
  type        = string
  description = "refresh_token"
}

variable "token" {
  type        = string
  description = "Oauth api access token"
}

variable "login_customer_id" {
  type        = string
  description = "[Optional] only if you setup under manager account"
}

variable "customer_id" {
  type        = string
  description = "Google Ads Customer Id, without dashes"
}

variable "cloud_function_region" {
  type        = string
  description = "Cloud Function Region where the solutions will run"
}

variable "cloud_function_name" {
  type        = string
  description = "The name of the cloud function"
  default     = "pmax-campaign-manager-default"
}

variable "cloud_storage_region" {
  type        = string
  description = "region where to deploy the cloud storage bucket containing the config"
}

variable "solution_user_list" {
  type        = list
  description = "List of users for the solution"
}

variable "spreadsheet_id" {
  type        = string
  description = "The Google Spreadsheet id for the sheet used to power the application."
}