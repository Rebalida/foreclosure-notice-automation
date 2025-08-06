import os
import logging
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Path to the token file
TOKEN_PATH = 'credentials/token.json'
CREDENTIALS_PATH = 'credentials/credentials.json'

def get_credentials(scopes: list) -> Credentials:
    """
    Handles Google API authentication.
    - Loads existing credentials from token.json.
    - If invalid or expired, refreshes them.
    - If non-existent, runs the OAuth2 flow to create them.
    Args:
        scopes: A list of Google API scopes required.
    Returns:
        Valid Google API credentials.
    """
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, scopes)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                logging.info("Credentials refreshed successfully.")
            except Exception as e:
                logging.error(f"Failed to refresh token: {e}. Please re-authenticate.")
                # If refresh fails, force re-authentication by deleting the token
                os.remove(TOKEN_PATH)
                return get_credentials(scopes)
        else:
            if not os.path.exists(CREDENTIALS_PATH):
                logging.critical(f"'{CREDENTIALS_PATH}' not found. Please download it from Google Cloud Console.")
                raise FileNotFoundError(f"'{CREDENTIALS_PATH}' not found.")
            
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, scopes)
            creds = flow.run_local_server(port=0)
            logging.info("Authentication successful. Token created.")
        
        # Save the credentials for the next run
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())
            
    return creds
