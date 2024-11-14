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

resource "local_file" "ads_config" {
  content = templatefile("./config-template.yaml", {
    developer_token    = "${var.developer_token}",
    client_id          = "${var.client_id}",
    client_secret      = "${var.client_secret}",
    access_token       = "${var.access_token}",
    refresh_token      = "${var.refresh_token}",
    login_customer_id  = "${var.login_customer_id}"
    customer_id_inclusion_list = "${var.customer_id_inclusion_list}"
    spreadsheet_id     = "${var.spreadsheet_id}"
  })
  filename = "../functions/config.yaml"
}

data "archive_file" "zip_code_repo" {
  type        = "zip"
  source_dir  = "../functions/"
  output_path = "../../dist/function-source.zip"
  depends_on = [
    local_file.ads_config
  ]
}

resource "random_id" "bucket_prefix" {
  byte_length = 8
}

resource "google_pubsub_topic" "default" {
  name = "performance-max-topic"
}

resource "google_storage_bucket_object" "cf_upload_object" {
  name   = "src-${data.archive_file.zip_code_repo.output_md5}.zip"
  bucket = google_storage_bucket.cf_upload_bucket.name
  source = "../../dist/function-source.zip"
  depends_on = [
    data.archive_file.zip_code_repo
  ]
}

resource "google_cloudfunctions2_function" "function" {
  name                  = var.cloud_function_name
  location              = var.cloud_function_region
  description           = "mad Pmax function"

  build_config {
    runtime     = "python312"
    entry_point = "pmax_trigger" # Set the entry entry_point
    source {
      storage_source {
        bucket = google_storage_bucket.cf_upload_bucket.name
        object = google_storage_bucket_object.cf_upload_object.name
      }
    }
  }

  service_config {
    available_memory      = "1G"
    service_account_email = google_service_account.service_account.email
  }

  event_trigger {
    trigger_region = var.cloud_function_region
    event_type = "google.cloud.pubsub.topic.v1.messagePublished"
    pubsub_topic   = google_pubsub_topic.default.id
    retry_policy = "RETRY_POLICY_DO_NOT_RETRY"
    service_account_email = google_service_account.service_account.email
  }
}