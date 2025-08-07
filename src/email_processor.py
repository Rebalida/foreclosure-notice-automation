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
            
            # Function to extract text from a part
            def extract_text_from_part(part):
                mime_type = part.get('mimeType', '')
                body = part.get('body', {})
                
                if 'data' in body:
                    data = body['data']
                    try:
                        decoded_data = base64.urlsafe_b64decode(data.encode('ASCII')).decode('utf-8')
                        # If it's HTML, strip HTML tags (basic cleanup)
                        if mime_type == 'text/html':
                            import re
                            # Remove HTML tags and decode HTML entities
                            decoded_data = re.sub(r'<[^>]+>', '', decoded_data)
                            decoded_data = decoded_data.replace('&nbsp;', ' ').replace('&amp;', '&')
                        return decoded_data
                    except Exception as e:
                        logging.warning(f"Failed to decode part with mime type {mime_type}: {e}")
                        return ""
                return ""
            
            # Try to get text content in order of preference
            content = ""
            
            # Check if payload has parts (multipart email)
            parts = payload.get('parts', [])
            if parts:
                # Look for text/plain first, then text/html
                for part in parts:
                    mime_type = part.get('mimeType', '')
                    if mime_type == 'text/plain':
                        content = extract_text_from_part(part)
                        if content:
                            return content
                
                # If no text/plain found, try text/html
                for part in parts:
                    mime_type = part.get('mimeType', '')
                    if mime_type == 'text/html':
                        content = extract_text_from_part(part)
                        if content:
                            return content
                
                # Handle nested multipart (multipart/alternative, etc.)
                for part in parts:
                    if part.get('mimeType', '').startswith('multipart/'):
                        nested_parts = part.get('parts', [])
                        for nested_part in nested_parts:
                            nested_mime = nested_part.get('mimeType', '')
                            if nested_mime in ['text/plain', 'text/html']:
                                content = extract_text_from_part(nested_part)
                                if content:
                                    return content
            else:
                # Single part email (no parts array)
                content = extract_text_from_part(payload)
                if content:
                    return content

            logging.warning(f"Could not extract readable content from message ID: {msg_id}")
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