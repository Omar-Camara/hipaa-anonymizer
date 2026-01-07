# GGUF Quick Start Guide

## Why GGUF?

GGUF models are **2x faster on CPU** and use **50% less memory** than standard Hugging Face models. Perfect for CPU-only systems!

## Quick Setup (5 minutes)

### 1. Install llama-cpp-python

```bash
pip install llama-cpp-python huggingface-hub
```

### 2. Login to Hugging Face

```bash
huggingface-cli login
# Get token from: https://huggingface.co/settings/tokens
```

### 3. Request Access

- **Phi-3 Mini**: https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf
  - Click "Request access" → Usually instant approval

### 4. Download Model

```bash
# Download Phi-3 Mini Q4 (recommended - 2.2GB)
python scripts/download_gguf_models.py phi3-mini --quantization q4
```

### 5. Use It!

```python
from src.pipeline import HIPAAPipeline

# GGUF will be auto-detected if available
pipeline = HIPAAPipeline(enable_tier3=True)

# That's it! Works 2x faster on CPU
text = "Patient May reported symptoms in May 2024"
results = pipeline.detect(text)
```

## Model Options

### Phi-3 Mini (Recommended)

```bash
# Q4 - Best balance (2.2GB, recommended)
python scripts/download_gguf_models.py phi3-mini --quantization q4

# FP16 - Best quality (7.2GB)
python scripts/download_gguf_models.py phi3-mini --quantization fp16
```

### LLaMA 3.2 3B

```bash
# Q4 - Good balance
python scripts/download_gguf_models.py llama3.2-3b --quantization q4

# Q8 - Best quality
python scripts/download_gguf_models.py llama3.2-3b --quantization q8
```

## Performance

| Format | CPU Speed | Memory | File Size |
|--------|-----------|--------|-----------|
| Standard | 1-3 sec | 2-4GB | 7-8GB |
| **GGUF Q4** | **0.5-1.5 sec** | **1-2GB** | **2-3GB** |

## Manual Download (Alternative)

If the script doesn't work:

```bash
huggingface-cli download microsoft/Phi-3-mini-4k-instruct-gguf \
    Phi-3-mini-4k-instruct-q4.gguf \
    --local-dir models
```

Then use:

```python
from src.validators.slm_validator import SLMValidator

validator = SLMValidator(
    model_name="models/Phi-3-mini-4k-instruct-q4.gguf",
    use_gguf=True
)
```

## Troubleshooting

**"llama-cpp-python not found"**
```bash
pip install llama-cpp-python
```

**"401 Unauthorized"**
- Request access on Hugging Face
- Login: `huggingface-cli login`

**"Model file not found"**
- Check the download completed
- Verify the file path

## Full Documentation

See `docs/GGUF_SETUP.md` for complete setup guide.

