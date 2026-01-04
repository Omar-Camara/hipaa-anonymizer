"""
Unit tests for the RegexDetector class.

Tests cover all detection methods with various format variants
and edge cases to ensure robust pattern matching.
"""

import pytest
from src.detectors.regex_detector import RegexDetector


class TestRegexDetector:
    """Test suite for RegexDetector."""
    
    @pytest.fixture
    def detector(self):
        """Create a RegexDetector instance for testing."""
        return RegexDetector()
    
    def test_detect_ssn_dashed_format(self, detector):
        """Test SSN detection with dashed format."""
        text = "My SSN is 123-45-6789."
        results = detector.detect_ssn(text)
        
        assert len(results) == 1
        assert results[0]['type'] == 'ssn'
        assert results[0]['value'] == '123-45-6789'
        assert results[0]['start'] == 10
        assert results[0]['end'] == 21
        assert results[0]['confidence'] == 1.0
    
    def test_detect_ssn_spaced_format(self, detector):
        """Test SSN detection with spaced format."""
        text = "SSN: 123 45 6789"
        results = detector.detect_ssn(text)
        
        assert len(results) == 1
        assert results[0]['type'] == 'ssn'
        assert results[0]['value'] == '123-45-6789'  # Normalized
        assert results[0]['start'] == 5
        assert results[0]['end'] == 16
    
    def test_detect_ssn_no_separator(self, detector):
        """Test SSN detection without separators."""
        text = "SSN 123456789 found"
        results = detector.detect_ssn(text)
        
        assert len(results) == 1
        assert results[0]['type'] == 'ssn'
        assert results[0]['value'] == '123456789'
        assert results[0]['start'] == 4
        assert results[0]['end'] == 13
    
    def test_detect_ssn_multiple(self, detector):
        """Test detection of multiple SSNs."""
        text = "SSN1: 123-45-6789 and SSN2: 987-65-4321"
        results = detector.detect_ssn(text)
        
        assert len(results) == 2
        assert results[0]['value'] == '123-45-6789'
        assert results[1]['value'] == '987-65-4321'
    
    def test_detect_ssn_invalid_excluded(self, detector):
        """Test that invalid SSN patterns are excluded."""
        text = "Invalid: 000-12-3456, 123-00-4567, 123-45-0000"
        results = detector.detect_ssn(text)
        
        # Should not match invalid patterns
        assert len(results) == 0
    
    def test_detect_phone_parentheses_format(self, detector):
        """Test phone detection with parentheses format."""
        text = "Call me at (123) 456-7890"
        results = detector.detect_phone(text)
        
        assert len(results) == 1
        assert results[0]['type'] == 'phone'
        assert results[0]['value'] == '(123) 456-7890'
        assert results[0]['start'] == 11
        assert results[0]['end'] == 25
        assert results[0]['confidence'] == 1.0
    
    def test_detect_phone_dashed_format(self, detector):
        """Test phone detection with dashed format."""
        text = "Phone: 123-456-7890"
        results = detector.detect_phone(text)
        
        assert len(results) == 1
        assert results[0]['type'] == 'phone'
        assert results[0]['value'] == '123-456-7890'
    
    def test_detect_phone_dotted_format(self, detector):
        """Test phone detection with dotted format."""
        text = "Contact 123.456.7890"
        results = detector.detect_phone(text)
        
        assert len(results) == 1
        assert results[0]['type'] == 'phone'
        assert results[0]['value'] == '123.456.7890'
    
    def test_detect_phone_no_separator(self, detector):
        """Test phone detection without separators."""
        text = "Call 1234567890"
        results = detector.detect_phone(text)
        
        assert len(results) == 1
        assert results[0]['type'] == 'phone'
        assert results[0]['value'] == '1234567890'
    
    def test_detect_phone_with_country_code(self, detector):
        """Test phone detection with country code."""
        text = "International: +1-123-456-7890 or 1-123-456-7890"
        results = detector.detect_phone(text)
        
        assert len(results) == 2
        assert '+1-123-456-7890' in [r['value'] for r in results]
        assert '1-123-456-7890' in [r['value'] for r in results]
    
    def test_detect_email_basic(self, detector):
        """Test basic email detection."""
        text = "Contact me at john.doe@example.com"
        results = detector.detect_email(text)
        
        assert len(results) == 1
        assert results[0]['type'] == 'email'
        assert results[0]['value'] == 'john.doe@example.com'
        assert results[0]['confidence'] == 1.0
    
    def test_detect_email_variants(self, detector):
        """Test email detection with various formats."""
        text = "Emails: user+tag@example.co.uk, test_123@subdomain.example.org"
        results = detector.detect_email(text)
        
        assert len(results) == 2
        assert 'user+tag@example.co.uk' in [r['value'] for r in results]
        assert 'test_123@subdomain.example.org' in [r['value'] for r in results]
    
    def test_detect_ipv4(self, detector):
        """Test IPv4 address detection."""
        text = "Server IP: 192.168.1.1 and 10.0.0.1"
        results = detector.detect_ip(text)
        
        assert len(results) == 2
        ip_values = [r['value'] for r in results]
        assert '192.168.1.1' in ip_values
        assert '10.0.0.1' in ip_values
        assert all(r['type'] == 'ip' for r in results)
        assert all(r['confidence'] == 1.0 for r in results)
    
    def test_detect_ipv4_boundary_values(self, detector):
        """Test IPv4 detection with boundary values."""
        text = "IPs: 0.0.0.0, 255.255.255.255, 127.0.0.1"
        results = detector.detect_ip(text)
        
        assert len(results) == 3
        ip_values = [r['value'] for r in results]
        assert '0.0.0.0' in ip_values
        assert '255.255.255.255' in ip_values
        assert '127.0.0.1' in ip_values
    
    def test_detect_ipv6(self, detector):
        """Test IPv6 address detection."""
        text = "IPv6: 2001:0db8:85a3:0000:0000:8a2e:0370:7334"
        results = detector.detect_ip(text)
        
        assert len(results) == 1
        assert results[0]['type'] == 'ip'
        assert '2001:0db8:85a3:0000:0000:8a2e:0370:7334' in results[0]['value']
    
    def test_detect_url_http(self, detector):
        """Test URL detection with http protocol."""
        text = "Visit http://example.com for more info"
        results = detector.detect_url(text)
        
        assert len(results) == 1
        assert results[0]['type'] == 'url'
        assert results[0]['value'] == 'http://example.com'
        assert results[0]['confidence'] == 1.0
    
    def test_detect_url_https(self, detector):
        """Test URL detection with https protocol."""
        text = "Secure: https://secure.example.com/path?query=value"
        results = detector.detect_url(text)
        
        assert len(results) == 1
        assert results[0]['type'] == 'url'
        assert 'https://secure.example.com' in results[0]['value']
    
    def test_detect_url_www(self, detector):
        """Test URL detection with www prefix."""
        text = "Check www.example.org"
        results = detector.detect_url(text)
        
        assert len(results) == 1
        assert results[0]['type'] == 'url'
        assert results[0]['value'] == 'www.example.org'
    
    def test_detect_url_ftp(self, detector):
        """Test URL detection with ftp protocol."""
        text = "Download from ftp://files.example.com"
        results = detector.detect_url(text)
        
        assert len(results) == 1
        assert results[0]['type'] == 'url'
        assert 'ftp://files.example.com' in results[0]['value']
    
    def test_detect_all_comprehensive(self, detector):
        """Test detect_all with multiple PHI types."""
        text = """
        Patient info:
        SSN: 123-45-6789
        Phone: (555) 123-4567
        Email: patient@hospital.com
        IP: 192.168.1.100
        URL: https://medical-records.example.com
        """
        results = detector.detect_all(text)
        
        # Should detect all types
        types = [r['type'] for r in results]
        assert 'ssn' in types
        assert 'phone' in types
        assert 'email' in types
        assert 'ip' in types
        assert 'url' in types
        
        # Results should be sorted by start position
        assert all(results[i]['start'] <= results[i+1]['start'] 
                  for i in range(len(results) - 1))
    
    def test_detect_all_empty_text(self, detector):
        """Test detect_all with empty text."""
        results = detector.detect_all("")
        assert len(results) == 0
    
    def test_detect_all_no_matches(self, detector):
        """Test detect_all with text containing no PHI."""
        text = "This is just regular text with no sensitive information."
        results = detector.detect_all(text)
        assert len(results) == 0
    
    def test_detect_all_overlapping_positions(self, detector):
        """Test that results have correct positions even with multiple matches."""
        text = "SSN: 123-45-6789 and phone: 123-456-7890"
        results = detector.detect_all(text)
        
        # Ensure no overlapping positions
        for i in range(len(results) - 1):
            assert results[i]['end'] <= results[i+1]['start'] or \
                   results[i+1]['end'] <= results[i]['start']
    
    def test_detect_ssn_in_context(self, detector):
        """Test SSN detection in realistic context."""
        text = "The patient's social security number is 456-78-9012."
        results = detector.detect_ssn(text)
        
        assert len(results) == 1
        assert results[0]['value'] == '456-78-9012'
        assert results[0]['start'] == 40
        assert results[0]['end'] == 51
    
    def test_detect_phone_in_context(self, detector):
        """Test phone detection in realistic context."""
        text = "Please contact the office at 1-800-555-1234 for assistance."
        results = detector.detect_phone(text)
        
        assert len(results) == 1
        assert '1-800-555-1234' in results[0]['value']
    
    def test_detect_ssn_spaced_variations(self, detector):
        """Test SSN detection with various spacing patterns."""
        # Single space between groups
        text1 = "SSN: 123 45 6789"
        results1 = detector.detect_ssn(text1)
        assert len(results1) == 1
        assert results1[0]['value'] == '123-45-6789'  # Normalized
        
        # Space with no separator (should still work)
        text2 = "SSN: 123 45 6789 in context"
        results2 = detector.detect_ssn(text2)
        assert len(results2) == 1
        assert results2[0]['value'] == '123-45-6789'
        
        # Mixed spacing in same text (spaced and dashed)
        text3 = "SSN1: 123 45 6789 and SSN2: 456-78-9012"
        results3 = detector.detect_ssn(text3)
        assert len(results3) == 2
        assert any('123-45-6789' in r['value'] for r in results3)
        assert any('456-78-9012' in r['value'] for r in results3)
    
    def test_detect_phone_international_uk(self, detector):
        """Test international phone detection - UK format."""
        text = "Contact: +44 20 1234 5678 or +44-20-1234-5678"
        results = detector.detect_phone(text)
        
        assert len(results) >= 1
        assert any('+44' in r['value'] for r in results)
    
    def test_detect_phone_international_france(self, detector):
        """Test international phone detection - France format."""
        text = "Phone: +33 1 23 45 67 89"
        results = detector.detect_phone(text)
        
        assert len(results) == 1
        assert results[0]['type'] == 'phone'
        assert '+33' in results[0]['value']
    
    def test_detect_phone_international_germany(self, detector):
        """Test international phone detection - Germany format."""
        text = "Tel: +49 30 12345678"
        results = detector.detect_phone(text)
        
        assert len(results) == 1
        assert results[0]['type'] == 'phone'
        assert '+49' in results[0]['value']
    
    def test_detect_phone_international_canada(self, detector):
        """Test international phone detection - Canada format (similar to US)."""
        text = "Call: +1-613-555-1234"
        results = detector.detect_phone(text)
        
        assert len(results) == 1
        assert results[0]['type'] == 'phone'
        assert '+1-613-555-1234' in results[0]['value']
    
    def test_detect_phone_international_australia(self, detector):
        """Test international phone detection - Australia format."""
        text = "Phone: +61 2 1234 5678"
        results = detector.detect_phone(text)
        
        assert len(results) == 1
        assert results[0]['type'] == 'phone'
        assert '+61' in results[0]['value']
    
    def test_detect_phone_international_multiple(self, detector):
        """Test detection of multiple international phone numbers."""
        text = "Contacts: +44 20 1234 5678, +33 1 23 45 67 89, +49 30 12345678"
        results = detector.detect_phone(text)
        
        assert len(results) == 3
        countries = [r['value'].split()[0] if ' ' in r['value'] else r['value'][:3] 
                    for r in results]
        assert any('+44' in c for c in countries)
        assert any('+33' in c for c in countries)
        assert any('+49' in c for c in countries)
    
    def test_detect_email_with_plus_sign(self, detector):
        """Test email detection with plus sign in username."""
        text = "Email: user+tag@example.com"
        results = detector.detect_email(text)
        
        assert len(results) == 1
        assert results[0]['type'] == 'email'
        assert results[0]['value'] == 'user+tag@example.com'
    
    def test_detect_email_with_multiple_plus(self, detector):
        """Test email detection with multiple plus signs."""
        text = "Email: first+middle+last@example.com"
        results = detector.detect_email(text)
        
        assert len(results) == 1
        assert results[0]['type'] == 'email'
        assert '+' in results[0]['value']
    
    def test_detect_email_with_dots(self, detector):
        """Test email detection with dots in username."""
        text = "Email: first.last@example.com"
        results = detector.detect_email(text)
        
        assert len(results) == 1
        assert results[0]['type'] == 'email'
        assert results[0]['value'] == 'first.last@example.com'
    
    def test_detect_email_with_multiple_dots(self, detector):
        """Test email detection with multiple dots in username."""
        text = "Email: first.middle.last@example.com"
        results = detector.detect_email(text)
        
        assert len(results) == 1
        assert results[0]['type'] == 'email'
        assert results[0]['value'] == 'first.middle.last@example.com'
    
    def test_detect_email_with_plus_and_dots(self, detector):
        """Test email detection with both plus and dots in username."""
        text = "Email: first.last+tag@example.com"
        results = detector.detect_email(text)
        
        assert len(results) == 1
        assert results[0]['type'] == 'email'
        assert results[0]['value'] == 'first.last+tag@example.com'
        assert '.' in results[0]['value']
        assert '+' in results[0]['value']
    
    def test_detect_email_complex_username(self, detector):
        """Test email detection with complex username containing +, ., and _."""
        text = "Emails: user_name+tag123@example.com, test.user+filter@subdomain.co.uk"
        results = detector.detect_email(text)
        
        assert len(results) == 2
        assert any('user_name+tag123' in r['value'] for r in results)
        assert any('test.user+filter' in r['value'] for r in results)
    
    def test_detect_email_edge_cases(self, detector):
        """Test email detection with various edge cases."""
        text = "Emails: a+b@c.co, test.email+123@example-domain.com"
        results = detector.detect_email(text)
        
        assert len(results) == 2
        assert all(r['type'] == 'email' for r in results)
        assert all('@' in r['value'] for r in results)

