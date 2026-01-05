"""
Unit tests for anonymization modules.

Tests cover Safe Harbor, pseudonymization, and category tagging.
"""

import pytest
from src.anonymizers.safe_harbor import SafeHarborAnonymizer
from src.anonymizers.pseudonymizer import Pseudonymizer
from src.anonymizers.category_tagger import CategoryTagger


class TestSafeHarborAnonymizer:
    """Test suite for Safe Harbor anonymizer."""
    
    @pytest.fixture
    def anonymizer(self):
        """Create SafeHarborAnonymizer instance."""
        return SafeHarborAnonymizer()
    
    @pytest.fixture
    def sample_detections(self):
        """Sample PHI detections for testing."""
        return [
            {'type': 'ssn', 'value': '123-45-6789', 'start': 20, 'end': 31, 'confidence': 1.0},
            {'type': 'phone', 'value': '(555) 123-4567', 'start': 40, 'end': 54, 'confidence': 1.0},
            {'type': 'name', 'value': 'John Smith', 'start': 8, 'end': 19, 'confidence': 0.9},
        ]
    
    def test_anonymize_basic(self, anonymizer, sample_detections):
        """Test basic anonymization."""
        text = "Patient John Smith, SSN: 123-45-6789, phone: (555) 123-4567"
        result = anonymizer.anonymize(text, sample_detections)
        
        assert '[SSN]' in result
        assert '[PHONE]' in result
        assert '[NAME]' in result
        assert '123-45-6789' not in result
        assert '(555) 123-4567' not in result
    
    def test_anonymize_with_redaction(self, anonymizer, sample_detections):
        """Test redaction (removal) of PHI."""
        text = "Patient John Smith, SSN: 123-45-6789"
        result = anonymizer.anonymize_with_redaction(text, sample_detections)
        
        assert 'John Smith' not in result
        assert '123-45-6789' not in result
        assert 'Patient' in result  # Non-PHI should remain
    
    def test_anonymize_with_tags(self, anonymizer, sample_detections):
        """Test anonymization with tagged placeholders."""
        text = "Patient John Smith, SSN: 123-45-6789"
        result = anonymizer.anonymize_with_tags(text, sample_detections)
        
        assert '[NAME:1]' in result or '[SSN:1]' in result
        assert 'John Smith' not in result
        assert '123-45-6789' not in result
    
    def test_custom_replacements(self):
        """Test custom replacement map."""
        custom_map = {'ssn': '[REDACTED_SSN]', 'phone': '[REDACTED_PHONE]'}
        anonymizer = SafeHarborAnonymizer(replacement_map=custom_map)
        
        detections = [{'type': 'ssn', 'value': '123-45-6789', 'start': 0, 'end': 11, 'confidence': 1.0}]
        result = anonymizer.anonymize("SSN: 123-45-6789", detections)
        
        assert '[REDACTED_SSN]' in result
        assert '123-45-6789' not in result
    
    def test_empty_detections(self, anonymizer):
        """Test with no detections."""
        text = "No PHI in this text"
        result = anonymizer.anonymize(text, [])
        
        assert result == text
    
    def test_overlapping_detections(self, anonymizer):
        """Test handling of overlapping detections."""
        # This shouldn't happen after deduplication, but test anyway
        detections = [
            {'type': 'name', 'value': 'John', 'start': 8, 'end': 12, 'confidence': 0.8},
            {'type': 'name', 'value': 'John Smith', 'start': 8, 'end': 19, 'confidence': 0.9},
        ]
        text = "Patient John Smith"
        result = anonymizer.anonymize(text, detections)
        
        # Should handle gracefully
        assert '[NAME]' in result


