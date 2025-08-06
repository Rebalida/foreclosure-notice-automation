# tests/test_data_parser.py
import pytest
from datetime import datetime
from src.utils.data_parser import DataParser, ForeclosureData

# This is a sample email body. You should replace this with a real, anonymized
# example of the emails you will be processing.
SAMPLE_EMAIL_BODY = """
Hello,

This is a notice of a new foreclosure auction.

Property Address: Sta. Barbara Iba, Zambales
Auction Date: August 10, 2025
Auction Time: 1:00 AM
Case No.: 2025-78910

Attorney for Plaintiff: Smith & Jones Law Firm
Attorney Phone: (123) 456-7890

Financial Details:
Original Loan Amount: $350,000.00
Assessed Value: $410,000.00

Please review the attached documents.
"""

@pytest.fixture
def parser():
    """Pytest fixture to create a DataParser instance for tests."""
    return DataParser()

def test_full_parse_success(parser):
    """
    Tests that a complete, well-formatted email body is parsed correctly.
    """
    data = parser.parse(SAMPLE_EMAIL_BODY)
    
    assert isinstance(data, ForeclosureData)
    assert data.property_address == "123 Main St, Anytown, USA 12345"
    assert data.case_number == "2023-123456"
    assert data.attorney_name == "Smith & Jones Law Firm"
    assert data.attorney_phone == "(123) 456-7890"
    assert data.original_loan_amount == 350000.00
    assert data.assessed_value == 410000.00
    assert data.auction_datetime == datetime(2023, 10, 26, 10, 0)

def test_missing_case_number_fails_parsing(parser):
    """
    Tests that parsing returns None if the essential case number is missing.
    """
    email_without_case_number = SAMPLE_EMAIL_BODY.replace("Case No.: 2023-123456", "")
    data = parser.parse(email_without_case_number)
    assert data is None

def test_partial_data_parsing(parser):
    """
    Tests that parsing still works and returns a dataclass even if non-essential fields are missing.
    """
    partial_email = """
    Property Address: 456 Oak Ave, Sometown, USA 54321
    Case No.: 2023-654321
    """
    data = parser.parse(partial_email)
    
    assert isinstance(data, ForeclosureData)
    assert data.property_address == "456 Oak Ave, Sometown, USA 54321"
    assert data.case_number == "2023-654321"
    assert data.attorney_name is None
    assert data.original_loan_amount is None
    assert data.auction_datetime is None

def test_to_sheet_row_format(parser):
    """
    Tests that the to_sheet_row method formats the data correctly for Google Sheets.
    """
    data = parser.parse(SAMPLE_EMAIL_BODY)
    row = data.to_sheet_row()
    
    assert row[0] == "123 Main St, Anytown, USA 12345"
    assert row[1] == "2023-10-26"  # Date format
    assert row[2] == "10:00 AM"    # Time format
    assert row[3] == "2023-123456"
    assert isinstance(row[8], str) # Date Added is a string
