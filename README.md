# HIPAA Anonymizer

Production-ready HIPAA-compliant PHI anonymization system with full MLOps lifecycle.

## 🎯 Project Goal

Build a three-tier detection pipeline that can identify and anonymize all 18 HIPAA identifiers from clinical notes and medical documents with ≥99% recall and ≥95% precision.

## 🏗️ Architecture

**Three-Tier Detection Pipeline:**

1. **Tier 1: Regex Detector** ✅ - Deterministic patterns (SSN, phone, email, IP, URL)
2. **Tier 2: NER Detector** ✅ - Contextual understanding (names, locations, dates, organizations)
3. **Tier 3: SLM Validation** ✅ - Local Small Language Model validation for ambiguous cases

## 🚀 Quick Start

### Installation

```bash
# Create virtual environment (recommended)
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install spaCy English model for Tier 2
python -m spacy download en_core_web_sm
# Or use the setup script:
# ./scripts/setup_venv.sh
```

### Testing the Detector

#### Option 1: Interactive CLI Script

```bash
# Interactive mode - type text and press Enter
python scripts/test_detector.py

# Test specific text
python scripts/test_detector.py --text "Patient SSN: 123-45-6789, phone: (555) 123-4567"

# Test from file with highlighting
python scripts/test_detector.py --file scripts/sample_medical_notes.txt --highlight
```

#### Option 2: Python REPL

```python
from src.detectors.regex_detector import RegexDetector

detector = RegexDetector()
text = "Patient SSN: 123-45-6789, phone: (555) 123-4567, email: patient@hospital.com"
results = detector.detect_all(text)

for result in results:
    print(f"{result['type']}: {result['value']} at position {result['start']}-{result['end']}")
```

#### Option 3: Using the Pipeline

```python
from src.pipeline import HIPAAPipeline

pipeline = HIPAAPipeline()

# Detect PHI (Tier 1 & 2)
text = "Patient information: SSN 123-45-6789, contact (555) 123-4567"
results = pipeline.detect(text)
print(results)

# Enable Tier 3 for ambiguous case validation
pipeline_tier3 = HIPAAPipeline(enable_tier3=True)
results_validated = pipeline_tier3.detect(text)  # Validates ambiguous detections

# Anonymize PHI
anonymized = pipeline.anonymize(text, method="safe_harbor")
print(anonymized)  # "Patient information: SSN [SSN], contact [PHONE]"

# Or use pseudonymization
pseudonymized = pipeline.anonymize(text, method="pseudonymize")
print(pseudonymized)  # Consistent pseudonyms for same PHI
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_regex_detector.py -v
```

### Using the API

```bash
# Start the FastAPI server
uvicorn src.api.main:app --reload --port 8000

# Access interactive documentation
# Open http://localhost:8000/docs in your browser

# Access Gradio UI (integrated)
# Open http://localhost:8000/ui in your browser

# Test the API
python scripts/test_api.py
```

**API Endpoints:**

- `GET /health` - Health check and tier availability
- `POST /detect` - Detect PHI in text
- `POST /anonymize` - Anonymize text with PHI
- `POST /batch/detect` - Batch detection
- `POST /batch/anonymize` - Batch anonymization
- `GET /ui` - Gradio web interface

See [API Guide](docs/API_GUIDE.md) for detailed documentation.

### Using the Gradio UI

**Option 1: Standalone**
```bash
# Launch standalone Gradio UI
python scripts/run_gradio.py

# Access at: http://localhost:7860
```

**Option 2: Integrated with API**
```bash
# Start FastAPI server (UI automatically mounted)
uvicorn src.api.main:app --reload --port 8000

# Access UI at: http://localhost:8000/ui
```

The Gradio UI provides:
- 🔍 **Detect PHI**: Interactive detection with visual results
- 🛡️ **Anonymize**: Multiple anonymization methods
- 📊 **Statistics**: PHI detection breakdowns
- 📝 **Examples**: Pre-loaded example texts

See [Gradio UI Guide](docs/GRADIO_UI.md) for detailed documentation.

### Using Docker

**Quick Start with Docker Compose:**
```bash
# Build and start the container
docker compose up --build

# Access the API
# http://localhost:8000/docs
```

**Using Docker directly:**
```bash
# Build the image
docker build -t hipaa-anonymizer:latest .

# Run the container
docker run -d --name hipaa-anonymizer -p 8000:8000 hipaa-anonymizer:latest
```

**Production deployment:**
```bash
# Build production image
docker build -f Dockerfile.prod -t hipaa-anonymizer:prod .

# Run with production settings
docker run -d --name hipaa-anonymizer-prod -p 8000:8000 hipaa-anonymizer:prod
```

See [Docker Setup Guide](docs/DOCKER_SETUP.md) for detailed instructions.

## 📋 Current Status

- ✅ **Tier 1: Regex Detector** - Complete

  - SSN detection (multiple formats)
  - Phone numbers (US & international)
  - Email addresses
  - IP addresses (IPv4 & IPv6)
  - URLs
  - 39 comprehensive unit tests

- ✅ **Tier 2: NER Detector** - Complete

  - Name detection (person names, organizations)
  - Location detection (cities, states, addresses)
  - Date detection (various formats)
  - Auto-detects best available spaCy model (en_core_web_sm recommended)
  - 14 comprehensive unit tests

- ✅ **Tier 3: SLM Validation** - Complete
  - Validates ambiguous/low-confidence detections
  - Refines PHI type classifications
  - Filters false positives
  - Supports Phi-3 Mini and LLaMA 3.2 3B models
  - 12 comprehensive unit tests
- ✅ **Anonymization Layer** - Complete

  - Safe Harbor method (HIPAA standard)
  - Pseudonymization (consistent replacements)
  - Category tagging (HIPAA category mapping)
  - Multiple anonymization modes (replace, redact, tag)
  - 15 comprehensive unit tests

