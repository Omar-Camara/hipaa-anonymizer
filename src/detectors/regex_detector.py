"""
Tier 1 Regex Detector for HIPAA PHI Anonymization.

This module provides deterministic pattern matching for common PHI identifiers
including SSN, phone numbers, email addresses, IP addresses, and URLs.
"""

import re
from typing import List, Dict, Pattern, Optional


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
    
    def detect_all(self, text: str) -> List[Dict[str, any]]:
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
        
        # Sort by start position for consistent ordering
        results.sort(key=lambda x: x['start'])
        return results
    
    def detect_ssn(self, text: str) -> List[Dict[str, any]]:
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
    
    def detect_phone(self, text: str) -> List[Dict[str, any]]:
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
    
    def detect_email(self, text: str) -> List[Dict[str, any]]:
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
    
    def detect_ip(self, text: str) -> List[Dict[str, any]]:
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
    
    def detect_url(self, text: str) -> List[Dict[str, any]]:
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

