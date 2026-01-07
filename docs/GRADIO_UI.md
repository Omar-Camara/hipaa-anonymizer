# Gradio UI Guide

The HIPAA Anonymizer includes a user-friendly Gradio web interface for easy testing and demonstration.

## Quick Start

### Option 1: Standalone Gradio UI

Run the Gradio interface independently:

```bash
# Activate virtual environment
source venv/bin/activate

# Launch Gradio UI
python scripts/run_gradio.py
```

The UI will be available at: **http://localhost:7860**

### Option 2: Integrated with FastAPI

The Gradio UI is automatically mounted when running the FastAPI server:

```bash
# Start FastAPI server
uvicorn src.api.main:app --reload --port 8000

# Access UI at: http://localhost:8000/ui
# Access API docs at: http://localhost:8000/docs
```

## Features

### 🔍 Detect PHI Tab

- **Input**: Paste or type text containing PHI
- **Tier 2 (NER)**: Toggle contextual understanding (names, locations, dates)
- **Tier 3 (SLM)**: Toggle SLM validation for ambiguous cases (optional)
- **Output**: 
  - List of detected PHI with positions, confidence scores, and sources
  - Statistics showing total PHI and breakdown by type

### 🛡️ Anonymize Tab

- **Input**: Paste or type text containing PHI
- **Method Selection**:
  - **Safe Harbor**: HIPAA-compliant placeholders (e.g., `[SSN]`, `[NAME]`)
  - **Pseudonymize**: Consistent replacements (same PHI → same pseudonym)
  - **Redact**: Complete removal of PHI
  - **Tag**: Numbered placeholders (e.g., `[NAME:1]`, `[SSN:2]`)
- **Output**:
  - Anonymized text
  - Detected PHI list (optional)
  - Statistics

### ℹ️ About Tab

- System overview
- Detection tier explanations
- Anonymization method descriptions
- HIPAA compliance information

## Example Usage

### Example 1: Simple Detection

1. Go to **Detect PHI** tab
2. Enter text: `Patient John Smith, SSN: 123-45-6789, phone: (555) 123-4567`
3. Enable Tier 2
4. Click **Detect PHI**
5. See detected PHI with positions and confidence scores

### Example 2: Anonymization

1. Go to **Anonymize** tab
2. Enter text: `Dr. Sarah Johnson from Memorial Hospital treated patient Robert Williams`
3. Select method: **Safe Harbor**
4. Enable Tier 2
5. Check **Show Detections**
6. Click **Anonymize**
7. See anonymized text: `Dr. [NAME] from [ORGANIZATION] treated patient [NAME]`

### Example 3: Using Examples

1. Go to **Anonymize** tab
2. Scroll to **Example Texts** section
3. Click any example to load it
4. Click **Anonymize** to see results

## Configuration

### Port Configuration

To change the port for standalone Gradio:

```python
# Edit scripts/run_gradio.py
app.launch(server_port=8080)  # Change from 7860 to 8080
```

### Theme Customization

The UI uses Gradio's `Soft` theme. To change:

```python
# Edit src/ui/gradio_app.py
with gr.Blocks(title="HIPAA Anonymizer", theme=gr.themes.Monochrome()) as app:
    # ... or use gr.themes.Default(), gr.themes.Glass(), etc.
```

## Docker Integration

The Gradio UI is automatically available when running in Docker:

```bash
# Start Docker container
docker compose up

# Access UI at: http://localhost:8000/ui
```

## Troubleshooting

### UI Not Loading

1. **Check if Gradio is installed:**
   ```bash
   pip install gradio
   ```

2. **Check port availability:**
   ```bash
   lsof -i :7860  # For standalone
   lsof -i :8000  # For integrated
   ```

3. **Check logs:**
   ```bash
   # For standalone
   python scripts/run_gradio.py
   
   # For integrated
   uvicorn src.api.main:app --reload
   ```

### Tier 3 Not Available

If Tier 3 checkbox is enabled but not working:
- Models need to be downloaded (~2-7GB)
- Requires `transformers` and `torch` installed
- First use will download models automatically
- See [Tier 3 Setup Guide](TIER3_SETUP.md) for details

### Performance Issues

- **Slow detection**: Disable Tier 3 if not needed
- **Memory issues**: Reduce batch size or disable Tier 3
- **Network timeouts**: Check internet connection for model downloads

## API vs UI

Both interfaces provide the same functionality:

- **Gradio UI**: User-friendly, visual, great for demos
- **REST API**: Programmatic access, integration, automation

You can use both simultaneously - they share the same pipeline backend.

## Next Steps

- Try the example texts
- Test with your own medical text samples
- Compare different anonymization methods
- Enable Tier 3 for ambiguous case validation
- Use the API for programmatic access

## Additional Resources

- [API Guide](API_GUIDE.md) - REST API documentation
- [API Testing](API_TESTING.md) - How to test the API
- [Tier 3 Setup](TIER3_SETUP.md) - SLM validation setup
- [Docker Setup](DOCKER_SETUP.md) - Docker deployment

