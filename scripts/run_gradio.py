#!/usr/bin/env python3
"""
Standalone Gradio UI launcher.

Usage:
    python scripts/run_gradio.py
    # Or
    python -m src.ui.gradio_app
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.ui.gradio_app import create_interface

if __name__ == "__main__":
    print("🚀 Starting HIPAA Anonymizer Gradio UI...")
    print("📱 UI will be available at: http://localhost:7860")
    print("🛑 Press Ctrl+C to stop\n")
    
    app = create_interface()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )

