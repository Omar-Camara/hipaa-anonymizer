# HIPAA Anonymizer

Production-ready HIPAA-compliant PHI anonymization system with full MLOps lifecycle.

## 🎯 Project Goal

Build a three-tier detection pipeline that can identify and anonymize all 18 HIPAA identifiers from clinical notes and medical documents with ≥99% recall and ≥95% precision.

## 🏗️ Architecture

**Three-Tier Detection Pipeline:**
1. **Tier 1: Regex Detector** ✅ - Deterministic patterns (SSN, phone, email, IP, URL)
2. **Tier 2: BioBERT NER** 🚧 - Contextual understanding (names, locations, dates, organizations)
3. **Tier 3: SLM Validation** 🚧 - Local LLM validation for ambiguous cases

## 🚀 Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt
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
text = "Patient information: SSN 123-45-6789, contact (555) 123-4567"
results = pipeline.detect(text)
print(results)
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

## 📋 Current Status

- ✅ **Tier 1: Regex Detector** - Complete
  - SSN detection (multiple formats)
  - Phone numbers (US & international)
  - Email addresses
  - IP addresses (IPv4 & IPv6)
  - URLs
  - 39 comprehensive unit tests

- 🚧 **Tier 2: BioBERT NER** - Next step
- 🚧 **Tier 3: SLM Validation** - Planned
- 🚧 **Anonymization Layer** - Planned
- 🚧 **API Interface** - Planned

## 🔍 What's Detected

The regex detector currently identifies:

- **SSN**: `123-45-6789`, `123 45 6789`, `123456789`
- **Phone**: `(123) 456-7890`, `123-456-7890`, `+1-123-456-7890`, `+44 20 1234 5678`
- **Email**: `user@example.com`, `first.last+tag@example.com`
- **IP**: `192.168.1.1`, `2001:0db8:85a3:0000:0000:8a2e:0370:7334`
- **URL**: `https://example.com`, `www.example.org`, `ftp://files.example.com`

## 📁 Project Structure

```
hipaa-anonymizer/
├── src/
│   ├── detectors/          # Detection modules (Tier 1, 2, 3)
│   │   ├── regex_detector.py    ✅
│   │   ├── ner_detector.py      🚧
│   │   └── slm_validator.py     🚧
│   ├── anonymizers/        # Anonymization strategies
│   ├── pipeline.py         # Main pipeline integration
│   └── api.py              # FastAPI endpoints
├── tests/                  # Unit and integration tests
├── scripts/                # Utility scripts
│   ├── test_detector.py    # Interactive testing CLI
│   └── sample_medical_notes.txt
└── requirements.txt
```

## 🎯 Next Steps

1. **Build Pipeline Integration** - Complete `src/pipeline.py` to aggregate all tiers
2. **Implement Tier 2: BioBERT NER** - Add contextual detection for names, locations, dates
3. **Create Anonymization Layer** - Implement Safe Harbor and pseudonymization
4. **Build API Interface** - FastAPI endpoints for production use
5. **Add MLOps** - MLflow tracking, model registry, monitoring

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



