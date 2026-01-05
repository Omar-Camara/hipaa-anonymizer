# HIPAA Anonymizer

Production-ready HIPAA-compliant PHI anonymization system with full MLOps lifecycle.

## 🎯 Project Goal

Build a three-tier detection pipeline that can identify and anonymize all 18 HIPAA identifiers from clinical notes and medical documents with ≥99% recall and ≥95% precision.

## 🏗️ Architecture

**Three-Tier Detection Pipeline:**

1. **Tier 1: Regex Detector** ✅ - Deterministic patterns (SSN, phone, email, IP, URL)
2. **Tier 2: NER Detector** ✅ - Contextual understanding (names, locations, dates, organizations)
3. **Tier 3: SLM Validation** 🚧 - Local Small Language Model validation for ambiguous cases

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

- ✅ **Tier 2: NER Detector** - Complete
  - Name detection (person names, organizations)
  - Location detection (cities, states, addresses)
  - Date detection (various formats)
  - Auto-detects best available spaCy model (en_core_web_sm recommended)
  - 14 comprehensive unit tests
- 🚧 **Tier 3: SLM Validation** - Planned
- 🚧 **Anonymization Layer** - Planned
- 🚧 **API Interface** - Planned

## 🔍 What's Detected

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

1. **Implement Tier 3: SLM Validation** - Add local LLM validation for ambiguous cases
2. **Create Anonymization Layer** - Implement Safe Harbor and pseudonymization
3. **Build API Interface** - FastAPI endpoints for production use
4. **Add MLOps** - MLflow tracking, model registry, monitoring
5. **Fine-tune Models** - Optimize on i2b2 dataset for better accuracy

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
