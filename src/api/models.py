"""
Pydantic models for API request/response validation.
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, field_validator
from pydantic import ConfigDict


class DetectionResponse(BaseModel):
    """Single PHI detection result."""
    type: str = Field(..., description="Type of PHI detected (e.g., 'ssn', 'name', 'phone')")
    value: str = Field(..., description="The detected PHI value")
    start: int = Field(..., description="Start position in text")
    end: int = Field(..., description="End position in text")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")
    source: Optional[str] = Field(None, description="Detection source (e.g., 'regex', 'ner', 'slm_validated')")
    validated: Optional[bool] = Field(None, description="Whether validated by Tier 3")
    original_type: Optional[str] = Field(None, description="Original type before Tier 3 refinement")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "ssn",
                "value": "123-45-6789",
                "start": 0,
                "end": 11,
                "confidence": 1.0,
                "source": "regex",
                "validated": None,
                "original_type": None
            }
        }
    )


class DetectionRequest(BaseModel):
    """Request model for PHI detection."""
    text: str = Field(..., description="Text to scan for PHI", min_length=1)
    enable_tier2: bool = Field(True, description="Enable Tier 2 (NER) detection")
    enable_tier3: bool = Field(False, description="Enable Tier 3 (SLM validation)")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text": "Patient John Smith, SSN: 123-45-6789, phone: (555) 123-4567",
                "enable_tier2": True,
                "enable_tier3": False
            }
        }
    )


class DetectionResponseModel(BaseModel):
    """Response model for detection endpoint."""
    detections: List[DetectionResponse] = Field(..., description="List of detected PHI")
    total: int = Field(..., description="Total number of PHI detected")
    text_length: int = Field(..., description="Length of input text")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "detections": [
                    {
                        "type": "ssn",
                        "value": "123-45-6789",
                        "start": 0,
                        "end": 11,
                        "confidence": 1.0,
                        "source": "regex"
                    }
                ],
                "total": 1,
                "text_length": 50
            }
        }
    )


class AnonymizeRequest(BaseModel):
    """Request model for anonymization."""
    text: str = Field(..., description="Text containing PHI to anonymize", min_length=1)
    method: str = Field(
        "safe_harbor",
        description="Anonymization method: 'safe_harbor', 'pseudonymize', 'redact', or 'tag'"
    )
    enable_tier2: bool = Field(True, description="Enable Tier 2 (NER) detection")
    enable_tier3: bool = Field(False, description="Enable Tier 3 (SLM validation)")
    redact: bool = Field(False, description="If True, remove PHI entirely (overrides method)")
    tag: bool = Field(False, description="If True, use tagged format [TYPE:N] (overrides method)")
    
    @field_validator('method')
    @classmethod
    def validate_method(cls, v):
        valid_methods = ['safe_harbor', 'pseudonymize', 'redact', 'tag']
        if v not in valid_methods:
            raise ValueError(f"Method must be one of {valid_methods}")
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text": "Patient John Smith, SSN: 123-45-6789",
                "method": "safe_harbor",
                "enable_tier2": True,
                "enable_tier3": False
            }
        }
    )


class AnonymizeResponse(BaseModel):
    """Response model for anonymization endpoint."""
    anonymized_text: str = Field(..., description="Anonymized text with PHI replaced/removed")
    original_text: str = Field(..., description="Original input text")
    detections: List[DetectionResponse] = Field(..., description="List of detected PHI")
    statistics: Dict[str, Any] = Field(..., description="Anonymization statistics")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "anonymized_text": "Patient [NAME], SSN: [SSN]",
                "original_text": "Patient John Smith, SSN: 123-45-6789",
                "detections": [
                    {
                        "type": "name",
                        "value": "John Smith",
                        "start": 8,
                        "end": 18,
                        "confidence": 0.9,
                        "source": "ner"
                    },
                    {
                        "type": "ssn",
                        "value": "123-45-6789",
                        "start": 26,
                        "end": 37,
                        "confidence": 1.0,
                        "source": "regex"
                    }
                ],
                "statistics": {
                    "total_phi": 2,
                    "by_type": {"name": 1, "ssn": 1},
                    "by_hipaa_category": {"name": 1, "social_security_number": 1}
                }
            }
        }
    )


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    tiers_available: Dict[str, bool] = Field(..., description="Availability of each tier")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "tiers_available": {
                    "tier1": True,
                    "tier2": True,
                    "tier3": False
                }
            }
        }
    )
