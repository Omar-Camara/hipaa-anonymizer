# HIPAA Anonymizer API Guide

## Overview

The HIPAA Anonymizer provides a RESTful API for detecting and anonymizing Protected Health Information (PHI) in text. The API uses a three-tier detection pipeline:

- **Tier 1**: Regex patterns (SSN, phone, email, IP, URL)
- **Tier 2**: NER (names, locations, dates, organizations)
- **Tier 3**: SLM validation (ambiguous cases)

## Quick Start

### Start the Server

```bash
# Install dependencies
pip install fastapi uvicorn

# Start the server
uvicorn src.api.main:app --reload --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Test the API

```bash
# Run the test script
python scripts/test_api.py
```

## Endpoints

### Health Check

**GET** `/health`

Check service health and tier availability.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "tiers_available": {
    "tier1": true,
    "tier2": true,
    "tier3": false
  }
}
```

### Detect PHI

**POST** `/detect`

Detect PHI in text without anonymizing.

**Request:**
```json
{
  "text": "Patient John Smith, SSN: 123-45-6789, phone: (555) 123-4567",
  "enable_tier2": true,
  "enable_tier3": false
}
```

**Response:**
```json
{
  "detections": [
    {
      "type": "ssn",
      "value": "123-45-6789",
      "start": 26,
      "end": 37,
      "confidence": 1.0,
      "source": "regex"
    },
    {
      "type": "phone",
      "value": "(555) 123-4567",
      "start": 45,
      "end": 60,
      "confidence": 1.0,
      "source": "regex"
    },
    {
      "type": "name",
      "value": "John Smith",
      "start": 8,
      "end": 18,
      "confidence": 0.9,
      "source": "ner"
    }
  ],
  "total": 3,
  "text_length": 60
}
```

### Anonymize Text

**POST** `/anonymize`

Detect and anonymize PHI in text.

**Request:**
```json
{
  "text": "Patient John Smith, SSN: 123-45-6789",
  "method": "safe_harbor",
  "enable_tier2": true,
  "enable_tier3": false
}
```

**Methods:**
- `safe_harbor`: Replace with generic placeholders (HIPAA standard)
- `pseudonymize`: Replace with consistent pseudonyms
- `redact`: Remove PHI entirely
- `tag`: Replace with tagged format `[TYPE:N]`

**Response:**
```json
{
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
    "by_type": {
      "name": 1,
      "ssn": 1
    },
    "by_hipaa_category": {
      "name": 1,
      "social_security_number": 1
    }
  }
}
```

### Batch Detection

**POST** `/batch/detect`

Detect PHI in multiple texts.

**Request:**
```json
[
  "Patient Alice, SSN: 123-45-6789",
  "Contact at email@example.com"
]
```

**Query Parameters:**
- `enable_tier2`: Enable Tier 2 (default: `true`)
- `enable_tier3`: Enable Tier 3 (default: `false`)

**Response:**
```json
{
  "results": [
    {
      "text": "Patient Alice, SSN: 123-45-6789",
      "detections": [...],
      "total": 2
    },
    {
      "text": "Contact at email@example.com",
      "detections": [...],
      "total": 1
    }
  ],
  "total_texts": 2
}
```

### Batch Anonymization

**POST** `/batch/anonymize`

Anonymize multiple texts.

**Request:**
```json
[
  "Patient Alice, SSN: 123-45-6789",
  "Contact at email@example.com"
]
```

**Query Parameters:**
- `method`: Anonymization method (default: `safe_harbor`)
- `enable_tier2`: Enable Tier 2 (default: `true`)
- `enable_tier3`: Enable Tier 3 (default: `false`)

## Python Client Example

```python
import requests

BASE_URL = "http://localhost:8000"

# Detect PHI
response = requests.post(
    f"{BASE_URL}/detect",
    json={
        "text": "Patient John Smith, SSN: 123-45-6789",
        "enable_tier2": True,
        "enable_tier3": False
    }
)
detections = response.json()["detections"]

# Anonymize
response = requests.post(
    f"{BASE_URL}/anonymize",
    json={
        "text": "Patient John Smith, SSN: 123-45-6789",
        "method": "safe_harbor"
    }
)
anonymized = response.json()["anonymized_text"]
```

## cURL Examples

### Detect PHI
```bash
curl -X POST "http://localhost:8000/detect" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Patient John Smith, SSN: 123-45-6789",
    "enable_tier2": true,
    "enable_tier3": false
  }'
```

### Anonymize
```bash
curl -X POST "http://localhost:8000/anonymize" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Patient John Smith, SSN: 123-45-6789",
    "method": "safe_harbor"
  }'
```

## Error Handling

The API returns standard HTTP status codes:

- `200`: Success
- `422`: Validation error (invalid request format)
- `500`: Internal server error
- `503`: Service unavailable (pipeline initialization failed)

Error response format:
```json
{
  "detail": "Error message description"
}
```

## Performance Considerations

- **Tier 1 (Regex)**: Fast, always enabled
- **Tier 2 (NER)**: Moderate speed, requires spaCy model
- **Tier 3 (SLM)**: Slower, requires model download (~2-7GB)

For production use:
- Use Tier 1 + Tier 2 for most cases
- Enable Tier 3 only for ambiguous cases
- Consider batch endpoints for multiple texts
- Pipeline instances are cached per tier configuration

## Security Notes

- Configure CORS appropriately for production
- Consider adding authentication/authorization
- Validate input text length limits
- Monitor API usage and rate limiting

## Next Steps

- Add authentication (API keys, OAuth)
- Implement rate limiting
- Add request logging and monitoring
- Deploy with Docker
- Add WebSocket support for streaming

