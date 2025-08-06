import logging
from datetime import datetime, timedelta
from googleapiclient.discovery import build, Resource
from google.oauth2.credentials import Credentials
from .utils.data_parser import ForeclosureData

class CalendarManager:
    """
    Manages interactions with the Google Calendar API
    """
    def __init__(self, creds: Credentials, calendar_id: str):
        """
        Initializes the CalendarManager.
        Args:
            creds: Authorized Google OAuth2 credentials.
            calendar_id: The ID of the Google Calendar.
        """
        self.service: Resource = build('calendar', 'v3', credentials=creds)
        self.calendar_id = calendar_id
    
    def create_event_for_notice(self, notice: ForeclosureData):
        """
        Creates a Google Calendar event for a foreclosure auction.
        Args:
            notice: A ForeclosureData object containing auction details.
        """
        if not notice.auction_datetime:
            logging.warning(f"Cannot create event for case {notice.case_number} due to missing auction date/time.")
            return
        
        event_start_dt = notice.auction_datetime
        event_end_dt = event_start_dt + timedelta(hours=1)

        event = {
            'summary': f'Foreclosure Auction: {notice.property_address}',
            'location': notice.property_address,
            'description': (
                f"Case Number: {notice.case_number}\n"
                f"Attorney: {notice.attorney_name} ({notice.attorney_phone})\n"
                f"Original Loan: ${notice.original_loan_amount:,.2f}\n"
                f"Assessed Value: ${notice.assessed_value:,.2f}"
            ),
            'start': {
                'dateTime': event_start_dt.isoformat(),
                'timeZone': 'Asia/Manila', # IMPORTANT: Adjust to your timezone
            },
            'end': {
                'dateTime': event_end_dt.isoformat(),
                'timeZone': 'Asia/Manila', # IMPORTANT: Adjust to your timezone
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60}, # 1 day before
                    {'method': 'popup', 'minutes': 60},     # 1 hour before
                ],
            },
        }

        try:
            created_event = self.service.events().insert(
                calendarId=self.calendar_id,
                body=event
            ).execute()
            logging.info(f"Event created for case {notice.case_number}: {created_event.get('htmlLink')}")
        except Exception as e:
            logging.error(f"Failed to create calendar event for case {notice.case_number}: {e}")