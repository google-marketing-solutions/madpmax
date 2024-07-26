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

# Links terraform to a cloud storage backend to manage Terraform state.
# Conduct the following steps:
# 1. Deploy Ads Api Tools through regular terraform workflow; init, plan, deploy
# 2. Note down the bucket name of the resource created in
# "google_storage_bucket.backend".
# 3. Fill in the bucket name in terraform.backend.gcs below.
# 4. Uncomment terraform.backend.gcs
# 5. Reinitizalize terraform through terraform init and accept connection
# to GCS backend.

resource "google_storage_bucket" "backend" {
  name          = "${random_id.bucket_prefix.hex}-bucket-tfstate"
  force_destroy = false
  location      = var.cloud_storage_region
  storage_class = "STANDARD"
  uniform_bucket_level_access = true
  versioning {
    enabled = true
  }
}