# Virtual Environment Setup Guide

## Quick Setup

Run the setup script:

```bash
./scripts/setup_venv.sh
```

This will:
1. Create a virtual environment using Python 3.11 (if available)
2. Install all project dependencies
3. Install scispaCy and the biomedical NER model
4. Test the installation

## Manual Setup

If you prefer to set up manually:

```bash
# Create virtual environment with Python 3.11 (recommended)
python3.11 -m venv venv

# Or use your default Python 3
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install project dependencies
pip install -r requirements.txt

# Install scispaCy
pip install scispacy

# Install the biomedical NER model
pip install en-core-sci-sm
# Or if that doesn't work:
# pip install https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.3/en_core_sci_sm-0.5.3.tar.gz
```

## Using the Virtual Environment

### Activate

```bash
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt.

### Deactivate

```bash
deactivate
```

### Verify Installation

```bash
# Test that you're using the venv Python
which python
# Should show: .../hipaa-anonymizer/venv/bin/python

# Test spaCy model
python -c "import spacy; nlp = spacy.load('en_core_sci_sm'); print('✅ Model works!')"

# Run the test suite
python scripts/test_ner.py
```

## IDE Integration

### VS Code

1. Open the project in VS Code
2. Press `Cmd+Shift+P` (Mac) or `Ctrl+Shift+P` (Windows/Linux)
3. Type "Python: Select Interpreter"
4. Choose the interpreter from `venv/bin/python`

### PyCharm

1. File → Settings → Project → Python Interpreter
2. Click the gear icon → Add
3. Select "Existing environment"
4. Browse to `venv/bin/python`

## Troubleshooting

### "Command not found: python3.11"

If Python 3.11 isn't available, use Python 3:

```bash
python3 -m venv venv
```

### Model installation fails

Try installing the model directly:

```bash
source venv/bin/activate
pip install https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.3/en_core_sci_sm-0.5.3.tar.gz
```

### Wrong Python version in venv

Recreate the virtual environment:

```bash
rm -rf venv
python3.11 -m venv venv  # or python3
source venv/bin/activate
pip install -r requirements.txt
```

## Best Practices

1. **Always activate the venv** before running scripts
2. **Commit `requirements.txt`** but **never commit `venv/`** (already in .gitignore)
3. **Update requirements** when adding new packages:
   ```bash
   pip freeze > requirements.txt
   ```
4. **Use the venv Python** for all project work

## Optional: Automatic Activation with direnv

If you use `direnv`, you can automatically activate the venv when you `cd` into the project:

```bash
# Install direnv
brew install direnv  # Mac
# or: sudo apt install direnv  # Linux

# Add to ~/.zshrc or ~/.bashrc
echo 'eval "$(direnv hook zsh)"' >> ~/.zshrc

# The .envrc file in the project root will auto-activate the venv
```

