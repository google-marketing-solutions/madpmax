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

resource "google_project_service" "cloudfunctions" {
  project = var.project_id
  service = "cloudfunctions.googleapis.com"
  disable_on_destroy = false
}
resource "google_project_service" "logging" {
  project = var.project_id
  service = "logging.googleapis.com"
  disable_on_destroy = false
}
resource "google_project_service" "googleads" {
  project = var.project_id
  service = "googleads.googleapis.com"
  disable_on_destroy = false
}
resource "google_project_service" "cloudtasks" {
  project = var.project_id
  service = "cloudtasks.googleapis.com"
  disable_on_destroy = false
}
resource "google_project_service" "cloudbuild" {
  project = var.project_id
  service = "cloudbuild.googleapis.com"
  disable_on_destroy = false
}
resource "google_project_service" "sheets" {
  project = var.project_id
  service = "sheets.googleapis.com"
  disable_on_destroy = false
}
resource "google_project_service" "drive" {
  project = var.project_id
  service = "drive.googleapis.com"
  disable_on_destroy = false
}
resource "google_project_service" "youtube" {
  project = var.project_id
  service = "youtube.googleapis.com"
  disable_on_destroy = false
}
resource "google_project_service" "pubsub" {
  project = var.project_id
  service = "pubsub.googleapis.com"
  disable_on_destroy = false
}
resource "google_project_service" "eventarc" {
  project = var.project_id
  service = "eventarc.googleapis.com"
  disable_on_destroy = false
}
resource "google_project_service" "artifactregistry" {
  project = var.project_id
  service = "artifactregistry.googleapis.com"
  disable_on_destroy = false
}
