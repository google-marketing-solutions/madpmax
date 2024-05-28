/**
 * Copyright 2024 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *       http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/**
 * Publishes a message to a Pub/Sub topic.
 * @param {string} project The project ID.
 * @param {string} topic The topic ID.
 * @param {{id: string, value: string}} attr Object containing of the attributes of the message.
 * @param {string} data The data of the message.
 * @return {UrlFetchApp.HTTPResponse | undefined} The UrlFetchApp.HTTPResponse result object. If the
 *     service does not have access, the function returns undefined.
 */
function pubsub(project, topic, attr, data) {
  const service = getService();

  if (!service.hasAccess()) {
    const authorizationUrl = service.getAuthorizationUrl();
    const template = HtmlService.createTemplate(
      '<a href="<?= authorizationUrl ?>" target="_blank">Authorize</a>. ' +
        'Reopen the sidebar when the authorization is complete.',
    );
    template.authorizationUrl = authorizationUrl;
    const page = template.evaluate();
    SpreadsheetApp.getUi().showSidebar(page);

    return;
  }

  const url =
    `https://pubsub.googleapis.com/v1/projects/${project}/topics/${topic}:publish`

  const body = {
    messages: [
      {
        attributes: attr,
        data: Utilities.base64Encode(data),
      },
    ],
  };

  const response = UrlFetchApp.fetch(url, {
    method: 'POST',
    contentType: 'application/json',
    muteHttpExceptions: true,
    payload: JSON.stringify(body),
    headers: {
      Authorization: 'Bearer ' + service.getAccessToken(),
    },
  });

  return response;
}
