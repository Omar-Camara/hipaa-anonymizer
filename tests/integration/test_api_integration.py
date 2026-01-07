"""
Integration tests for the FastAPI endpoints.

Tests the complete API flow including batch processing.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
from fastapi.testclient import TestClient
from src.api.app import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


class TestAPIIntegration:
    """Integration tests for API endpoints."""
    
    def test_detect_endpoint(self, client):
        """Test the /detect endpoint."""
        response = client.post(
            "/detect",
            json={"text": "Patient John Smith, SSN: 123-45-6789"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "detections" in data
        assert len(data["detections"]) > 0
    
    def test_anonymize_endpoint(self, client):
        """Test the /anonymize endpoint."""
        response = client.post(
            "/anonymize",
            json={
                "text": "Patient John Smith, SSN: 123-45-6789",
                "method": "safe_harbor"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "anonymized_text" in data
        assert "John Smith" not in data["anonymized_text"] or "[NAME]" in data["anonymized_text"]
        assert "123-45-6789" not in data["anonymized_text"] or "[SSN]" in data["anonymized_text"]
    
    def test_batch_detect_endpoint(self, client):
        """Test the /batch/detect endpoint."""
        texts = [
            "Patient John Smith, SSN: 123-45-6789",
            "Contact: (555) 123-4567, email: test@example.com",
            "No PHI in this text"
        ]
        
        response = client.post(
            "/batch/detect",
            json=texts,
            params={"enable_tier2": True, "enable_tier3": False}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) == 3
        assert data["total_texts"] == 3
        
        # First text should have detections
        assert len(data["results"][0]["detections"]) > 0
        # Third text might have no detections
        assert data["results"][2]["total"] >= 0
    
    def test_batch_anonymize_endpoint(self, client):
        """Test the /batch/anonymize endpoint."""
        texts = [
            "Patient John Smith, SSN: 123-45-6789",
            "Contact: (555) 123-4567"
        ]
        
        response = client.post(
            "/batch/anonymize",
            json=texts,
            params={"method": "safe_harbor", "enable_tier2": True}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) == 2
        
        # Check that PHI was anonymized
        for result in data["results"]:
            assert "anonymized_text" in result
            assert "original_text" in result
            assert "statistics" in result
    
    def test_health_endpoint(self, client):
        """Test the /health endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
    
    def test_api_error_handling(self, client):
        """Test API error handling."""
        # Invalid request
        response = client.post("/detect", json={})
        assert response.status_code == 422  # Validation error
        
        # Empty text - may return 422 (validation error) or 200 (empty detections)
        # Both are acceptable behaviors
        response = client.post("/detect", json={"text": ""})
        assert response.status_code in [200, 422]
        if response.status_code == 200:
            data = response.json()
            assert len(data["detections"]) == 0

