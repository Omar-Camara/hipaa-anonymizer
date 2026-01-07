# How to Test the API Yourself

## Quick Start

### 1. Start the Server

Open a terminal and run:

```bash
# Activate virtual environment
source venv/bin/activate

# Start the server
uvicorn src.api.main:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

### 2. Test Methods

## Method 1: Interactive API Documentation (Easiest)

Open your browser and go to:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

You can:
- See all available endpoints
- Click "Try it out" on any endpoint
- Fill in the request body
- Click "Execute" to test
- See the response immediately

**Example for `/detect` endpoint:**
1. Go to http://localhost:8000/docs
2. Find `POST /detect`
3. Click "Try it out"
4. Paste this in the request body:
```json
{
  "text": "Patient John Smith, SSN: 123-45-6789, phone: (555) 123-4567",
  "enable_tier2": true,
  "enable_tier3": false
}
```
5. Click "Execute"
6. See the response with detected PHI!

## Method 2: Using the Test Script

Run the automated test script:

```bash
# In a new terminal (keep server running)
source venv/bin/activate
python scripts/test_api.py
```

This will test all endpoints automatically.

## Method 3: Using cURL

### Health Check
```bash
curl http://localhost:8000/health
```

### Detect PHI
```bash
curl -X POST "http://localhost:8000/detect" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Patient John Smith, SSN: 123-45-6789, phone: (555) 123-4567",
    "enable_tier2": true,
    "enable_tier3": false
  }'
```

### Anonymize Text
```bash
curl -X POST "http://localhost:8000/anonymize" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Patient John Smith, SSN: 123-45-6789",
    "method": "safe_harbor",
    "enable_tier2": true
  }'
```

## Method 4: Using Python

Create a test script or use Python REPL:

```python
import requests

BASE_URL = "http://localhost:8000"

# Test health
response = requests.get(f"{BASE_URL}/health")
print("Health:", response.json())

# Test detection
response = requests.post(
    f"{BASE_URL}/detect",
    json={
        "text": "Patient John Smith, SSN: 123-45-6789, phone: (555) 123-4567",
        "enable_tier2": True,
        "enable_tier3": False
    }
)
print("\nDetections:")
for det in response.json()["detections"]:
    print(f"  - {det['type']}: '{det['value']}' (confidence: {det['confidence']})")

# Test anonymization
response = requests.post(
    f"{BASE_URL}/anonymize",
    json={
        "text": "Patient John Smith, SSN: 123-45-6789",
        "method": "safe_harbor"
    }
)
result = response.json()
print(f"\nOriginal: {result['original_text']}")
print(f"Anonymized: {result['anonymized_text']}")
```

## Method 5: Using HTTPie (if installed)

```bash
# Install: pip install httpie

# Health check
http GET http://localhost:8000/health

# Detect PHI
http POST http://localhost:8000/detect \
  text="Patient John Smith, SSN: 123-45-6789" \
  enable_tier2:=true

# Anonymize
http POST http://localhost:8000/anonymize \
  text="Patient John Smith, SSN: 123-45-6789" \
  method="safe_harbor"
```

## Test Examples

### Example 1: Simple Detection
```bash
curl -X POST "http://localhost:8000/detect" \
  -H "Content-Type: application/json" \
  -d '{"text": "SSN: 123-45-6789"}'
```

**Expected Response:**
```json
{
  "detections": [
    {
      "type": "ssn",
      "value": "123-45-6789",
      "start": 5,
      "end": 16,
      "confidence": 1.0,
      "source": null
    }
  ],
  "total": 1,
  "text_length": 16
}
```

### Example 2: Medical Note
```bash
curl -X POST "http://localhost:8000/anonymize" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Patient John Smith, DOB: 1985-05-15, SSN: 123-45-6789, phone: (555) 123-4567, email: john@example.com",
    "method": "safe_harbor",
    "enable_tier2": true
  }'
```

**Expected Response:**
```json
{
  "anonymized_text": "Patient [NAME], DOB: [DATE], SSN: [SSN], phone: [PHONE], email: [EMAIL]",
  "original_text": "Patient John Smith, DOB: 1985-05-15, SSN: 123-45-6789, phone: (555) 123-4567, email: john@example.com",
  "detections": [...],
  "statistics": {
    "total_phi": 5,
    "by_type": {"name": 1, "date": 1, "ssn": 1, "phone": 1, "email": 1}
  }
}
```

### Example 3: Batch Processing
```bash
curl -X POST "http://localhost:8000/batch/detect?enable_tier2=true" \
  -H "Content-Type: application/json" \
  -d '[
    "Patient Alice, SSN: 123-45-6789",
    "Contact at email@example.com"
  ]'
```

## Troubleshooting

### Server won't start
- Make sure port 8000 is not in use: `lsof -i :8000`
- Check if FastAPI is installed: `pip install fastapi uvicorn`

### Connection refused
- Make sure the server is running
- Check the URL: should be `http://localhost:8000` or `http://127.0.0.1:8000`

### Import errors
- Make sure you're in the virtual environment: `source venv/bin/activate`
- Install dependencies: `pip install -r requirements.txt`

### Tier 2/3 not available
- Tier 2: Install spaCy model: `python -m spacy download en_core_web_sm`
- Tier 3: Requires model download (see Tier 3 setup docs)

## Quick Test Checklist

- [ ] Server starts without errors
- [ ] `/health` endpoint returns `{"status": "healthy"}`
- [ ] `/detect` finds PHI in test text
- [ ] `/anonymize` replaces PHI correctly
- [ ] Interactive docs load at `/docs`
- [ ] Batch endpoints work with multiple texts

## Next Steps

Once testing works:
1. Try with your own medical text samples
2. Test different anonymization methods (safe_harbor, pseudonymize, redact, tag)
3. Enable Tier 3 for ambiguous case validation
4. Test batch processing for multiple documents

