function pubsub(project, topic, attr, data) {
    var service = getService();
    
    if (!service.hasAccess()) {
      var authorizationUrl = service.getAuthorizationUrl();
      var template = HtmlService.createTemplate(
        '<a href="<?= authorizationUrl ?>" target="_blank">Authorize</a>. ' +
        'Reopen the sidebar when the authorization is complete.');
      template.authorizationUrl = authorizationUrl;
      var page = template.evaluate();
      SpreadsheetApp.getUi().showSidebar(page);
      
    } else {
      var url = 'https://pubsub.googleapis.com/v1/projects/[PROJECT]/topics/[TOPIC]:publish'
      .replace('[TOPIC]', topic)
      .replace('[PROJECT]', project);
      
      // The data attribute is of 'string' type and needs to be base64 Encoded!
      var body = {
        messages: [
          {
            attributes: attr,
            data: Utilities.base64Encode(data)
          }]
      };    
      
      var response = UrlFetchApp.fetch(url, {
        method: 'POST',
        contentType: 'application/json',
        muteHttpExceptions: true,
        payload: JSON.stringify(body),
        headers: {
          Authorization: 'Bearer ' + service.getAccessToken()
        }
      });
      
      var result = JSON.parse(response.getContentText());
      var message = JSON.stringify(result);
     return {
        log: message
      }
    } //end of if
  }