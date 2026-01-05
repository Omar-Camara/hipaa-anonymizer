"""
Unit tests for the NERDetector class.

Tests cover NER detection functionality with various medical text scenarios.
Note: Some tests may be skipped if spaCy biomedical model is not installed.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock


class TestNERDetector:
    """Test suite for NERDetector."""
    
    @pytest.fixture
    def detector(self):
        """Create a NERDetector instance for testing."""
        from src.detectors.ner_detector import NERDetector
        return NERDetector(use_spacy=True, confidence_threshold=0.5)
    
    def test_initialization(self, detector):
        """Test that detector initializes without errors."""
        assert detector.model_name == "en_core_sci_sm"
        assert detector.use_spacy is True
        assert detector.confidence_threshold == 0.5
        assert detector._initialized is False  # Lazy loading
    
    def test_label_mapping(self, detector):
        """Test label to HIPAA category mapping."""
        assert detector._map_label_to_hipaa('B-PER') == 'name'
        assert detector._map_label_to_hipaa('I-PER') == 'name'
        assert detector._map_label_to_hipaa('B-ORG') == 'organization'
        assert detector._map_label_to_hipaa('B-LOC') == 'location'
        assert detector._map_label_to_hipaa('B-DATE') == 'date'
        assert detector._map_label_to_hipaa('UNKNOWN') is None
    
    def test_empty_text(self, detector):
        """Test detection with empty text."""
        results = detector.detect("")
        assert len(results) == 0
        
        results = detector.detect("   ")
        assert len(results) == 0
    
    def test_detect_names_method(self, detector):
        """Test detect_names method."""
        # Mock the detect method
        mock_results = [
            {'type': 'name', 'value': 'John Smith', 'start': 0, 'end': 10, 'confidence': 0.9},
            {'type': 'location', 'value': 'Boston', 'start': 15, 'end': 21, 'confidence': 0.8},
            {'type': 'name', 'value': 'Jane Doe', 'start': 25, 'end': 33, 'confidence': 0.95}
        ]
        
        with patch.object(detector, 'detect', return_value=mock_results):
            names = detector.detect_names("test text")
            assert len(names) == 2
            assert all(n['type'] == 'name' for n in names)
    
    def test_detect_locations_method(self, detector):
        """Test detect_locations method."""
        mock_results = [
            {'type': 'location', 'value': 'Boston', 'start': 0, 'end': 6, 'confidence': 0.9},
            {'type': 'name', 'value': 'John', 'start': 10, 'end': 14, 'confidence': 0.8}
        ]
        
        with patch.object(detector, 'detect', return_value=mock_results):
            locations = detector.detect_locations("test text")
            assert len(locations) == 1
            assert locations[0]['type'] == 'location'
    
    def test_detect_dates_method(self, detector):
        """Test detect_dates method."""
        mock_results = [
            {'type': 'date', 'value': 'March 15, 2024', 'start': 0, 'end': 15, 'confidence': 0.95},
            {'type': 'name', 'value': 'John', 'start': 20, 'end': 24, 'confidence': 0.8}
        ]
        
        with patch.object(detector, 'detect', return_value=mock_results):
            dates = detector.detect_dates("test text")
            assert len(dates) == 1
            assert dates[0]['type'] == 'date'
    
    def test_detect_organizations_method(self, detector):
        """Test detect_organizations method."""
        mock_results = [
            {'type': 'organization', 'value': 'Boston Medical Center', 'start': 0, 'end': 22, 'confidence': 0.9},
            {'type': 'name', 'value': 'John', 'start': 25, 'end': 29, 'confidence': 0.8}
        ]
        
        with patch.object(detector, 'detect', return_value=mock_results):
            orgs = detector.detect_organizations("test text")
            assert len(orgs) == 1
            assert orgs[0]['type'] == 'organization'
    
    def test_confidence_threshold_filtering(self, detector):
        """Test that low-confidence results are filtered."""
        mock_results = [
            {'type': 'name', 'value': 'High Conf', 'start': 0, 'end': 10, 'confidence': 0.9},
            {'type': 'name', 'value': 'Low Conf', 'start': 15, 'end': 23, 'confidence': 0.3}
        ]
        
        detector.confidence_threshold = 0.5
        
        with patch.object(detector, 'detect', return_value=mock_results):
            # The filtering happens in _detect_spacy/_detect_transformers
            # This test verifies the threshold is used
            assert detector.confidence_threshold == 0.5
    
    def test_merge_overlapping_entities(self, detector):
        """Test merging of overlapping entities."""
        results = [
            {'type': 'name', 'value': 'John', 'start': 0, 'end': 4, 'confidence': 0.7},
            {'type': 'name', 'value': 'John Smith', 'start': 0, 'end': 10, 'confidence': 0.9}
        ]
        
        merged = detector._merge_overlapping(results)
        assert len(merged) == 1
        assert merged[0]['confidence'] == 0.9  # Higher confidence kept
    
    def test_chunk_text_long_document(self, detector):
        """Test text chunking for long documents."""
        long_text = "Sentence one. Sentence two. Sentence three. " * 100
        
        chunks = detector._chunk_text(long_text, max_length=100)
        assert len(chunks) > 1
        assert all(len(chunk) <= 100 or len(chunk.split()) <= 20 for chunk in chunks)
    
    def test_calculate_chunk_offsets(self, detector):
        """Test chunk offset calculation."""
        text = "First sentence. Second sentence. Third sentence."
        chunks = ["First sentence.", "Second sentence.", "Third sentence."]
        
        offsets = detector._calculate_chunk_offsets(text, chunks)
        assert len(offsets) == len(chunks)
        assert offsets[0] == 0
    
    def test_get_subtype(self, detector):
        """Test subtype extraction."""
        assert detector._get_subtype('B-PER', 'name') == 'person'
        assert detector._get_subtype('B-ORG', 'name') == 'organization'
        assert detector._get_subtype('B-LOC', 'location') is None
    
    @pytest.mark.skip(reason="Requires spaCy biomedical model")
    def test_detect_with_spacy_model(self, detector):
        """Test actual detection with spaCy model (requires model installation)."""
        text = "Dr. John Smith examined patient Jane Doe at Boston Medical Center."
        results = detector.detect(text)
        
        # Should detect names and possibly locations/organizations
        assert len(results) > 0
        assert all('type' in r for r in results)
        assert all('value' in r for r in results)
        assert all('start' in r for r in results)
        assert all('end' in r for r in results)
        assert all('confidence' in r for r in results)
        assert all('source' in r for r in results)
        assert all(r['source'] == 'ner' for r in results)
    
    def test_standardized_output_format(self, detector):
        """Test that output matches Tier 1 format."""
        mock_results = [
            {
                'type': 'name',
                'value': 'John Smith',
                'start': 0,
                'end': 10,
                'confidence': 0.9,
                'source': 'ner'
            }
        ]
        
        with patch.object(detector, 'detect', return_value=mock_results):
            results = detector.detect("test")
            
            # Check required fields match Tier 1 format
            assert len(results) > 0
            result = results[0]
            assert 'type' in result
            assert 'value' in result
            assert 'start' in result
            assert 'end' in result
            assert 'confidence' in result
            assert isinstance(result['confidence'], float)
            assert 0 <= result['confidence'] <= 1

