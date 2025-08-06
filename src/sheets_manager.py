import logging
from typing import List
from googleapiclient.discovery import build, Resource
from google.oauth2.credentials import Credentials
from .utils.data_parser import ForeclosureData

class SheetsManager:
    """
    Manages interactions with the Google Sheets API.
    """
    def __init__(self, creds: Credentials, spreadsheet_id: str):
        """
        Initializes the SheetsManager.
        Args:
            creds: Authorized Google OAuth2 credentials.
            spreadsheet_id: The ID of the Google Sheet.
        """
        self.service: Resource = build('sheets', 'v4', credentials=creds)
        self.spreadsheet_id = spreadsheet_id
        self.sheet = self.service.spreadsheets()
        self._ensure_header()

    def _ensure_header(self):
        """
        Ensures the sheet has the correct header row. Creates it if it doesn't exist.
        """
        try:
            # Check if the first row is empty or doesn't match the header
            result = self.sheet.values().get(spreadsheetId=self.spreadsheet_id, range='A1:Z1').execute()
            values = result.get('values', [])
            header = [
                "Property Address", "Auction Date", "Auction Time", "Case Number",
                "Attorney Name", "Attorney Phone", "Original Loan Amount", "Assessed Value",
                "Date Added"
            ]

            if not values or values[0] != header:
                logging.info("Header not found or incorrect. Writing new header to the sheet.")
                body = {'values': [header]}
                self.sheet.values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range='A1',
                    valueInputOption='USER_ENTERED',
                    body=body
                ).execute()
        except Exception as e:
            logging.error(f"Failed to ensure sheet header: {e}")
            raise

    def get_existing_case_numbers(self) -> List[str]:
        """
        Retrieves all existing case numbers from the sheet to prevent duplicates.
        Assumes 'Case Number' is in column D.
        Returns:
            A list of existing case numbers.
        """
        try:
            # Range 'D2:D' gets all values in column D starting from the second row
            result = self.sheet.values().get(
                spreadsheetId=self.spreadsheet_id,
                range='D2:D'
            ).execute()
            values = result.get('values', [])
            return [row[0] for row in values if row] # Flatten list and remove empty rows
        except Exception as e:
            logging.error(f"Failed to retrieve existing case numbers from sheet: {e}")
            return []

    def add_records(self, data: List[ForeclosureData]):
        """
        Appends new records to the Google Sheet.
        Args:
            data: A list of ForeclosureData objects to add.
        """
        if not data:
            return

        values = [d.to_sheet_row() for d in data]
        body = {'values': values}

        try:
            self.sheet.values().append(
                spreadsheetId=self.spreadsheet_id,
                range='A1', 
                valueInputOption='USER_ENTERED',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            logging.info(f"Successfully appended {len(values)} new records to the sheet.")
        except Exception as e:
            logging.error(f"Failed to append records to sheet: {e}")
