"""
Test script for FastAPI endpoints.

Usage:
    python scripts/test_api.py
    
    Or start the server first:
    uvicorn src.api.main:app --reload
    Then run this script.
"""

import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"


def test_health():
    """Test health check endpoint."""
    print("=" * 60)
    print("Testing /health endpoint")
    print("=" * 60)
    
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()


def test_detect():
    """Test detection endpoint."""
    print("=" * 60)
    print("Testing /detect endpoint")
    print("=" * 60)
    
    payload = {
        "text": "Patient John Smith, DOB: 1985-05-15, SSN: 123-45-6789, phone: (555) 123-4567, email: john.smith@example.com",
        "enable_tier2": True,
        "enable_tier3": False
    }
    
    response = requests.post(f"{BASE_URL}/detect", json=payload)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Total detections: {result['total']}")
    print(f"Text length: {result['text_length']}")
    print("\nDetections:")
    for det in result['detections']:
        print(f"  - {det['type']}: '{det['value']}' (conf: {det['confidence']:.2f}, source: {det.get('source', 'unknown')})")
    print()


def test_anonymize():
    """Test anonymization endpoint."""
    print("=" * 60)
    print("Testing /anonymize endpoint (safe_harbor)")
    print("=" * 60)
    
    payload = {
        "text": "Patient John Smith, DOB: 1985-05-15, SSN: 123-45-6789, phone: (555) 123-4567",
        "method": "safe_harbor",
        "enable_tier2": True,
        "enable_tier3": False
    }
    
    response = requests.post(f"{BASE_URL}/anonymize", json=payload)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"\nOriginal: {result['original_text']}")
    print(f"Anonymized: {result['anonymized_text']}")
    print(f"\nStatistics:")
    print(f"  Total PHI: {result['statistics']['total_phi']}")
    print(f"  By type: {result['statistics']['by_type']}")
    print()


def test_anonymize_pseudonymize():
    """Test pseudonymization."""
    print("=" * 60)
    print("Testing /anonymize endpoint (pseudonymize)")
    print("=" * 60)
    
    payload = {
        "text": "Patient John Smith, SSN: 123-45-6789",
        "method": "pseudonymize",
        "enable_tier2": True,
        "enable_tier3": False
    }
    
    response = requests.post(f"{BASE_URL}/anonymize", json=payload)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"\nOriginal: {result['original_text']}")
    print(f"Anonymized: {result['anonymized_text']}")
    print()


def test_batch_detect():
    """Test batch detection."""
    print("=" * 60)
    print("Testing /batch/detect endpoint")
    print("=" * 60)
    
    texts = [
        "Patient Alice Johnson, SSN: 987-65-4321",
        "Contact Dr. Smith at smith@hospital.com",
        "Patient Bob Williams, phone: 555-9876"
    ]
    
    response = requests.post(
        f"{BASE_URL}/batch/detect",
        params={"enable_tier2": True, "enable_tier3": False},
        json=texts
    )
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Total texts: {result['total_texts']}")
    print("\nResults:")
    for i, res in enumerate(result['results'], 1):
        print(f"\n  Text {i}: {res['text'][:50]}...")
        print(f"    Detections: {res['total']}")
        for det in res['detections']:
            print(f"      - {det['type']}: '{det['value']}'")
    print()


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("HIPAA Anonymizer API Test Suite")
    print("=" * 60)
    print("\nMake sure the API server is running:")
    print("  uvicorn src.api.main:app --reload")
    print("\n" + "=" * 60 + "\n")
    
    try:
        test_health()
        test_detect()
        test_anonymize()
        test_anonymize_pseudonymize()
        test_batch_detect()
        
        print("=" * 60)
        print("All tests completed!")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to API server.")
        print("Please start the server first:")
        print("  uvicorn src.api.main:app --reload")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

