"""
Unit tests for SLM Validator (Tier 3).

Tests cover validation logic, prompt generation, and response parsing.
Uses mocks to avoid requiring actual model downloads.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.validators.slm_validator import SLMValidator


class TestSLMValidator:
    """Test suite for SLM Validator."""
    
    @pytest.fixture
    def mock_model(self):
        """Create a mock model for testing."""
        mock_model = MagicMock()
        mock_tokenizer = MagicMock()
        mock_pipeline = MagicMock()
        
        # Mock pipeline response
        mock_pipeline.return_value = [{
            'generated_text': 'YES, this is PHI. Type: ssn'
        }]
        
        return {
            'model': mock_model,
            'tokenizer': mock_tokenizer,
            'pipeline': mock_pipeline
        }
    
    @patch('src.validators.slm_validator.AutoTokenizer')
    @patch('src.validators.slm_validator.AutoModelForCausalLM')
    @patch('src.validators.slm_validator.pipeline')
    def test_initialization(self, mock_pipeline, mock_model_class, mock_tokenizer_class):
        """Test SLM validator initialization."""
        # Mock the model loading
        mock_tokenizer = MagicMock()
        mock_model = MagicMock()
        mock_pipeline_instance = MagicMock()
        
        mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer
        mock_model_class.from_pretrained.return_value = mock_model
        mock_pipeline.return_value = mock_pipeline_instance
        
        validator = SLMValidator(model_name="microsoft/Phi-3-mini-4k-instruct")
        
        assert validator._tokenizer is not None
        assert validator._model is not None
        assert validator._pipeline is not None
    
    def test_identify_ambiguous_low_confidence(self):
        """Test identification of ambiguous detections (low confidence)."""
        validator = SLMValidator.__new__(SLMValidator)
        validator.confidence_threshold = 0.7
        
        detections = [
            {'type': 'ssn', 'value': '123-45-6789', 'start': 0, 'end': 11, 'confidence': 0.5},
            {'type': 'phone', 'value': '(555) 123-4567', 'start': 20, 'end': 34, 'confidence': 0.9},
            {'type': 'name', 'value': 'John Smith', 'start': 40, 'end': 51, 'confidence': 0.6},
        ]
        
        ambiguous = validator._identify_ambiguous(detections)
        
        # First and third should be ambiguous (low confidence)
        assert 0 in ambiguous
        assert 2 in ambiguous
        assert 1 not in ambiguous
    
    def test_identify_ambiguous_overlapping(self):
        """Test identification of ambiguous detections (overlapping)."""
        validator = SLMValidator.__new__(SLMValidator)
        validator.confidence_threshold = 0.7
        
        detections = [
            {'type': 'ssn', 'value': '123-45-6789', 'start': 0, 'end': 11, 'confidence': 0.9},
            {'type': 'phone', 'value': '123-45-6789', 'start': 5, 'end': 16, 'confidence': 0.8},  # Overlaps
            {'type': 'name', 'value': 'John Smith', 'start': 30, 'end': 41, 'confidence': 0.9},
        ]
        
        ambiguous = validator._identify_ambiguous(detections)
        
        # First two should be ambiguous (overlapping, different types)
        assert 0 in ambiguous
        assert 1 in ambiguous
        assert 2 not in ambiguous
    
    def test_overlaps(self):
        """Test overlap detection between two detections."""
        validator = SLMValidator.__new__(SLMValidator)
        
        det1 = {'start': 0, 'end': 10}
        det2 = {'start': 5, 'end': 15}  # Overlaps
        det3 = {'start': 20, 'end': 30}  # No overlap
        
        assert validator._overlaps(det1, det2) is True
        assert validator._overlaps(det1, det3) is False
        assert validator._overlaps(det2, det3) is False
    
    def test_create_validation_prompt(self):
        """Test validation prompt creation."""
        validator = SLMValidator.__new__(SLMValidator)
        
        prompt = validator._create_validation_prompt(
            context="Patient information: SSN 123-45-6789",
            detected_text="123-45-6789",
            detected_type="ssn",
            confidence=0.6
        )
        
        assert "Context:" in prompt
        assert "123-45-6789" in prompt
        assert "ssn" in prompt
        assert "0.60" in prompt
        assert "YES" in prompt
        assert "NO" in prompt
    
    def test_parse_response_yes(self):
        """Test parsing YES response."""
        validator = SLMValidator.__new__(SLMValidator)
        
        response = "YES, this is PHI. Type: ssn"
        is_phi, phi_type = validator._parse_response(response)
        
        assert is_phi is True
        assert phi_type == "ssn"
    
    def test_parse_response_no(self):
        """Test parsing NO response."""
        validator = SLMValidator.__new__(SLMValidator)
        
        response = "NO, this is not PHI"
        is_phi, phi_type = validator._parse_response(response)
        
        assert is_phi is False
        assert phi_type is None
    
    def test_parse_response_with_type(self):
        """Test parsing response with PHI type."""
        validator = SLMValidator.__new__(SLMValidator)
        
        responses = [
            ("YES. Type: phone", True, "phone"),
            ("YES, this is an email address", True, "email"),
            ("YES, location: Boston", True, "location"),
            ("NO, not PHI", False, None),
        ]
        
        for response, expected_is_phi, expected_type in responses:
            is_phi, phi_type = validator._parse_response(response)
            assert is_phi == expected_is_phi
            assert phi_type == expected_type
    
    @patch('src.validators.slm_validator.AutoTokenizer')
    @patch('src.validators.slm_validator.AutoModelForCausalLM')
    @patch('src.validators.slm_validator.pipeline')
    def test_validate_single_accepts(self, mock_pipeline, mock_model_class, mock_tokenizer_class):
        """Test single detection validation (accepts)."""
        # Setup mocks
        mock_tokenizer = MagicMock()
        mock_model = MagicMock()
        mock_pipeline_instance = MagicMock()
        mock_pipeline_instance.return_value = [{'generated_text': 'YES, this is PHI. Type: ssn'}]
        
        mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer
        mock_model_class.from_pretrained.return_value = mock_model
        mock_pipeline.return_value = mock_pipeline_instance
        
        validator = SLMValidator(model_name="microsoft/Phi-3-mini-4k-instruct")
        
        detection = {
            'type': 'ssn',
            'value': '123-45-6789',
            'start': 0,
            'end': 11,
            'confidence': 0.6
        }
        
        result = validator._validate_single(detection, "SSN: 123-45-6789", context_window=10)
        
        assert result is not None
        assert result['type'] == 'ssn'
        assert result['confidence'] > detection['confidence']  # Confidence boosted
        assert result.get('validated') is True
    
    @patch('src.validators.slm_validator.AutoTokenizer')
    @patch('src.validators.slm_validator.AutoModelForCausalLM')
    @patch('src.validators.slm_validator.pipeline')
    def test_validate_single_rejects(self, mock_pipeline, mock_model_class, mock_tokenizer_class):
        """Test single detection validation (rejects false positive)."""
        # Setup mocks
        mock_tokenizer = MagicMock()
        mock_model = MagicMock()
        mock_pipeline_instance = MagicMock()
        mock_pipeline_instance.return_value = [{'generated_text': 'NO, this is not PHI'}]
        
        mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer
        mock_model_class.from_pretrained.return_value = mock_model
        mock_pipeline.return_value = mock_pipeline_instance
        
        validator = SLMValidator(model_name="microsoft/Phi-3-mini-4k-instruct")
        
        detection = {
            'type': 'ssn',
            'value': '123-45-6789',
            'start': 0,
            'end': 11,
            'confidence': 0.5
        }
        
        result = validator._validate_single(detection, "MRN: 123-45-6789 (not SSN)", context_window=10)
        
        assert result is None  # Rejected as false positive
    
    @patch('src.validators.slm_validator.AutoTokenizer')
    @patch('src.validators.slm_validator.AutoModelForCausalLM')
    @patch('src.validators.slm_validator.pipeline')
    def test_validate_refines_type(self, mock_pipeline, mock_model_class, mock_tokenizer_class):
        """Test validation that refines PHI type."""
        # Setup mocks
        mock_tokenizer = MagicMock()
        mock_model = MagicMock()
        mock_pipeline_instance = MagicMock()
        mock_pipeline_instance.return_value = [{'generated_text': 'YES, this is PHI. Type: phone'}]
        
        mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer
        mock_model_class.from_pretrained.return_value = mock_model
        mock_pipeline.return_value = mock_pipeline_instance
        
        validator = SLMValidator(model_name="microsoft/Phi-3-mini-4k-instruct")
        
        detection = {
            'type': 'ssn',
            'value': '123-45-6789',
            'start': 0,
            'end': 11,
            'confidence': 0.6
        }
        
        result = validator._validate_single(detection, "Phone: 123-45-6789", context_window=10)
        
        assert result is not None
        assert result['type'] == 'phone'  # Type refined
        assert result.get('original_type') == 'ssn'
    
    @patch('src.validators.slm_validator.AutoTokenizer')
    @patch('src.validators.slm_validator.AutoModelForCausalLM')
    @patch('src.validators.slm_validator.pipeline')
    def test_validate_handles_errors(self, mock_pipeline, mock_model_class, mock_tokenizer_class):
        """Test validation error handling."""
        # Setup mocks
        mock_tokenizer = MagicMock()
        mock_model = MagicMock()
        mock_pipeline_instance = MagicMock()
        mock_pipeline_instance.side_effect = Exception("Model error")
        
        mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer
        mock_model_class.from_pretrained.return_value = mock_model
        mock_pipeline.return_value = mock_pipeline_instance
        
        validator = SLMValidator(model_name="microsoft/Phi-3-mini-4k-instruct")
        
        detection = {
            'type': 'ssn',
            'value': '123-45-6789',
            'start': 0,
            'end': 11,
            'confidence': 0.6
        }
        
        # Should return original detection on error
        result = validator._validate_single(detection, "SSN: 123-45-6789", context_window=10)
        
        assert result == detection  # Returns original on error
    
    def test_is_available(self):
        """Test availability check."""
        validator = SLMValidator.__new__(SLMValidator)
        validator._pipeline = None
        validator._llama_model = None
        validator.model_format = 'transformers'  # Initialize model_format
        
        assert validator.is_available() is False
        
        validator._pipeline = MagicMock()
        assert validator.is_available() is True
        
        # Test GGUF format
        validator.model_format = 'gguf'
        validator._pipeline = None
        validator._llama_model = None
        assert validator.is_available() is False
        
        validator._llama_model = MagicMock()
        assert validator.is_available() is True

