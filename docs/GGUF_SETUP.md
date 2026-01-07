# GGUF Model Setup Guide

## Overview

GGUF (GPT-Generated Unified Format) models are optimized quantized formats that provide **better CPU performance** than standard Hugging Face models. They're smaller, faster, and use less memory.

## Why Use GGUF?

- ✅ **2x faster** CPU inference
- ✅ **50-75% smaller** file sizes
- ✅ **Lower memory** usage
- ✅ **Better for CPU-only** systems

## Supported Models

### Phi-3 Mini (Recommended)

- **Repository**: [microsoft/Phi-3-mini-4k-instruct-gguf](https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf)
- **Q4 (Recommended)**: 2.2GB - Balanced quality/speed
- **FP16**: 7.2GB - Minimal quality loss

### LLaMA 3.2 3B

- **Repository**: [bartowski/Llama-3.2-3B-Instruct-GGUF](https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF)
- **Q4**: Recommended - Good balance
- **Q5**: Better quality
- **Q8**: Best quality (larger file)

## Installation

### Step 1: Install llama-cpp-python

```bash
# For CPU (recommended)
pip install llama-cpp-python

# For GPU acceleration (optional)
CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install llama-cpp-python
```

### Step 2: Install huggingface-hub

```bash
pip install huggingface-hub
```

### Step 3: Authenticate with Hugging Face

```bash
huggingface-cli login
# Enter your token from https://huggingface.co/settings/tokens
```

### Step 4: Request Model Access

1. **Phi-3 Mini**: https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf
   - Click "Request access" button
   - Wait for approval (usually instant)

2. **LLaMA 3.2 3B**: https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF
   - Click "Request access" if needed

### Step 5: Download GGUF Model

**Option A: Using the download script (Recommended)**

```bash
# Download Phi-3 Mini Q4 (recommended)
python scripts/download_gguf_models.py phi3-mini --quantization q4

# Or download LLaMA 3.2 3B Q4
python scripts/download_gguf_models.py llama3.2-3b --quantization q4
```

**Option B: Manual download**

```bash
# Download Phi-3 Mini Q4
huggingface-cli download microsoft/Phi-3-mini-4k-instruct-gguf \
    Phi-3-mini-4k-instruct-q4.gguf \
    --local-dir models \
    --local-dir-use-symlinks False
```

## Usage

### Basic Usage

```python
from src.validators.slm_validator import SLMValidator
from src.pipeline import HIPAAPipeline

# Use GGUF model (auto-detects if available)
validator = SLMValidator(
    model_name="models/Phi-3-mini-4k-instruct-q4.gguf",  # Path to GGUF file
    use_gguf=True,  # Enable GGUF support
    gguf_quantization="q4"  # Quantization level
)

# Or use in pipeline
pipeline = HIPAAPipeline(enable_tier3=True)
# Pipeline will auto-detect GGUF if llama-cpp-python is installed
```

### Auto-Detection

The validator automatically prefers GGUF models if:
- `llama-cpp-python` is installed
- `use_gguf=True` (default)
- GGUF model file is found in cache or specified path

### Specify Model Path

```python
# Direct path to GGUF file
validator = SLMValidator(
    model_name="/path/to/Phi-3-mini-4k-instruct-q4.gguf",
    use_gguf=True
)
```

## Performance Comparison

| Format | CPU Latency | Memory | File Size |
|--------|-------------|--------|-----------|
| **Hugging Face** | 1-3 sec | 2-4GB | 7-8GB |
| **GGUF Q4** | 0.5-1.5 sec | 1-2GB | 2-3GB |
| **GGUF Q8** | 0.7-2 sec | 2-3GB | 4-5GB |

## Quantization Levels

- **Q4**: Best balance (recommended) - 2-3GB, fast
- **Q5**: Better quality - 3-4GB, slightly slower
- **Q8**: Best quality - 4-5GB, still faster than standard
- **FP16**: Minimal quality loss - 7GB, similar to standard

## Troubleshooting

### "llama-cpp-python not available"

```bash
pip install llama-cpp-python
```

### "Model file not found"

1. Check the file path is correct
2. Download the model using the script:
   ```bash
   python scripts/download_gguf_models.py phi3-mini
   ```

### "401 Unauthorized"

1. Request access to the model on Hugging Face
2. Login: `huggingface-cli login`
3. Wait for approval

### Slow Performance

1. Use Q4 quantization (smaller, faster)
2. Ensure you're using CPU-optimized build
3. Check you have enough RAM

## Comparison: GGUF vs Standard

### Standard Hugging Face Format

**Pros:**
- ✅ Works out of the box
- ✅ Easy to use
- ✅ Full compatibility

**Cons:**
- ⚠️ Slower on CPU
- ⚠️ Larger files
- ⚠️ More memory

### GGUF Format

**Pros:**
- ✅ 2x faster on CPU
- ✅ 50-75% smaller files
- ✅ Less memory usage
- ✅ Better for CPU-only systems

**Cons:**
- ⚠️ Requires llama-cpp-python
- ⚠️ Need to download separately
- ⚠️ Slightly more setup

## Recommendation

**For CPU-only systems**: Use GGUF Q4 - Best performance/size balance

**For systems with GPU**: Standard format works fine, but GGUF still faster on CPU

**For development**: Standard format is easier to start with

## Next Steps

1. Install `llama-cpp-python`
2. Download a GGUF model using the script
3. Use it in your pipeline - it will auto-detect!

See `docs/MODEL_FORMATS.md` for more details on format comparison.

