#!/bin/bash
# Script to install the biomedical NER model for Tier 2

set -e

echo "🔬 Installing biomedical NER model for Tier 2..."
echo ""

# Check if spaCy is installed
if ! python -c "import spacy" 2>/dev/null; then
    echo "❌ spaCy is not installed. Installing..."
    pip install "spacy>=3.7.0"
fi

# Get spaCy version
SPACY_VERSION=$(python -c "import spacy; print(spacy.__version__)" 2>/dev/null | cut -d. -f1,2)
echo "📦 Detected spaCy version: $SPACY_VERSION"

# Install scispaCy
echo "📥 Installing scispaCy..."
pip install scispacy

# Try to install the model
echo "📥 Installing en_core_sci_sm model..."

# Try different installation methods based on spaCy version
if python -m pip install "en-core-sci-sm" 2>/dev/null; then
    echo "✅ Model installed via PyPI"
elif python -m pip install "https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.3/en_core_sci_sm-0.5.3.tar.gz" 2>/dev/null; then
    echo "✅ Model installed via direct download (v0.5.3)"
else
    echo "⚠️  Could not install en_core_sci_sm automatically."
    echo ""
    echo "Please try one of these methods:"
    echo ""
    echo "Method 1: Install from PyPI (if available for your spaCy version):"
    echo "  pip install en-core-sci-sm"
    echo ""
    echo "Method 2: Install specific version:"
    echo "  pip install https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.3/en_core_sci_sm-0.5.3.tar.gz"
    echo ""
    echo "Method 3: Use standard English model as fallback:"
    echo "  python -m spacy download en_core_web_sm"
    echo "  Then use: NERDetector(model_name='en_core_web_sm')"
    exit 1
fi

# Test the installation
echo ""
echo "🧪 Testing model installation..."
if python -c "import spacy; nlp = spacy.load('en_core_sci_sm'); print('✓ Model loaded successfully')" 2>/dev/null; then
    echo "✅ Model installed and working!"
else
    echo "❌ Model installed but failed to load. Check error messages above."
    exit 1
fi

echo ""
echo "🎉 Installation complete! Tier 2 NER detector is ready to use."

