# Tier 2: NER Detector Setup Guide

## Overview

Tier 2 uses Named Entity Recognition (NER) to detect contextual PHI like names, locations, dates, and organizations. The implementation supports two approaches:

1. **spaCy Biomedical Model** (Recommended for start) - Easier to set up
2. **Transformers/BioBERT** (Advanced) - More flexible but requires more setup

## Quick Start

### Option 1: Using spaCy Biomedical Model (Recommended)

```bash
# Install spaCy if not already installed
pip install "spacy>=3.7.0"

# Install scispaCy (biomedical models for spaCy)
pip install scispacy

# Install the biomedical model (must use pip, not spacy download)
# For spaCy 3.8.x, use version 0.5.3
pip install https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.3/en_core_sci_sm-0.5.3.tar.gz

# Or try the latest version from PyPI (if available)
# pip install en-core-sci-sm

# Test the installation
python -c "import spacy; nlp = spacy.load('en_core_sci_sm'); print('✓ Model loaded successfully')"
```

**Note:** The `en_core_sci_sm` model is NOT available via `spacy download`. It must be installed via pip as a separate package. The model version must match your spaCy version.

### Option 2: Using Transformers/BioBERT

```bash
# Install transformers and torch
pip install "transformers>=4.35.0" "torch>=2.1.0"

# The model will be downloaded automatically on first use
```

## Usage

### Basic Usage

```python
from src.detectors.ner_detector import NERDetector

# Initialize detector (uses spaCy by default)
detector = NERDetector()

# Detect entities
text = "Dr. John Smith examined patient Jane Doe at Boston Medical Center on March 15, 2024."
results = detector.detect(text)

for result in results:
    print(f"{result['type']}: {result['value']} (confidence: {result['confidence']:.2f})")
```

### Using with Pipeline

```python
from src.pipeline import HIPAAPipeline

# Pipeline automatically includes Tier 2 if available
pipeline = HIPAAPipeline(enable_tier2=True)

text = "Patient John Smith, DOB: 01/15/1985, lives in Boston, MA."
results = pipeline.detect(text)

# Results include both Tier 1 (regex) and Tier 2 (NER) detections
```

### Custom Configuration

```python
# Use transformers instead of spaCy
detector = NERDetector(
    model_name="dmis-lab/biobert-base-cased-v1.2",
    use_spacy=False,
    confidence_threshold=0.7  # Higher threshold for fewer false positives
)

# Force CPU usage
detector = NERDetector(device='cpu')
```

## What Gets Detected

Tier 2 detects:

- **Names**: Person names (patients, physicians, relatives)
- **Organizations**: Hospital names, clinics, insurance companies
- **Locations**: Cities, states, addresses, geographic subdivisions
- **Dates**: Birth dates, admission dates, procedure dates (various formats)

## Testing

Run the test suite:

```bash
# Run all NER tests
pytest tests/test_ner_detector.py -v

# Run with coverage
pytest tests/test_ner_detector.py --cov=src.detectors.ner_detector
```

Note: Some tests may be skipped if the biomedical model is not installed.

## Troubleshooting

### Error: "No compatible package found for 'en_core_sci_sm'"

**Solution:** You need to install `scispacy` first:

```bash
pip install scispacy
python -m spacy download en_core_sci_sm
```

### Error: "spaCy model 'en_core_sci_sm' not found"

**Solution:**

```bash
# First install scispaCy
pip install scispacy

# Then download the model
python -m spacy download en_core_sci_sm
```

### Error: "Transformers library not available"

**Solution:**

```bash
pip install "transformers>=4.35.0" "torch>=2.1.0"
```

### Warning: "Tier 2 (NER) not available"

The pipeline will continue with Tier 1 only. To enable Tier 2:

1. Install scispaCy: `pip install scispacy`
2. Download model: `python -m spacy download en_core_sci_sm`
3. Restart your application

### Performance Issues

- **Slow inference**: Use GPU if available (`device='cuda'`)
- **High memory usage**: Use smaller model or reduce batch size
- **Too many false positives**: Increase `confidence_threshold`

## Model Information

### spaCy Biomedical Model (`en_core_sci_sm`)

- **Package**: scispaCy (separate from spaCy)
- **Size**: ~50MB
- **Speed**: Fast (CPU-friendly)
- **Accuracy**: Good for general biomedical text
- **Best for**: Quick setup, CPU environments
- **Installation**: `pip install scispacy` then `python -m spacy download en_core_sci_sm`

### BioBERT (`dmis-lab/biobert-base-cased-v1.2`)

- **Size**: ~400MB
- **Speed**: Slower (benefits from GPU)
- **Accuracy**: Excellent (pre-trained on biomedical corpus)
- **Best for**: Production, high-accuracy requirements

## Alternative: Use Standard spaCy Model (Fallback)

If you can't install the biomedical model, you can use the standard English model as a fallback:

```python
from src.detectors.ner_detector import NERDetector

# Use standard English model (less accurate for medical text)
detector = NERDetector(model_name="en_core_web_sm", use_spacy=True)
```

Install with:

```bash
python -m spacy download en_core_web_sm
```

## Next Steps

1. **Fine-tuning**: Fine-tune BioBERT on i2b2 dataset for better accuracy
2. **Custom Labels**: Add custom entity types for medical record numbers
3. **Performance**: Optimize with batch processing and quantization
4. **Integration**: Combine with Tier 3 (SLM validation) for ambiguous cases

## References

- [spaCy Documentation](https://spacy.io/)
- [scispaCy Documentation](https://allenai.github.io/scispacy/)
- [Transformers Documentation](https://huggingface.co/docs/transformers/)
- [BioBERT Paper](https://arxiv.org/abs/1901.08746)
- [i2b2 Dataset](https://www.i2b2.org/NLP/DataSets/)
