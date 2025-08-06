# config/settings.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Google API Scopes ---
# Define the permissions your application needs.
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/calendar'
]

# --- Gmail Configuration ---
# This query tells Gmail which emails to fetch.
# Customize this to match your foreclosure notice emails.
# Example: 'from:notifications@foreclosureservice.com subject:"New Foreclosure Notice" is:unread'
GMAIL_QUERY = os.getenv('GMAIL_SEARCH_QUERY', 'subject:"Foreclosure Notice"')

# --- Google Sheets Configuration ---
# The ID of the spreadsheet where data will be stored.
# You can find this in the URL of your Google Sheet:
# https://docs.google.com/spreadsheets/d/THIS_IS_THE_ID/edit
SHEET_ID = os.getenv('SPREADSHEET_ID')
if not SHEET_ID:
    raise ValueError("SPREADSHEET_ID is not set in the .env file.")

# --- Google Calendar Configuration ---
# The ID of the calendar where events will be created.
# For your primary calendar, this is usually your email address.
# For a secondary calendar, find it in the calendar's settings.
CALENDAR_ID = os.getenv('CALENDAR_ID', 'primary')
