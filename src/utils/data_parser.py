# src/utils/data_parser.py
import re
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List

@dataclass
class ForeclosureData:
    """
    A structured dataclass to hold parsed foreclosure information.
    """
    property_address: Optional[str] = None
    auction_datetime: Optional[datetime] = None
    case_number: Optional[str] = None
    attorney_name: Optional[str] = None
    attorney_phone: Optional[str] = None
    original_loan_amount: Optional[float] = None
    assessed_value: Optional[float] = None
    date_added: str = field(default_factory=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    def to_sheet_row(self) -> List[any]:
        """Converts the dataclass instance to a list for a Google Sheet row."""
        return [
            self.property_address,
            self.auction_datetime.strftime('%Y-%m-%d') if self.auction_datetime else None,
            self.auction_datetime.strftime('%I:%M %p') if self.auction_datetime else None,
            self.case_number,
            self.attorney_name,
            self.attorney_phone,
            self.original_loan_amount,
            self.assessed_value,
            self.date_added
        ]

class DataParser:
    """
    Parses unstructured text from emails to extract foreclosure data using regex.
    NOTE: These regex patterns are examples and MUST be adapted to your specific email formats.
    """
    def __init__(self):
        # --- IMPORTANT ---
        # The regex patterns below are generic. You will need to inspect your actual
        # email content and adjust these patterns meticulously.
        self.patterns = {
            'property_address': re.compile(r"Property Address:\s*(.*)"),
            'auction_date': re.compile(r"Auction Date:\s*(\w+\s+\d{1,2},\s+\d{4})"),
            'auction_time': re.compile(r"Auction Time:\s*(\d{1,2}:\d{2}\s*(?:AM|PM))"),
            'case_number': re.compile(r"Case (?:No\.?|Number):\s*(\d{4}-\d{5,6})"),
            'attorney_name': re.compile(r"Attorney for Plaintiff:\s*(.*)"),
            'attorney_phone': re.compile(r"Attorney Phone:\s*(\(\d{3}\)\s*\d{3}-\d{4})"),
            'original_loan_amount': re.compile(r"Original Loan Amount:\s*\$([\d,]+\.\d{2})"),
            'assessed_value': re.compile(r"Assessed Value:\s*\$([\d,]+\.\d{2})"),
        }

    def _extract(self, pattern: re.Pattern, text: str) -> Optional[str]:
        """Helper to run a regex pattern and return the first group match."""
        match = pattern.search(text)
        return match.group(1).strip() if match else None

    def parse(self, text: str) -> Optional[ForeclosureData]:
        """
        Parses the email body text and populates a ForeclosureData object.
        Args:
            text: The plain text content of the email.
        Returns:
            A populated ForeclosureData object or None if essential data (like case number) is missing.
        """
        data = ForeclosureData()
        data.property_address = self._extract(self.patterns['property_address'], text)
        data.case_number = self._extract(self.patterns['case_number'], text)
        data.attorney_name = self._extract(self.patterns['attorney_name'], text)
        data.attorney_phone = self._extract(self.patterns['attorney_phone'], text)

        # Handle numeric fields
        loan_amount_str = self._extract(self.patterns['original_loan_amount'], text)
        if loan_amount_str:
            data.original_loan_amount = float(loan_amount_str.replace(',', ''))

        assessed_value_str = self._extract(self.patterns['assessed_value'], text)
        if assessed_value_str:
            data.assessed_value = float(assessed_value_str.replace(',', ''))
            
        # Combine date and time into a datetime object
        date_str = self._extract(self.patterns['auction_date'], text)
        time_str = self._extract(self.patterns['auction_time'], text)
        if date_str and time_str:
            try:
                datetime_str = f"{date_str} {time_str}"
                data.auction_datetime = datetime.strptime(datetime_str, '%B %d, %Y %I:%M %p')
            except ValueError as e:
                logging.error(f"Could not parse date/time string '{datetime_str}': {e}")

        # A case number is essential for tracking. If it's not found, the parse fails.
        if not data.case_number:
            logging.warning("Parsing failed: Case Number not found in email content.")
            return None

        logging.info(f"Successfully parsed data for case number: {data.case_number}")
        return data