- ✅ **API Interface** - Complete
  - FastAPI REST endpoints
  - Detection and anonymization endpoints
  - Batch processing support
  - Interactive API documentation
  - Comprehensive test suite

- ✅ **Gradio UI** - Complete
  - User-friendly web interface
  - PHI detection with visual results
  - Multiple anonymization methods
  - Statistics and metadata display
  - Example texts and documentation
  - Integrated with FastAPI or standalone

- ✅ **Docker Deployment** - Complete
  - Dockerfile for development and production
  - Docker Compose for easy local development
  - Production-optimized multi-stage builds
  - Health checks and security best practices

## 🔍 What's Detected

**Current Coverage: ~78% of 18 HIPAA identifiers fully detected**

✅ **Fully Detected (14/18)**:
- Names, Geographic subdivisions, Dates
- Telephone numbers, Fax numbers, Email addresses, SSN
- Medical record numbers, Health plan beneficiary numbers
- Account numbers, Certificate/license numbers
- Web URLs, IP addresses

⚠️ **Partially Detected (1/18)**:
- Other unique identifiers (catch-all category)

❌ **Not Yet Detected (3/18)**:
- Vehicle identifiers (VINs, license plates)
- Device identifiers (medical device IDs)
- Biometric identifiers

See [HIPAA Coverage Guide](docs/HIPAA_COVERAGE.md) for detailed status.

## 🔍 What's Detected (Details)

### Tier 1: Regex Detector

- **SSN**: `123-45-6789`, `123 45 6789`, `123456789`
- **Phone**: `(123) 456-7890`, `123-456-7890`, `+1-123-456-7890`, `+44 20 1234 5678`
- **Email**: `user@example.com`, `first.last+tag@example.com`
- **IP**: `192.168.1.1`, `2001:0db8:85a3:0000:0000:8a2e:0370:7334`
- **URL**: `https://example.com`, `www.example.org`, `ftp://files.example.com`

### Tier 2: NER Detector

- **Names**: Person names (patients, physicians, relatives)
- **Organizations**: Hospital names, clinics, insurance companies
- **Locations**: Cities, states, addresses, geographic subdivisions
- **Dates**: Birth dates, admission dates, procedure dates (various formats)

### Tier 3: SLM Validation

- **Validates ambiguous detections** - Low confidence or overlapping detections
- **Refines classifications** - Improves PHI type accuracy
- **Filters false positives** - Removes incorrectly detected PHI
- **Context-aware** - Uses semantic understanding for edge cases

**Note**: Tier 3 requires `transformers` and `torch`. Models are downloaded automatically on first use (~2-7GB).

## 🔒 Anonymization Methods

The system supports multiple anonymization strategies:

### Safe Harbor (Default)

HIPAA-compliant replacement with generic placeholders:

- `[SSN]`, `[PHONE]`, `[EMAIL]`, `[NAME]`, `[LOCATION]`, etc.

### Pseudonymization

Consistent replacements - same PHI gets same pseudonym:

- Preserves format (SSN format, phone format, etc.)
- Useful for data analysis while maintaining privacy

### Redaction

Complete removal of PHI from text.

### Tagged Format

Numbered placeholders: `[NAME:1]`, `[SSN:2]`, etc.

**Example:**

```python
pipeline = HIPAAPipeline()

# Safe Harbor (default)
anonymized = pipeline.anonymize(text, method="safe_harbor")

# Pseudonymization
pseudonymized = pipeline.anonymize(text, method="pseudonymize")

# Redaction
redacted = pipeline.anonymize(text, redact=True)

# Tagged
tagged = pipeline.anonymize(text, tag=True)
```

## 📁 Project Structure

```
hipaa-anonymizer/
├── src/
│   ├── detectors/          # Detection modules (Tier 1, 2, 3)
│   │   ├── regex_detector.py    ✅
│   │   ├── ner_detector.py      ✅
│   │   └── slm_validator.py     🚧
│   ├── anonymizers/        # Anonymization strategies
│   ├── pipeline.py         # Main pipeline integration
│   └── api.py              # FastAPI endpoints
├── tests/                  # Unit and integration tests
├── scripts/                # Utility scripts
│   ├── test_detector.py    # Interactive testing CLI
│   ├── test_ner.py         # NER detector testing
│   └── sample_medical_notes.txt
├── docs/                   # Documentation
│   ├── TIER2_SETUP.md      # Tier 2 setup guide
│   ├── MODEL_COMPARISON.md  # Model comparison
│   └── VENV_SETUP.md       # Virtual environment guide
└── requirements.txt
```

## 🎯 Next Steps

1. **Build API Interface** - FastAPI endpoints for production use
2. **Add MLOps** - MLflow tracking, model registry, monitoring
3. **Fine-tune Models** - Optimize on i2b2 dataset for better accuracy
4. **Advanced Privacy Features** - k-anonymity, differential privacy, synthetic data
5. **Performance Optimization** - Batch processing, caching, model quantization

## 📊 Performance Targets

- **Recall**: ≥99%
- **Precision**: ≥95%
- **Throughput**: ≥50 documents/second
- **HIPAA Compliance**: All 18 identifiers detected

## 🔒 Privacy Features (Planned)

- Safe Harbor method
- k-anonymity
- Differential privacy
- Synthetic data generation

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

**Note**: This software is provided for educational and research purposes. When using this software for HIPAA compliance in production environments, ensure you:

- Conduct thorough testing and validation
- Comply with all applicable healthcare regulations
- Consult with legal and compliance experts
- Implement appropriate security measures
- Regularly audit and monitor the system

The authors and contributors are not responsible for any compliance issues or data breaches resulting from the use of this software.
