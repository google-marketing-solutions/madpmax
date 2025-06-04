/**
 * Copyright 2024 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

// Update with your Cloud Project Client ID and Client Secret.
// Should be different credentials to the main pMAx Cloud credentials.
// Use the following redirect URI is
// https://script.google.com/macros/d/[REPLACE_WITH_SCRIPT_ID]/usercallback
const CLIENT_ID = 'UPDATE_CLINET_ID_HERE';          // OAuth client id.
const CLIENT_SECRET = 'UPDATE_CLIENT_SECRET_HERE';  // OAuth client secret.
const PROJECT_ID = 'UPDATE_PROJECT_ID_HERE';    // The Project ID of your GCP project.
const PUBSUB_TOPIC = 'UPDATE_PUBSUB_TOPIC_NAME_HERE';  // Name of PubSub topic.
