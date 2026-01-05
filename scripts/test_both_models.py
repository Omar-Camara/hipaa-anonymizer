#!/usr/bin/env python3
"""Compare both NER models side by side."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.detectors.ner_detector import NERDetector

test_text = "Dr. John Smith examined patient Jane Doe at Boston Medical Center on March 15, 2024."

print("=" * 70)
print("Comparing NER Models")
print("=" * 70)

# Test biomedical model
print("\n📊 Biomedical Model (en_core_sci_sm):")
try:
    detector_bio = NERDetector(model_name="en_core_sci_sm")
    results_bio = detector_bio.detect(test_text)
    print(f"  ✅ Detected {len(results_bio)} entities:")
    for r in results_bio:
        print(f"    - {r['type']}: '{r['value']}' (conf: {r['confidence']:.2f})")
except Exception as e:
    print(f"  ❌ Error: {e}")

# Test standard English model
print("\n📊 Standard English Model (en_core_web_sm):")
try:
    detector_std = NERDetector(model_name="en_core_web_sm")
    results_std = detector_std.detect(test_text)
    print(f"  ✅ Detected {len(results_std)} entities:")
    for r in results_std:
        print(f"    - {r['type']}: '{r['value']}' (conf: {r['confidence']:.2f})")
except Exception as e:
    print(f"  ❌ Error: {e}")

print("\n" + "=" * 70)
print("Recommendation: Use the model that detects the most relevant PHI")
print("=" * 70)

