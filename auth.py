# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Gets the OAuth2 credential from file.
from google.oauth2 import credentials
import yaml

_SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/adwords',
]
_TOKEN_URI = 'https://oauth2.googleapis.com/token'


def get_credentials_from_file(token, refresh_token, client_id, client_secret):
    '''Gets the Oauth2 credentials.
    Args:
      client_secret_file: path to client secret file.
      scopes: a list of the required scopes strings for this credential.
      token: path to the token.json file.
      port: port used to listen for auth response on localhost.
    Returns:
      An OAuth Credentials object for the authenticated user.
    '''
    creds = credentials.Credentials(
        token=token,
        refresh_token=refresh_token,
        token_uri=_TOKEN_URI,
        client_id=client_id,
        client_secret=client_secret,
        scopes=_SCOPES
    )
    # Creds expired generate new creds using refresh token.
    if not creds.valid and creds.expired and creds.refresh_token:
        credentials.Credentialsrefresh(
            refresh_token, client_id, client_secret, Request())
    if not creds or not creds.valid:
        raise Exception(
            'Error while generating OAuth credentials, no credentials returned.')
    return creds


if __name__ == '__main__':
    with open('google-ads.yaml', 'r') as ymlfile:
        cfg = yaml.safe_load(ymlfile)
    get_credentials_from_file(
        cfg['oauth_token'],
        cfg['refresh_token'],
        cfg['client_id'],
        cfg['client_secret'],
    )
