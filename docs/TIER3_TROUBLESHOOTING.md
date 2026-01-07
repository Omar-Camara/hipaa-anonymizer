# Tier 3 Troubleshooting Guide

## Model Download Issues

### Issue: 401 Unauthorized Error

**Error Message:**
```
HTTP status client error (401 Unauthorized)
```

**Cause:** The model is gated and requires Hugging Face authentication.

**Solution 1: Authenticate with Hugging Face**

```bash
# Install huggingface-hub CLI
pip install huggingface-hub

# Login to Hugging Face
huggingface-cli login

# Enter your Hugging Face token (get it from https://huggingface.co/settings/tokens)
```

**Solution 2: Use Environment Variable**

```bash
# Set your Hugging Face token
export HF_TOKEN=your_token_here

# Or add to .env file
echo "HF_TOKEN=your_token_here" >> .env
```

**Solution 3: Use a Non-Gated Model**

Modify the model selection to use a non-gated model:

```python
from src.validators.slm_validator import SLMValidator

# Use a non-gated model (if available)
validator = SLMValidator(
    model_name="microsoft/Phi-3-mini-4k-instruct",
    # Or try: "meta-llama/Llama-3.2-3B-Instruct" (also may be gated)
)
```

**Solution 4: Disable Tier 3 for Now**

Tier 3 is optional. You can use Tier 1 and Tier 2 without Tier 3:

```python
from src.pipeline import HIPAAPipeline

# Tier 3 disabled by default
pipeline = HIPAAPipeline(enable_tier3=False)
```

## Slow Download Speed

**Issue:** Model download is very slow (hours to complete).

**Solutions:**

1. **Use a faster connection** or download during off-peak hours
2. **Download manually** and place in cache:
   ```bash
   # Model cache location
   ~/.cache/huggingface/hub/
   ```
3. **Use a smaller model** if available
4. **Skip Tier 3** - It's optional for now

## Missing Dependencies

### Issue: accelerate not found

**Error:**
```
Using `bitsandbytes` 8-bit quantization requires Accelerate
```

**Solution:**
```bash
pip install accelerate>=0.26.0
```

Or disable quantization:
```python
validator = SLMValidator(use_quantization=False)
```

## Model Loading Errors

### Issue: Model fails to load after download

**Solutions:**

1. **Clear cache and retry:**
   ```bash
   rm -rf ~/.cache/huggingface/hub/models--microsoft--Phi-3-mini-4k-instruct
   ```

2. **Check disk space** (models are 2-7GB)

3. **Try different model:**
   ```python
   validator = SLMValidator(model_name="meta-llama/Llama-3.2-3B-Instruct")
   ```

## Testing Without Model

You can test Tier 3 logic without downloading models:

```bash
python scripts/test_tier3.py
# Choose option 1: Test without model
```

This tests:
- Ambiguous detection identification
- Prompt generation
- Response parsing
- All logic except actual model inference

## Recommended Approach

For now, **Tier 3 is optional**. The system works perfectly with just Tier 1 and Tier 2:

```python
from src.pipeline import HIPAAPipeline

# Works great without Tier 3
pipeline = HIPAAPipeline(enable_tier2=True, enable_tier3=False)

text = "Patient John Smith, SSN: 123-45-6789"
results = pipeline.detect(text)  # Uses Tier 1 & 2
anonymized = pipeline.anonymize(text)  # Full anonymization
```

Tier 3 adds validation for ambiguous cases, but Tier 1 and Tier 2 handle most PHI detection effectively.

