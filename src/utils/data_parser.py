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
            'property_address': re.compile(r"Property Address:\s*(.+?)(?:\n|$)", re.IGNORECASE | re.DOTALL),
            'auction_date': re.compile(r"Auction Date:\s*(.+?)(?:\n|$)", re.IGNORECASE),
            'auction_time': re.compile(r"Auction Time:\s*(.+?)(?:\n|$)", re.IGNORECASE),
            'case_number': re.compile(r"Case\s+No\.?\s*:\s*([^\s\n]+)", re.IGNORECASE),
            'attorney_name': re.compile(r"Attorney\s+for\s+Plaintiff:\s*(.+?)(?:\n|$)", re.IGNORECASE),
            'attorney_phone': re.compile(r"Attorney Phone:\s*(\(\d{3}\)\s*\d{3}-\d{4}|\d{3}-\d{3}-\d{4}|\d{3}\.\d{3}\.\d{4})", re.IGNORECASE),
            'original_loan_amount': re.compile(r"Original Loan Amount:\s*\$?([\d,]+\.?\d{0,2})", re.IGNORECASE),
            'assessed_value': re.compile(r"Assessed Value:\s*\$?([\d,]+\.?\d{0,2})", re.IGNORECASE),
        }

    def _extract(self, pattern: re.Pattern, text: str) -> Optional[str]:
        """Helper to run a regex pattern and return the first group match."""
        match = pattern.search(text)
        if match:
            result = match.group(1).strip()
            result = re.sub(r'[,.\s]+$', '', result)
            return result if result else None
        return None
    
    def _parse_datetime (self, date_str: str, time_str: str) -> Optional[datetime]:
        """
        Parse date and time strings into a datetime object
        """
        if not date_str or not time_str:
            return None
        
        try:
            date_str = date_str.strip()
            time_str = time_str.strip()

            date_formats = [
                '%B %d, %Y',
                '%b %d, %Y',
                '%m/%d/%Y',
                '%Y-%m-%d', 
            ]

            time_formats = [
                '%I:%M %p',
                '%H:%M',
            ]

            parsed_date = None
            for date_fmt in date_formats:
                try:
                    parsed_date = datetime.strptime(date_str, date_fmt)
                    break
                except ValueError:
                    continue
            
            if not parsed_date:
                logging.error(f"Could not parse date string: '{date_str}'")
                return None
            
            parsed_time = None
            for time_fmt in time_formats:
                try:
                    time_obj = datetime.strptime(time_str, time_fmt)
                    parsed_time = time_obj.time()
                    break
                except ValueError:
                    continue
            
            if not parsed_time:
                logging.error(f"Could not parse time string: '{time_str}'")
                return None

            return datetime.combine(parsed_date.date(), parsed_time)
        
        except Exception as e:
            logging.error(f"Error parsing datetime '{date_str} {time_str}': {e}")
            return None

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

        loan_amount_str = self._extract(self.patterns['original_loan_amount'], text)
        if loan_amount_str:
            try:
                clean_amount = loan_amount_str.replace(',', '')
                data.original_loan_amount = float(clean_amount)
            except ValueError as e:
               logging.error(f"Could not parse loan amount '{loan_amount_str}': {e}")
        
        assessed_value_str = self._extract(self.patterns['assessed_value'], text)
        if assessed_value_str:
            try:
                clean_value = assessed_value_str.replace(',', '')
                data.assessed_value = float(clean_value)
            except ValueError as e:
                logging.error(f"Could not parse assessed value '{assessed_value_str}': {e}")
        
        date_str = self._extract(self.patterns['auction_date'], text)
        time_str = self._extract(self.patterns['auction_time'], text)
        data.auction_datetime = self._parse_datetime(date_str, time_str)

        logging.debug(f"Extracted - Case: {data.case_number}, Address: {data.property_address}, Date: {date_str}, Time: {time_str}")

        if not data.case_number:
            logging.warning("Parsing failed: Case Number not found in email content.")
            logging.debug(f"Available text for case number matching: {text}")
            return None
        
        logging.info(f"Successfully parsed data for case number: {data.case_number}")
        return data

