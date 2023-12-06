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

data "google_compute_default_service_account" "default" {
}

locals {
  default_service_account_full = "serviceAccount:${data.google_compute_default_service_account.default.email}"
}

resource "google_storage_bucket_iam_member" "member" {
  bucket = google_storage_bucket.config.name
  role   = "roles/storage.objectViewer"
  member = local.default_service_account_full
}

resource "google_cloudfunctions2_function_iam_member" "eventarc_invoker" {
  project        = google_cloudfunctions2_function.function.project
  location       = google_cloudfunctions2_function.function.location
  cloud_function = google_cloudfunctions2_function.function.name
  role           = "roles/cloudfunctions.invoker"
  member         = local.default_service_account_full
}

resource "google_project_iam_binding" "cloud_functions_invoker" {
  project = var.project_id
  role    = "roles/cloudfunctions.invoker"

  members = [
    local.default_service_account_full
  ]
}

resource "google_project_iam_binding" "service_account_token" {
  project = var.project_id
  role    = "roles/iam.serviceAccountTokenCreator"

  members = [
    local.default_service_account_full
  ]
}

resource "google_project_iam_binding" "pubsub_editor" {
  project = var.project_id
  role    = "roles/pubsub.editor"

  members = [
    local.default_service_account_full
  ]
}

resource "google_project_iam_binding" "run_invoker" {
  project = var.project_id
  role    = "roles/run.invoker"

  members = [
    local.default_service_account_full
  ]
}

resource "google_project_iam_binding" "eventarc_publisher" {
  project = var.project_id
  role    = "roles/eventarc.publisher"

  members = [
    local.default_service_account_full
  ]
}

resource "google_project_iam_binding" "pubsub_publisher" {
  project = var.project_id
  role    = "roles/pubsub.publisher"

  members = var.solution_user_list
}

resource "google_project_iam_binding" "log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"

  members = [
    local.default_service_account_full
  ]
}

