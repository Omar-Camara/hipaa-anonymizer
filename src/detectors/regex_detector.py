"""
Tier 1 Regex Detector for HIPAA PHI Anonymization.

This module provides deterministic pattern matching for common PHI identifiers
including SSN, phone numbers, email addresses, IP addresses, and URLs.
"""

import re
from typing import List, Dict, Pattern, Optional, Any


class RegexDetector:
    """
    Detects PHI using compiled regex patterns for deterministic identifiers.
    
    Patterns are compiled once at initialization for optimal performance.
    All detection methods return results in a standardized format with
    type, value, start, end positions, and confidence score.
    """
    
    def __init__(self):
        """Initialize and compile all regex patterns."""
        # SSN patterns: 123-45-6789, 123 45 6789, 123456789
        # Excludes invalid patterns like 000-xx-xxxx, 123-00-xxxx, 123-45-0000
        # Note: 666 and 900-999 are reserved, but we'll be lenient for detection
        self._ssn_pattern = re.compile(
            r'\b(?!000)(?!666)\d{3}[- ]?(?!00)\d{2}[- ]?(?!0000)\d{4}\b'
        )
        
        # Phone number patterns
        # US Formats: (123) 456-7890, 123-456-7890, 123.456.7890, 1234567890
        # With optional country code: +1-123-456-7890, 1-123-456-7890
        # International formats: +44 20 1234 5678, +33 1 23 45 67 89, +49 30 12345678
        # Pattern handles both US and international formats
        us_phone = r'(?:\+?1[-.\s]?)?(?:\(\d{3}\)\s?|\d{3}[-.\s]?)\d{3}[-.\s]?\d{4}'
        # International: +country code followed by 7-15 digits with optional separators
        intl_phone = r'\+\d{1,3}[-.\s]?(?:\d[-.\s]?){7,15}\d'
        self._phone_pattern = re.compile(
            r'(?<!\d)(?:' + us_phone + r'|' + intl_phone + r')(?!\d)'
        )
        
        # Email pattern: standard RFC 5322 compliant
        self._email_pattern = re.compile(
            r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'
        )
        
        # IPv4 pattern: 192.168.1.1
        self._ipv4_pattern = re.compile(
            r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
            r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
        )
        
        # IPv6 pattern: 2001:0db8:85a3:0000:0000:8a2e:0370:7334
        # Simplified to catch common formats
        self._ipv6_pattern = re.compile(
            r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b|'
            r'\b::(?:[0-9a-fA-F]{1,4}:){0,6}[0-9a-fA-F]{1,4}\b|'
            r'\b(?:[0-9a-fA-F]{1,4}:){1,7}::\b|'
            r'\b(?:[0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}\b'
        )
        
        # URL pattern: http://, https://, www., ftp://, etc.
        self._url_pattern = re.compile(
            r'\b(?:https?|ftp)://[^\s<>"{}|\\^`\[\]]+|'
            r'\bwww\.[^\s<>"{}|\\^`\[\]]+\.[a-zA-Z]{2,}\b'
        )
        
        # Date patterns (MM/DD/YYYY, MM-DD-YYYY, MM.DD.YYYY, etc.)
        # Catches dates like 08/20/1955, 03/01/2023
        # Excludes years only (like "2024") and age expressions
        self._date_pattern = re.compile(
            r'\b(?:0?[1-9]|1[0-2])[/\-\.](?:0?[1-9]|[12][0-9]|3[01])[/\-\.](?:19|20)\d{2}\b'
        )
        
        # Zip code patterns (US)
        # Formats: 12345, 12345-6789, or state + zip: MA 02118, CA 90210
        # 5-digit zip codes
        zip_5 = r'\b\d{5}\b'
        # 5+4 format: 12345-6789
        zip_9 = r'\b\d{5}-\d{4}\b'
        # State + zip: MA 02118, CA 90210-1234
        state_zip = r'\b[A-Z]{2}\s+\d{5}(?:-\d{4})?\b'
        self._zip_pattern = re.compile(
            r'(?:' + zip_9 + r'|' + state_zip + r'|' + zip_5 + r')'
        )
        
        # Medical Record Number patterns
        # Formats: MR-123456, MRN-789, Medical Record #123, MR#456, MRN: 789
        self._mrn_pattern = re.compile(
            r'\b(?:MRN?|Medical\s+Record\s*#?)[\s:.-]+?\d{3,12}\b',
            re.IGNORECASE
        )
        
        # Health Plan Beneficiary Number patterns
        # Formats: Member ID: 123456, Policy #789, Group #456, Ins ID: 123
        # Insurance member IDs, policy numbers, group numbers
        self._health_plan_pattern = re.compile(
            r'\b(?:Member\s+ID|Policy\s*#?|Group\s*#?|Ins(urance)?\s+ID|Beneficiary\s+ID)[\s:.-]+'
            r'[A-Z0-9]{3,20}\b',
            re.IGNORECASE
        )
        
        # Account Number patterns
        # Formats: Account #123456, Acct: 789, Account Number: 456789
        # Generic numeric sequences in account contexts
        self._account_pattern = re.compile(
            r'\b(?:Account\s*#?|Acct\.?\s*#?|Account\s+Number)[\s:.-]?\d{3,20}\b',
            re.IGNORECASE
        )
        
        # Fax number patterns (similar to phone but with fax keyword context)
        # Look for "fax" keyword near phone number pattern
        # Also standalone fax patterns: Fax: (123) 456-7890
        fax_us_phone = r'(?:\+?1[-.\s]?)?(?:\(\d{3}\)\s?|\d{3}[-.\s]?)\d{3}[-.\s]?\d{4}'
        self._fax_pattern = re.compile(
            r'\b(?:Fax|F\.?)[\s:]+' + fax_us_phone + r'|' +
            r'(?:' + fax_us_phone + r')\s*(?:fax|f\.?)\b',
            re.IGNORECASE
        )
        
        # Certificate/License Number patterns
        # Driver's license: DL-1234567, License #789, DL# 456
        # Medical license: MD-12345, License #789
        # Professional licenses vary by state, use common patterns
        self._license_pattern = re.compile(
            r'\b(?:DL|License|Lic\.?|Cert\.?|Certificate)[\s#:.-]?[A-Z0-9]{4,15}\b',
            re.IGNORECASE
        )
        
        # Vehicle Identifier Number (VIN) pattern
        # VINs are exactly 17 alphanumeric characters (excluding I, O, Q to avoid confusion)
        # Format: 17 characters, typically uppercase
        self._vin_pattern = re.compile(
            r'\b(?:VIN|Vehicle\s+ID|Vehicle\s+Identifier)[\s:.-]?[A-HJ-NPR-Z0-9]{17}\b|'
            r'\b[A-HJ-NPR-Z0-9]{17}\b(?=\s*(?:VIN|vehicle|car|truck|auto))?',
            re.IGNORECASE
        )
        
        # License Plate patterns (US state formats)
        # Common formats: ABC-1234, ABC 1234, ABC1234, 123-ABC, 123 ABC, 123ABC
        # State abbreviations: 2-3 letters followed by numbers, or numbers followed by letters
        # Also catches state abbreviation + plate: CA ABC123, NY 123-ABC
        # Only match with explicit keywords or state abbreviation to avoid false positives
        plate_format1 = r'[A-Z]{2,3}[- ]?\d{2,4}[A-Z]{0,2}'  # ABC-1234, ABC1234 (at least 2 letters, 2 digits)
        plate_format2 = r'\d{2,4}[- ]?[A-Z]{2,3}'  # 123-ABC, 123ABC (at least 2 digits, 2 letters)
        # State plate: require at least one digit in the plate number
        state_plate = r'\b[A-Z]{2}\s+(?=[A-Z0-9]*\d)[A-Z0-9]{2,7}(?:[- ]?[A-Z0-9]{1,7})?\b'  # CA ABC123, NY 123-ABC
        # Only match with explicit keywords (License Plate, Plate #, Tag #) or state abbreviation
        self._license_plate_pattern = re.compile(
            r'\b(?:License\s+Plate|Plate\s*#?|Tag\s*#?)[\s:.-]+' +
            r'(?:' + plate_format1 + r'|' + plate_format2 + r')|' +
            state_plate,
            re.IGNORECASE
        )
        
        # Device Identifier patterns
        # UDI (Unique Device Identifier) formats: typically alphanumeric with hyphens
        # Common formats: (01)12345678901234, 12345678901234, UDI-12345678901234
        # Serial numbers: SN-123456, Serial #789, S/N: ABC123
        # Medical device IDs: MDI-123456, Device ID: ABC123
        # Require explicit keywords or longer sequences to avoid false positives
        udi_pattern = r'(?:\(01\))?[A-Z0-9]{8,20}(?:[- ]?[A-Z0-9]{4,8})*'
        serial_pattern = r'(?:SN|Serial\s*#?|S/N|S\.N\.)[\s:.-]+[A-Z0-9]{4,20}'
        device_id_pattern = r'(?:Device\s+ID|MDI|Device\s+Serial)[\s:.-]+[A-Z0-9]{4,20}'
        self._device_identifier_pattern = re.compile(
            r'\b(?:UDI|Unique\s+Device\s+Identifier)[\s:.-]+' + udi_pattern + r'|' +
            r'\b' + udi_pattern + r'(?=\s*(?:UDI|device))|' +
            r'\b' + serial_pattern + r'|' +
            r'\b' + device_id_pattern + r'',
            re.IGNORECASE
        )
        
        # Biometric Identifier patterns
        # Text representations of biometric data (rare in text)
        # Fingerprint patterns: FP-123456, Fingerprint ID: ABC123
        # Voiceprint patterns: Voiceprint ID: 123456, VP-ABC123
        # Retina/Iris patterns: Retina ID: 123456, Iris ID: ABC123
        # DNA patterns: DNA ID: 123456, DNA Sequence: ABC123
        # Biometric template IDs: Biometric ID: 123456, Bio ID: ABC123
        biometric_patterns = [
            r'(?:Fingerprint|FP|Finger\s+Print)[\s:.-]+(?:ID|Identifier)[\s:.-]+[A-Z0-9]{3,20}',
            r'(?:Fingerprint|FP|Finger\s+Print)[\s:.-]+[A-Z0-9]{3,20}',
            r'(?:Voiceprint|VP|Voice\s+Print)[\s:.-]+(?:ID|Identifier)[\s:.-]+[A-Z0-9]{3,20}',
            r'(?:Voiceprint|VP|Voice\s+Print)[\s:.-]+[A-Z0-9]{3,20}',
            r'(?:Retina|Iris|Eye\s+Scan)[\s:.-]+(?:ID|Identifier)[\s:.-]+[A-Z0-9]{3,20}',
            r'(?:Retina|Iris|Eye\s+Scan)[\s:.-]+[A-Z0-9]{3,20}',
            r'(?:DNA|Genetic)[\s:.-]+(?:ID|Identifier|Sequence)[\s:.-]+[A-Z0-9]{3,30}',
            r'(?:DNA|Genetic)[\s:.-]+[A-Z0-9]{3,30}',
            r'(?:Biometric|Bio)[\s:.-]+(?:ID|Identifier|Template)[\s:.-]+[A-Z0-9]{3,20}',
            r'(?:Biometric|Bio)[\s:.-]+[A-Z0-9]{3,20}',
        ]
        self._biometric_pattern = re.compile(
            r'\b(?:' + '|'.join(biometric_patterns) + r')\b',
            re.IGNORECASE
        )
    
    def detect_all(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect all PHI types in the given text.
        
        Args:
            text: Input text to scan for PHI identifiers.
            
        Returns:
            List of detection dictionaries, each containing:
            - type: str - Type of PHI detected (ssn, phone, email, ip, url)
            - value: str - The detected value
            - start: int - Start position in text
            - end: int - End position in text
            - confidence: float - Confidence score (1.0 for regex)
        """
        results = []
        results.extend(self.detect_ssn(text))
        results.extend(self.detect_phone(text))
        results.extend(self.detect_email(text))
        results.extend(self.detect_ip(text))
        results.extend(self.detect_url(text))
        results.extend(self.detect_mrn(text))
        results.extend(self.detect_health_plan(text))
        results.extend(self.detect_account(text))
        results.extend(self.detect_fax(text))
        results.extend(self.detect_license(text))
        results.extend(self.detect_date(text))
        results.extend(self.detect_zip(text))
        results.extend(self.detect_vin(text))
        results.extend(self.detect_license_plate(text))
        results.extend(self.detect_device_identifier(text))
        results.extend(self.detect_biometric(text))
        
        # Sort by start position for consistent ordering
        results.sort(key=lambda x: x['start'])
        return results
    
    def detect_ssn(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect Social Security Numbers in the text.
        
        Supports formats:
        - 123-45-6789
        - 123 45 6789
        - 123456789
        
        Args:
            text: Input text to scan for SSNs.
            
        Returns:
            List of detection dictionaries with SSN matches.
        """
        results = []
        for match in self._ssn_pattern.finditer(text):
            # Normalize the SSN format for consistency
            ssn_value = match.group(0)
            # Remove spaces and ensure dashes are consistent
            normalized = re.sub(r'[\s-]', '-', ssn_value) if '-' in ssn_value or ' ' in ssn_value else ssn_value
            
            results.append({
                'type': 'ssn',
                'value': normalized,
                'start': match.start(),
                'end': match.end(),
                'confidence': 1.0
            })
        return results
    
    def detect_phone(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect phone numbers in the text.
        
        Supports formats:
        - (123) 456-7890
        - 123-456-7890
        - 123.456.7890
        - 1234567890
        - +1-123-456-7890
        - 1-123-456-7890
        
        Args:
            text: Input text to scan for phone numbers.
            
        Returns:
            List of detection dictionaries with phone number matches.
        """
        results = []
        for match in self._phone_pattern.finditer(text):
            phone_value = match.group(0)
            results.append({
                'type': 'phone',
                'value': phone_value,
                'start': match.start(),
                'end': match.end(),
                'confidence': 1.0
            })
        return results
    
    def detect_email(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect email addresses in the text.
        
        Args:
            text: Input text to scan for email addresses.
            
        Returns:
            List of detection dictionaries with email matches.
        """
        results = []
        for match in self._email_pattern.finditer(text):
            email_value = match.group(0)
            results.append({
                'type': 'email',
                'value': email_value,
                'start': match.start(),
                'end': match.end(),
                'confidence': 1.0
            })
        return results
    
    def detect_ip(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect IP addresses (IPv4 and IPv6) in the text.
        
        Args:
            text: Input text to scan for IP addresses.
            
        Returns:
            List of detection dictionaries with IP address matches.
        """
        results = []
        
        # Check IPv4
        for match in self._ipv4_pattern.finditer(text):
            ip_value = match.group(0)
            results.append({
                'type': 'ip',
                'value': ip_value,
                'start': match.start(),
                'end': match.end(),
                'confidence': 1.0
            })
        
        # Check IPv6
        for match in self._ipv6_pattern.finditer(text):
            ip_value = match.group(0)
            results.append({
                'type': 'ip',
                'value': ip_value,
                'start': match.start(),
                'end': match.end(),
                'confidence': 1.0
            })
        
        return results
    
    def detect_url(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect URLs in the text.
        
        Supports:
        - http://example.com
        - https://example.com
        - ftp://example.com
        - www.example.com
        
        Args:
            text: Input text to scan for URLs.
            
        Returns:
            List of detection dictionaries with URL matches.
        """
        results = []
        for match in self._url_pattern.finditer(text):
            url_value = match.group(0)
            results.append({
                'type': 'url',
                'value': url_value,
                'start': match.start(),
                'end': match.end(),
                'confidence': 1.0
            })
        return results
    
    def detect_mrn(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect Medical Record Numbers in the text.
        
        Supports formats:
        - MR-123456
        - MRN-789
        - Medical Record #123
        - MR#456
        - MRN: 789
        
        Args:
            text: Input text to scan for MRNs.
            
        Returns:
            List of detection dictionaries with MRN matches.
        """
        results = []
        for match in self._mrn_pattern.finditer(text):
            mrn_value = match.group(0)
            results.append({
                'type': 'medical_record_number',
                'value': mrn_value,
                'start': match.start(),
                'end': match.end(),
                'confidence': 1.0
            })
        return results
    
    def detect_health_plan(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect Health Plan Beneficiary Numbers in the text.
        
        Supports formats:
        - Member ID: 123456
        - Policy #789
        - Group #456
        - Ins ID: ABC123
        
        Args:
            text: Input text to scan for health plan numbers.
            
        Returns:
            List of detection dictionaries with health plan number matches.
        """
        results = []
        for match in self._health_plan_pattern.finditer(text):
            plan_value = match.group(0)
            results.append({
                'type': 'health_plan_beneficiary_number',
                'value': plan_value,
                'start': match.start(),
                'end': match.end(),
                'confidence': 1.0
            })
        return results
    
    def detect_account(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect Account Numbers in the text.
        
        Supports formats:
        - Account #123456
        - Acct: 789
        - Account Number: 456789
        
        Args:
            text: Input text to scan for account numbers.
            
        Returns:
            List of detection dictionaries with account number matches.
        """
        results = []
        for match in self._account_pattern.finditer(text):
            account_value = match.group(0)
            results.append({
                'type': 'account_number',
                'value': account_value,
                'start': match.start(),
                'end': match.end(),
                'confidence': 1.0
            })
        return results
    
    def detect_fax(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect Fax Numbers in the text.
        
        Supports formats:
        - Fax: (123) 456-7890
        - (123) 456-7890 fax
        - F: 123-456-7890
        
        Args:
            text: Input text to scan for fax numbers.
            
        Returns:
            List of detection dictionaries with fax number matches.
        """
        results = []
        for match in self._fax_pattern.finditer(text):
            fax_value = match.group(0)
            results.append({
                'type': 'fax_number',
                'value': fax_value,
                'start': match.start(),
                'end': match.end(),
                'confidence': 1.0
            })
        return results
    
    def detect_license(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect Certificate/License Numbers in the text.
        
        Supports formats:
        - DL-1234567
        - License #789
        - DL# 456
        - MD-12345 (medical license)
        
        Args:
            text: Input text to scan for license numbers.
            
        Returns:
            List of detection dictionaries with license number matches.
        """
        results = []
        for match in self._license_pattern.finditer(text):
            license_value = match.group(0)
            results.append({
                'type': 'certificate_license_number',
                'value': license_value,
                'start': match.start(),
                'end': match.end(),
                'confidence': 1.0
            })
        return results
    
    def detect_date(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect date patterns in MM/DD/YYYY format.
        
        Supports formats:
        - 08/20/1955
        - 03/01/2023
        - 12-31-2024
        - 1.15.2024
        
        Args:
            text: Input text to scan for dates.
            
        Returns:
            List of detection dictionaries with date matches.
        """
        results = []
        for match in self._date_pattern.finditer(text):
            date_value = match.group(0)
            results.append({
                'type': 'date',
                'value': date_value,
                'start': match.start(),
                'end': match.end(),
                'confidence': 1.0,
                'source': 'regex'
            })
        return results
    
    def detect_zip(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect US zip codes in the text.
        
        Supports formats:
        - 12345 (5-digit)
        - 12345-6789 (5+4 format)
        - MA 02118 (state + zip)
        - CA 90210-1234 (state + zip+4)
        
        Args:
            text: Input text to scan for zip codes.
            
        Returns:
            List of detection dictionaries with zip code matches.
        """
        results = []
        for match in self._zip_pattern.finditer(text):
            zip_value = match.group(0)
            results.append({
                'type': 'zip_code',
                'value': zip_value,
                'start': match.start(),
                'end': match.end(),
                'confidence': 1.0,
                'source': 'regex'
            })
        return results
    
    def detect_vin(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect Vehicle Identification Numbers (VINs) in the text.
        
        Supports formats:
        - VIN: 1HGBH41JXMN109186
        - Vehicle ID: 1HGBH41JXMN109186
        - 1HGBH41JXMN109186 (standalone, 17 alphanumeric chars)
        
        Args:
            text: Input text to scan for VINs.
            
        Returns:
            List of detection dictionaries with VIN matches.
        """
        results = []
        for match in self._vin_pattern.finditer(text):
            vin_value = match.group(0)
            # Extract just the VIN if it's part of a longer match
            vin_match = re.search(r'[A-HJ-NPR-Z0-9]{17}', vin_value, re.IGNORECASE)
            if vin_match:
                vin_value = vin_match.group(0).upper()
            results.append({
                'type': 'vehicle_identifier',
                'value': vin_value,
                'start': match.start(),
                'end': match.end(),
                'confidence': 1.0,
                'source': 'regex'
            })
        return results
    
    def detect_license_plate(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect license plate numbers in the text.
        
        Supports formats:
        - ABC-1234, ABC 1234, ABC1234
        - 123-ABC, 123 ABC, 123ABC
        - CA ABC123, NY 123-ABC
        - License Plate: ABC123
        - Plate #: 123ABC
        
        Args:
            text: Input text to scan for license plates.
            
        Returns:
            List of detection dictionaries with license plate matches.
        """
        results = []
        for match in self._license_plate_pattern.finditer(text):
            plate_value = match.group(0)
            results.append({
                'type': 'vehicle_identifier',
                'value': plate_value,
                'start': match.start(),
                'end': match.end(),
                'confidence': 1.0,
                'source': 'regex'
            })
        return results
    
    def detect_device_identifier(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect device identifiers and serial numbers in the text.
        
        Supports formats:
        - UDI: (01)12345678901234
        - Serial #: 123456
        - SN-ABC123
        - Device ID: MDI-123456
        - Medical device serial numbers
        
        Args:
            text: Input text to scan for device identifiers.
            
        Returns:
            List of detection dictionaries with device identifier matches.
        """
        results = []
        for match in self._device_identifier_pattern.finditer(text):
            device_value = match.group(0)
            results.append({
                'type': 'device_identifier',
                'value': device_value,
                'start': match.start(),
                'end': match.end(),
                'confidence': 1.0,
                'source': 'regex'
            })
        return results
    
    def detect_biometric(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect biometric identifiers in the text.
        
        Supports formats:
        - Fingerprint ID: 123456
        - FP-ABC123
        - Voiceprint ID: 123456
        - Retina ID: ABC123
        - DNA ID: 123456
        - Biometric ID: ABC123
        
        Args:
            text: Input text to scan for biometric identifiers.
            
        Returns:
            List of detection dictionaries with biometric identifier matches.
        """
        results = []
        for match in self._biometric_pattern.finditer(text):
            biometric_value = match.group(0)
            results.append({
                'type': 'biometric_identifier',
                'value': biometric_value,
                'start': match.start(),
                'end': match.end(),
                'confidence': 1.0,
                'source': 'regex'
            })
        return results

