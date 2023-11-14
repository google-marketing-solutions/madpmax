function getService() {
  return OAuth2.createService('MyPubSub')
  .setAuthorizationBaseUrl('https://accounts.google.com/o/oauth2/auth')
  .setTokenUrl('https://accounts.google.com/o/oauth2/token')
  .setClientId(CLIENT_ID)
  .setClientSecret(CLIENT_SECRET)
  .setCallbackFunction('authCallback')
  .setPropertyStore(PropertiesService.getUserProperties())
  .setScope(['https://www.googleapis.com/auth/cloud-platform','https://www.googleapis.com/auth/pubsub','https://www.googleapis.com/auth/script.external_request'])
  .setParam('access_type', 'offline')
  .setParam('approval_prompt', 'force')
  .setParam('login_hint', Session.getActiveUser().getEmail());
}

function authCallback(request) {
  var service = getService();
  var isAuthorized = service.handleCallback(request);
  if (isAuthorized) {
    return HtmlService.createHtmlOutput('Success! You can close this tab.');
  } else {
    return HtmlService.createHtmlOutput('Denied. You can close this tab');
  }
}
// Reset the service
function reset() {
  var service = getService();
  service.reset();
}
/**
* Logs the redirect URI to register.
*/
function logRedirectUri() {
  var service = getService();
  Logger.log(service.getRedirectUri());
}