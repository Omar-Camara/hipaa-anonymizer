"""
Unit tests for FastAPI endpoints.

Tests API endpoints using FastAPI TestClient.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
from fastapi.testclient import TestClient
from src.api.app import app

client = TestClient(app)


def test_root():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data


def test_health():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "tiers_available" in data
    assert "tier1" in data["tiers_available"]


def test_detect():
    """Test detection endpoint."""
    payload = {
        "text": "Patient John Smith, SSN: 123-45-6789, phone: (555) 123-4567",
        "enable_tier2": True,
        "enable_tier3": False
    }
    
    response = client.post("/detect", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "detections" in data
    assert "total" in data
    assert "text_length" in data
    assert data["total"] >= 2  # Should detect SSN and phone at minimum


def test_detect_empty_text():
    """Test detection with empty text."""
    payload = {
        "text": "",
        "enable_tier2": True,
        "enable_tier3": False
    }
    
    response = client.post("/detect", json=payload)
    # Should return 422 (validation error) or 200 with empty detections
    assert response.status_code in [200, 422]


def test_anonymize_safe_harbor():
    """Test anonymization with safe_harbor method."""
    payload = {
        "text": "Patient John Smith, SSN: 123-45-6789",
        "method": "safe_harbor",
        "enable_tier2": True,
        "enable_tier3": False
    }
    
    response = client.post("/anonymize", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "anonymized_text" in data
    assert "original_text" in data
    assert "detections" in data
    assert "statistics" in data
    assert data["original_text"] == payload["text"]
    assert data["anonymized_text"] != payload["text"]  # Should be anonymized


def test_anonymize_pseudonymize():
    """Test anonymization with pseudonymize method."""
    payload = {
        "text": "Patient John Smith, SSN: 123-45-6789",
        "method": "pseudonymize",
        "enable_tier2": True,
        "enable_tier3": False
    }
    
    response = client.post("/anonymize", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "anonymized_text" in data
    assert data["anonymized_text"] != payload["text"]


def test_anonymize_invalid_method():
    """Test anonymization with invalid method."""
    payload = {
        "text": "Patient John Smith",
        "method": "invalid_method",
        "enable_tier2": True,
        "enable_tier3": False
    }
    
    response = client.post("/anonymize", json=payload)
    assert response.status_code == 422  # Validation error


def test_batch_detect():
    """Test batch detection endpoint."""
    texts = [
        "Patient Alice, SSN: 123-45-6789",
        "Contact at email@example.com"
    ]
    
    response = client.post(
        "/batch/detect",
        params={"enable_tier2": True, "enable_tier3": False},
        json=texts
    )
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "total_texts" in data
    assert data["total_texts"] == len(texts)
    assert len(data["results"]) == len(texts)


def test_batch_anonymize():
    """Test batch anonymization endpoint."""
    texts = [
        "Patient Alice, SSN: 123-45-6789",
        "Contact at email@example.com"
    ]
    
    response = client.post(
        "/batch/anonymize",
        params={"method": "safe_harbor", "enable_tier2": True, "enable_tier3": False},
        json=texts
    )
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "total_texts" in data
    assert data["total_texts"] == len(texts)


def test_detection_response_format():
    """Test that detection response has correct format."""
    payload = {
        "text": "SSN: 123-45-6789",
        "enable_tier2": False,
        "enable_tier3": False
    }
    
    response = client.post("/detect", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    if data["detections"]:
        det = data["detections"][0]
        assert "type" in det
        assert "value" in det
        assert "start" in det
        assert "end" in det
        assert "confidence" in det
        assert 0.0 <= det["confidence"] <= 1.0


def test_anonymize_statistics():
    """Test that anonymization returns proper statistics."""
    payload = {
        "text": "Patient John Smith, SSN: 123-45-6789, phone: (555) 123-4567",
        "method": "safe_harbor",
        "enable_tier2": True,
        "enable_tier3": False
    }
    
    response = client.post("/anonymize", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    stats = data["statistics"]
    assert "total_phi" in stats
    assert "by_type" in stats
    assert "by_hipaa_category" in stats
    assert stats["total_phi"] >= 2