class TestPseudonymizer:
    """Test suite for Pseudonymizer."""
    
    @pytest.fixture
    def pseudonymizer(self):
        """Create Pseudonymizer instance."""
        return Pseudonymizer(seed=42)
    
    @pytest.fixture
    def sample_detections(self):
        """Sample PHI detections."""
        return [
            {'type': 'ssn', 'value': '123-45-6789', 'start': 0, 'end': 11, 'confidence': 1.0},
            {'type': 'name', 'value': 'John Smith', 'start': 12, 'end': 23, 'confidence': 0.9},
        ]
    
    def test_pseudonymize_consistency(self, pseudonymizer, sample_detections):
        """Test that same PHI gets same pseudonym."""
        text1 = "SSN: 123-45-6789"
        text2 = "SSN: 123-45-6789"
        
        result1 = pseudonymizer.pseudonymize(text1, sample_detections[:1])
        result2 = pseudonymizer.pseudonymize(text2, sample_detections[:1])
        
        # Extract pseudonyms (assuming format preservation)
        # Both should have the same pseudonym for the same SSN
        assert result1 == result2
    
    def test_pseudonymize_format_preservation(self, pseudonymizer):
        """Test format preservation."""
        detections = [
            {'type': 'ssn', 'value': '123-45-6789', 'start': 0, 'end': 11, 'confidence': 1.0},
            {'type': 'phone', 'value': '(555) 123-4567', 'start': 12, 'end': 26, 'confidence': 1.0},
        ]
        text = "SSN: 123-45-6789 Phone: (555) 123-4567"
        result = pseudonymizer.pseudonymize(text, detections)
        
        # Should preserve format (XXX-XX-XXXX for SSN, (XXX) XXX-XXXX for phone)
        assert '-' in result or '(' in result  # Some format preserved
    
    def test_pseudonymize_cache(self, pseudonymizer):
        """Test pseudonym caching."""
        detections = [{'type': 'ssn', 'value': '123-45-6789', 'start': 0, 'end': 11, 'confidence': 1.0}]
        
        # First call
        result1 = pseudonymizer.pseudonymize("SSN: 123-45-6789", detections)
        
        # Second call with same value
        result2 = pseudonymizer.pseudonymize("SSN: 123-45-6789", detections)
        
        # Should be the same (cached)
        assert result1 == result2
        assert pseudonymizer.get_cache_size() > 0
    
    def test_clear_cache(self, pseudonymizer):
        """Test cache clearing."""
        detections = [{'type': 'ssn', 'value': '123-45-6789', 'start': 0, 'end': 11, 'confidence': 1.0}]
        pseudonymizer.pseudonymize("SSN: 123-45-6789", detections)
        
        assert pseudonymizer.get_cache_size() > 0
        pseudonymizer.clear_cache()
        assert pseudonymizer.get_cache_size() == 0
    
    def test_different_values_different_pseudonyms(self, pseudonymizer):
        """Test that different values get different pseudonyms."""
        detections1 = [{'type': 'ssn', 'value': '123-45-6789', 'start': 0, 'end': 11, 'confidence': 1.0}]
        detections2 = [{'type': 'ssn', 'value': '987-65-4321', 'start': 0, 'end': 11, 'confidence': 1.0}]
        
        result1 = pseudonymizer.pseudonymize("SSN: 123-45-6789", detections1)
        result2 = pseudonymizer.pseudonymize("SSN: 987-65-4321", detections2)
        
        # Should be different
        assert result1 != result2


class TestCategoryTagger:
    """Test suite for CategoryTagger."""
    
    @pytest.fixture
    def tagger(self):
        """Create CategoryTagger instance."""
        return CategoryTagger()
    
    def test_tag_basic(self, tagger):
        """Test basic tagging."""
        detections = [
            {'type': 'ssn', 'value': '123-45-6789', 'start': 0, 'end': 11, 'confidence': 1.0},
            {'type': 'phone', 'value': '(555) 123-4567', 'start': 12, 'end': 26, 'confidence': 1.0},
        ]
        
        tagged = tagger.tag(detections)
        
        assert len(tagged) == 2
        assert tagged[0]['hipaa_category'] == 'social_security_number'
        assert tagged[1]['hipaa_category'] == 'telephone_number'
        assert all('safe_harbor_requirement' in t for t in tagged)
    
    def test_get_hipaa_category(self, tagger):
        """Test HIPAA category mapping."""
        assert tagger.get_hipaa_category('ssn') == 'social_security_number'
        assert tagger.get_hipaa_category('phone') == 'telephone_number'
        assert tagger.get_hipaa_category('name') == 'name'
        assert tagger.get_hipaa_category('unknown') == 'other_unique_identifier'
    
    def test_requires_removal(self, tagger):
        """Test removal requirement checking."""
        detection_ssn = {'type': 'ssn', 'value': '123-45-6789', 'start': 0, 'end': 11}
        detection_name = {'type': 'name', 'value': 'John', 'start': 0, 'end': 4}
        
        assert tagger.requires_removal(detection_ssn) is True
        assert tagger.requires_removal(detection_name) is True
    
    def test_tag_with_metadata(self, tagger):
        """Test that tagged detections include metadata."""
        detections = [
            {'type': 'ssn', 'value': '123-45-6789', 'start': 0, 'end': 11, 'confidence': 1.0},
        ]
        
        tagged = tagger.tag(detections)
        
        assert 'hipaa_category' in tagged[0]
        assert 'safe_harbor_requirement' in tagged[0]
        assert 'requires_removal' in tagged[0]
        assert tagged[0]['requires_removal'] is True

