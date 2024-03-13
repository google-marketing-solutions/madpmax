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
 * Creates a new service.
 * @return {GoogleAppsScript.OAuth2.Service} The authentication service
 *    object.
 */
function getService() {
  return OAuth2.createService('MyPubSub')
    .setAuthorizationBaseUrl('https://accounts.google.com/o/oauth2/auth')
    .setTokenUrl('https://accounts.google.com/o/oauth2/token')
    .setClientId(CLIENT_ID)
    .setClientSecret(CLIENT_SECRET)
    .setCallbackFunction('authCallback')
    .setPropertyStore(PropertiesService.getUserProperties())
    .setScope([
      'https://www.googleapis.com/auth/cloud-platform',
      'https://www.googleapis.com/auth/pubsub',
      'https://www.googleapis.com/auth/script.external_request',
    ])
    .setParam('access_type', 'offline')
    .setParam('approval_prompt', 'force')
    .setParam('login_hint', Session.getActiveUser().getEmail());
}

/**
 * Handles the OAuth callback.
 * @param {GoogleAppsScript.Events.AppsScriptHttpRequestEvent} request
 *    The HTTP request.
 * @return {GoogleAppsScript.HTML.HtmlOutput} The HTML output to be
 *    rendered in browser.
 */
function authCallback(request) {
  const service = getService();
  const isAuthorized = service.handleCallback(request);
  if (isAuthorized) {
    return HtmlService.createHtmlOutput('Success! You can close this tab.');
  } else {
    return HtmlService.createHtmlOutput('Denied. You can close this tab');
  }
}

/**
 * Resets the service.
 */
function reset() {
  const service = getService();
  service.reset();
}

/**
 * Logs the redirect URI to register.
 */
function logRedirectUri() {
  const service = getService();
  Logger.log(service.getRedirectUri());
}
