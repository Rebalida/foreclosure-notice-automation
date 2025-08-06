import schedule
import time
import logging
from datetime import datetime
from typing import List

from src.email_processor import EmailProcessor
from src.sheets_manager import SheetsManager
from src.calendar_manager import CalendarManager
from src.utils.data_parser import ForeclosureData
from config.settings import GMAIL_QUERY, SCOPES, SHEET_ID, CALENDAR_ID
from src.utils.auth import get_credentials

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("logs/app.log"),
                        logging.StreamHandler()
                    ])

def job():
    """
    The main job function to be scheduled.
    - Authenticates with Google APIs.
    - Fetches and processes foreclosure emails.
    - Adds new records to Google Sheets.
    - Creates Google Calendar events for new auctions.
    """
    logging.info("Starting foreclosure automation job...")
    try:
        # Authenticate and get Google API service objects
        creds = get_credentials(SCOPES)
        email_processor = EmailProcessor(creds)
        sheets_manager = SheetsManager(creds, SHEET_ID)
        calendar_manager = CalendarManager(creds, CALENDAR_ID)

        # Fetch and parse emails
        logging.info(f"Fetching emails with query: '{GMAIL_QUERY}'")
        parsed_data: List[ForeclosureData] = email_processor.process_emails(query=GMAIL_QUERY)

        if not parsed_data:
            logging.info("No new foreclosure notices found.")
            logging.info("Job finished successfully.")
            return

        logging.info(f"Successfully parsed {len(parsed_data)} new foreclosure notices.")

        # Get existing case numbers from Google Sheets to prevent duplicates
        existing_case_numbers = sheets_manager.get_existing_case_numbers()
        logging.info(f"Found {len(existing_case_numbers)} existing case numbers in the sheet.")

        # Filter out already processed notices
        new_notices = [notice for notice in parsed_data if notice.case_number not in existing_case_numbers]

        if not new_notices:
            logging.info("All parsed notices have already been processed.")
            logging.info("Job finished successfully.")
            return

        logging.info(f"Found {len(new_notices)} new notices to process.")

        # Add new notices to Google Sheets
        sheets_manager.add_records(new_notices)

        # Create calendar events for the new notices
        for notice in new_notices:
            calendar_manager.create_event_for_notice(notice)

        logging.info("Successfully added new records to Sheets and created calendar events.")
        logging.info("Job finished successfully.")

    except Exception as e:
        logging.critical(f"A critical error occurred in the main job: {e}", exc_info=True)

def main():
    """
    Main function to run the job immediately and then schedule it.
    """
    logging.info("Foreclosure Automation System started.")
    
    # Run the job once immediately on startup
    job()

    # Schedule the job to run daily
    schedule.every().day.at("09:00").do(job)
    logging.info("Job scheduled to run daily at 9:00 AM.")

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
