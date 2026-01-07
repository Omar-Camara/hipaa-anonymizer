# Tier 3: SLM Validation Setup Guide

## Overview

Tier 3 uses a Small Language Model (SLM) to validate ambiguous PHI detections. This guide covers installation and usage.

## Installation

### Basic Setup

Tier 3 requires `transformers` and `torch`:

```bash
pip install transformers torch
```

### Optional: Model Quantization

For faster CPU inference, install `bitsandbytes`:

```bash
pip install bitsandbytes
```

## Model Selection

Tier 3 supports two models (auto-selected in order of preference):

1. **Phi-3 Mini** (Recommended for speed)
   - Model: `microsoft/Phi-3-mini-4k-instruct`
   - Size: ~2.3GB
   - Fast inference on CPU
   - ⚠️ **Gated model** - Requires Hugging Face authentication

2. **LLaMA 3.2 3B** (Recommended for accuracy)
   - Model: `meta-llama/Llama-3.2-3B-Instruct`
   - Size: ~6GB
   - Better accuracy, slightly slower
   - ⚠️ **Gated model** - Requires Hugging Face authentication

Models are automatically downloaded from Hugging Face on first use.

### Authentication Required

These models are gated and require a Hugging Face account and token:

1. **Create Hugging Face account**: https://huggingface.co/join
2. **Request access to models**: 
   - Go to: https://huggingface.co/microsoft/Phi-3-mini-4k-instruct
   - Click **"Request access"** button on the model page
   - Fill out the form and submit (approval is usually instant)
   - Optional: Also request access to: https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct
3. **Get your token**: 
   - Go to: https://huggingface.co/settings/tokens
   - Click **"New token"** → Choose **"Read"** permissions
   - Copy the token (you won't see it again!)
4. **Login**:
   ```bash
   pip install huggingface-hub
   huggingface-cli login
   # Paste your token when prompted
   ```

**See detailed guide**: `docs/HUGGINGFACE_ACCESS.md` for step-by-step instructions.

**Alternative**: Tier 3 is optional. The system works great with just Tier 1 and Tier 2!

## Usage

### Basic Usage

```python
from src.pipeline import HIPAAPipeline

# Enable Tier 3
pipeline = HIPAAPipeline(enable_tier3=True)

# Detect PHI (with Tier 3 validation)
text = "Patient May reported symptoms. SSN: 123-45-6789"
results = pipeline.detect(text)

# Tier 3 will validate ambiguous detections like "May" (name vs. month)
```

### Custom Model Selection

```python
from src.validators.slm_validator import SLMValidator
from src.pipeline import HIPAAPipeline

# Use specific model
validator = SLMValidator(model_name="microsoft/Phi-3-mini-4k-instruct")

# Or use in pipeline
pipeline = HIPAAPipeline(enable_tier3=True)
```

### Configuration Options

```python
from src.validators.slm_validator import SLMValidator

validator = SLMValidator(
    model_name="microsoft/Phi-3-mini-4k-instruct",
    confidence_threshold=0.7,  # Only validate detections below this confidence
    device="cpu",  # or "cuda" for GPU
    max_length=512,  # Maximum sequence length
    use_quantization=True  # Use 8-bit quantization (if bitsandbytes available)
)
```

## When Tier 3 is Used

Tier 3 validation is triggered for:

1. **Low Confidence Detections** (confidence < threshold, default 0.7)
   - Uncertain NER results
   - Borderline regex matches

2. **Overlapping Detections**
   - Same text detected as different types by multiple tiers
   - Needs disambiguation

3. **Context-Dependent Cases**
   - Names that could be common words (e.g., "May" as name vs. month)
   - Locations that could be organization names

## Performance

### CPU Performance (No GPU Required)

✅ **Yes, Tier 3 works perfectly on CPU!** No GPU needed.

**Expected Performance on CPU:**
- **Latency**: ~1-3 seconds per validation (CPU)
- **Throughput**: 3-8 validations/second (CPU)
- **Memory**: ~2-4GB RAM (depending on model)
- **Disk**: ~2-7GB for model storage

**With GPU (if available):**
- **Latency**: ~0.1-0.5 seconds per validation (GPU)
- **Throughput**: 20-50 validations/second (GPU)
- **Memory**: ~2-4GB VRAM

**Note**: The system automatically detects CPU vs GPU and uses the best available option.

### Optimization Tips

1. **Use quantization** - Install `bitsandbytes` for 8-bit models (faster, less memory)
2. **Adjust confidence threshold** - Higher threshold = fewer validations = faster
3. **Use GPU** - Set `device="cuda"` if available (10x faster)
4. **Batch processing** - Process multiple texts together (future enhancement)

## Troubleshooting

### Model Download Issues

If model download fails:

```bash
# Set Hugging Face token (if needed for gated models)
export HF_TOKEN=your_token_here

# Or download manually
python -c "from transformers import AutoModelForCausalLM; AutoModelForCausalLM.from_pretrained('microsoft/Phi-3-mini-4k-instruct')"
```

### Out of Memory

If you get OOM errors:

1. Use quantization: `use_quantization=True`
2. Use smaller model: `microsoft/Phi-3-mini-4k-instruct`
3. Reduce `max_length` parameter
4. Use CPU instead of GPU

### Slow Performance

1. Install `bitsandbytes` for quantization
2. Use GPU if available
3. Increase `confidence_threshold` to validate fewer cases
4. Consider using only Tier 1 & 2 for high-confidence scenarios

## Example: Ambiguous Case Validation

```python
from src.pipeline import HIPAAPipeline

pipeline = HIPAAPipeline(enable_tier3=True)

# Ambiguous case: "May" could be a name or a month
text = "Patient May reported symptoms in May 2024. SSN: 123-45-6789"

results = pipeline.detect(text)

# Tier 3 will:
# 1. Identify "May" as ambiguous (low confidence name detection)
# 2. Validate using SLM with context
# 3. Correctly classify first "May" as name, second as date
```

## Disabling Tier 3

If you don't need Tier 3 validation:

```python
# Disable Tier 3 (default)
pipeline = HIPAAPipeline(enable_tier3=False)

# Or don't install transformers/torch
# Tier 3 will be automatically disabled
```

## Next Steps

- See `docs/TIER3_PLAN.md` for detailed architecture
- Check `tests/test_slm_validator.py` for usage examples
- Review `src/validators/slm_validator.py` for implementation details

