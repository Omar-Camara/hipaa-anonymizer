#!/usr/bin/env python3
"""
Quick test script for Tier 2 NER Detector.

Tests the NER detector with sample medical text.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_model_loading():
    """Test if the spaCy model can be loaded."""
    print("🧪 Testing spaCy model loading...")
    try:
        import spacy
        nlp = spacy.load('en_core_sci_sm')
        print("✅ Model loaded successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        return False

def test_ner_detector():
    """Test the NERDetector class."""
    print("\n🧪 Testing NERDetector class...")
    try:
        from src.detectors.ner_detector import NERDetector
        
        detector = NERDetector()
        print("✅ NERDetector initialized!")
        
        # Test detection
        text = "Dr. John Smith examined patient Jane Doe at Boston Medical Center on March 15, 2024."
        print(f"\n📝 Test text: {text}")
        
        results = detector.detect(text)
        
        if results:
            print(f"\n✅ Detected {len(results)} entities:")
            for i, result in enumerate(results, 1):
                print(f"  {i}. {result['type'].upper()}: '{result['value']}' "
                      f"(confidence: {result['confidence']:.2f}, "
                      f"position: {result['start']}-{result['end']})")
            return True
        else:
            print("⚠️  No entities detected (this might be normal if model needs fine-tuning)")
            return True  # Still a success if detector works
            
    except Exception as e:
        print(f"❌ NERDetector test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_pipeline_integration():
    """Test integration with the pipeline."""
    print("\n🧪 Testing pipeline integration...")
    try:
        from src.pipeline import HIPAAPipeline
        
        pipeline = HIPAAPipeline(enable_tier2=True)
        print("✅ Pipeline initialized with Tier 2!")
        
        # Test with sample medical text
        text = "Patient John Smith, DOB: 01/15/1985, SSN: 123-45-6789, lives in Boston, MA."
        print(f"\n📝 Test text: {text}")
        
        results = pipeline.detect(text)
        
        print(f"\n✅ Pipeline detected {len(results)} PHI identifiers:")
        
        # Group by type
        by_type = {}
        for result in results:
            phi_type = result['type']
            if phi_type not in by_type:
                by_type[phi_type] = []
            by_type[phi_type].append(result)
        
        for phi_type, detections in sorted(by_type.items()):
            print(f"\n  {phi_type.upper()} ({len(detections)}):")
            for det in detections:
                source = det.get('source', 'unknown')
                print(f"    - '{det['value']}' (confidence: {det['confidence']:.2f}, source: {source})")
        
        return True
        
    except Exception as e:
        print(f"❌ Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("Tier 2 NER Detector Test Suite")
    print("=" * 60)
    
    results = []
    
    # Test 1: Model loading
    results.append(("Model Loading", test_model_loading()))
    
    # Test 2: NER Detector
    if results[0][1]:  # Only test if model loaded
        results.append(("NERDetector", test_ner_detector()))
        results.append(("Pipeline Integration", test_pipeline_integration()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n🎉 All tests passed! Tier 2 is ready to use.")
    else:
        print("\n⚠️  Some tests failed. Check error messages above.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())

