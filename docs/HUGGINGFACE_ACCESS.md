# How to Request Access to Gated Models on Hugging Face

## Step-by-Step Guide

### Step 1: Create/Login to Hugging Face Account

1. Go to https://huggingface.co/join
2. Sign up for a free account (or login if you already have one)
3. Verify your email if required

### Step 2: Request Access to Phi-3 Mini

1. Go to the model page: https://huggingface.co/microsoft/Phi-3-mini-4k-instruct
2. You'll see a message like "You need to request access to this model"
3. Click the **"Request access"** button
4. Fill out the form (usually just requires agreeing to terms)
5. Submit the request
6. **Wait for approval** (usually instant or within a few hours)

### Step 3: Request Access to LLaMA 3.2 3B (Optional)

1. Go to the model page: https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct
2. Click **"Request access"** button
3. Fill out the form and submit
4. Wait for approval

### Step 4: Get Your Access Token

1. Go to https://huggingface.co/settings/tokens
2. Click **"New token"**
3. Choose **"Read"** permissions (sufficient for downloading models)
4. Give it a name (e.g., "hipaa-anonymizer")
5. Click **"Generate token"**
6. **Copy the token immediately** (you won't be able to see it again!)

### Step 5: Authenticate Locally

```bash
# Install huggingface-hub if not already installed
pip install huggingface-hub

# Login with your token
huggingface-cli login

# When prompted, paste your token and press Enter
```

**Alternative: Use Environment Variable**

```bash
# Set token as environment variable
export HF_TOKEN=your_token_here

# Or add to .env file (if using python-dotenv)
echo "HF_TOKEN=your_token_here" >> .env
```

### Step 6: Test Access

```python
from transformers import AutoTokenizer

# Try to load tokenizer (this will test authentication)
try:
    tokenizer = AutoTokenizer.from_pretrained(
        "microsoft/Phi-3-mini-4k-instruct",
        trust_remote_code=True
    )
    print("✅ Access granted! You can now use Tier 3.")
except Exception as e:
    print(f"❌ Error: {e}")
    print("Make sure you've:")
    print("1. Requested access to the model")
    print("2. Been approved")
    print("3. Logged in with: huggingface-cli login")
```

## Quick Reference

### Model URLs

- **Phi-3 Mini**: https://huggingface.co/microsoft/Phi-3-mini-4k-instruct
- **LLaMA 3.2 3B**: https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct

### Important Links

- **Sign up**: https://huggingface.co/join
- **Tokens**: https://huggingface.co/settings/tokens
- **Your models**: https://huggingface.co/models?author=you

## Troubleshooting

### "Access Denied" Error

- Make sure you've **requested access** (not just logged in)
- Check that your request was **approved** (check email or model page)
- Try logging out and back in: `huggingface-cli logout` then `huggingface-cli login`

### "401 Unauthorized" Error

- Verify your token is correct: https://huggingface.co/settings/tokens
- Make sure token has **Read** permissions
- Re-authenticate: `huggingface-cli login`

### "Model Not Found" Error

- Check the model name is correct
- Verify you have access to the model page
- Try accessing the model page in your browser first

## Notes

- **Access is usually instant** for most models, but can take a few hours
- **Tokens never expire** unless you revoke them
- **One token is enough** for all models you have access to
- **Free accounts work fine** - no paid subscription needed

## Alternative: Skip Tier 3

Remember, **Tier 3 is optional**! The system works great with just Tier 1 and Tier 2:

```python
from src.pipeline import HIPAAPipeline

# Works perfectly without Tier 3
pipeline = HIPAAPipeline(enable_tier2=True, enable_tier3=False)
```

You can always add Tier 3 later once you have model access set up.
