import base64
import logging
from typing import List, Dict, Any
from googleapiclient.discovery import build, Resource
from google.oauth2.credentials import Credentials

from .utils.data_parser import DataParser, ForeclosureData

class EmailProcessor:
    """
    Handles fetching and processing of emails from the Gmail API.
    """
    def __init__(self, creds: Credentials):
        """
        Initializes the EmailProcessor with Google API credentials.
        Args:
            creds: Authorized Google OAuth2 credentials.
        """
        self.service: Resource = build('gmail', 'v1', credentials=creds)
        self.parser = DataParser()

    def list_messages(self, query: str) -> List[Dict[str, Any]]:
        """
        Lists messages from the user's mailbox matching the given query.
        Args:
            query: The query string to filter messages (e.g., 'from:someone@example.com is:unread').
        Returns:
            A list of message objects.
        """
        try:
            response = self.service.users().messages().list(userId='me', q=query).execute()
            messages = response.get('messages', [])
            return messages
        except Exception as e:
            logging.error(f"Failed to list Gmail messages: {e}")
            return []

    def get_message_content(self, msg_id: str) -> str:
        """
        Retrieves the full content of a single email message.
        Args:
            msg_id: The ID of the message to retrieve.
        Returns:
            The decoded email body as a string, or an empty string if an error occurs.
        """
        try:
            message = self.service.users().messages().get(userId='me', id=msg_id, format='full').execute()
            payload = message.get('payload', {})
            parts = payload.get('parts', [])
            
            # Find the plain text part of the email
            for part in parts:
                if part['mimeType'] == 'text/plain':
                    data = part['body']['data']
                    # Decode from base64url
                    decoded_data = base64.urlsafe_b64decode(data.encode('ASCII')).decode('utf-8')
                    return decoded_data
            
            # Fallback for simple emails with no parts
            if 'data' in payload.get('body', {}):
                data = payload['body']['data']
                decoded_data = base64.urlsafe_b64decode(data.encode('ASCII')).decode('utf-8')
                return decoded_data

            logging.warning(f"Could not find text/plain part for message ID: {msg_id}")
            return ""

        except Exception as e:
            logging.error(f"Failed to get message content for ID {msg_id}: {e}")
            return ""

    def process_emails(self, query: str) -> List[ForeclosureData]:
        """
        Fetches emails based on a query, parses them, and returns structured data.
        Args:
            query: The Gmail search query.
        Returns:
            A list of ForeclosureData objects.
        """
        messages = self.list_messages(query)
        if not messages:
            logging.info("No messages found matching the query.")
            return []

        parsed_data_list = []
        for message in messages:
            msg_id = message['id']
            logging.info(f"Processing message ID: {msg_id}")
            content = self.get_message_content(msg_id)
            if content:
                parsed_data = self.parser.parse(content)
                if parsed_data and parsed_data.case_number:
                    parsed_data_list.append(parsed_data)
                else:
                    logging.warning(f"Failed to parse required data from message ID: {msg_id}")
        
        return parsed_data_list