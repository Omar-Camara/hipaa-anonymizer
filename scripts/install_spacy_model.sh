#!/bin/bash
# Install spaCy English model (works around version issues)

set -e

echo "📦 Installing spaCy English model..."

# Try different installation methods
if python -m spacy download en_core_web_sm 2>/dev/null; then
    echo "✅ Model installed via spacy download"
elif pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl 2>/dev/null; then
    echo "✅ Model installed via direct download"
else
    echo "⚠️  Could not install en_core_web_sm automatically"
    echo ""
    echo "Try manually:"
    echo "  pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl"
    echo ""
    echo "Or check available versions at:"
    echo "  https://github.com/explosion/spacy-models/releases"
    exit 1
fi

# Test installation
echo ""
echo "🧪 Testing model..."
if python -c "import spacy; nlp = spacy.load('en_core_web_sm'); print('✅ Model works!')" 2>/dev/null; then
    echo "✅ Installation successful!"
else
    echo "❌ Model installed but failed to load"
    exit 1
fi

