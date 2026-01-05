#!/usr/bin/env python3
"""Test NER detector with clinical/medical text."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline import HIPAAPipeline

# Clinical text examples
clinical_texts = [
    # Example 1: Clinical note format
    """
    PATIENT: John Smith
    DOB: 01/15/1985
    MRN: 12345678
    
    Chief Complaint: Chest pain
    
    History of Present Illness:
    Patient is a 38-year-old male presenting to the emergency department 
    at Massachusetts General Hospital with acute chest pain. Patient reports 
    pain started this morning. Previous admission on March 15, 2024 showed 
    similar symptoms.
    
    Assessment: Acute coronary syndrome
    Plan: Admit to cardiology service. Contact Dr. Sarah Johnson for consultation.
    """,
    
    # Example 2: Discharge summary
    """
    DISCHARGE SUMMARY
    
    Patient Name: Jane Doe
    Date of Birth: 05/20/1975
    Admission Date: 03/10/2024
    Discharge Date: 03/12/2024
    Attending Physician: Dr. Michael Chen
    
    The patient was admitted to Boston Medical Center for evaluation of 
    abdominal pain. Laboratory studies were obtained. Patient was seen 
    by Dr. Emily Rodriguez from gastroenterology.
    
    Discharge medications prescribed. Follow-up scheduled with primary 
    care physician Dr. Robert Williams at Harvard Medical Center.
    """,
    
    # Example 3: Lab results
    """
    LABORATORY RESULTS
    
    Patient: Mary Johnson
    Ordering Physician: Dr. David Lee
    Collection Date: March 18, 2024
    
    Complete Blood Count ordered. Results reviewed by Dr. Lisa Anderson.
    Patient contacted at phone number (617) 555-1234.
    """
]

def main():
    print("=" * 70)
    print("Testing Tier 2 NER with Clinical/Medical Text")
    print("=" * 70)
    
    pipeline = HIPAAPipeline(enable_tier2=True)
    
    for i, text in enumerate(clinical_texts, 1):
        print(f"\n{'='*70}")
        print(f"Example {i}: Clinical Note")
        print(f"{'='*70}")
        print(f"Text length: {len(text)} characters")
        
        results = pipeline.detect(text)
        
        # Group by type and source
        by_type = {}
        for result in results:
            phi_type = result['type']
            source = result.get('source', 'regex')
            key = f"{phi_type} ({source})"
            if key not in by_type:
                by_type[key] = []
            by_type[key].append(result)
        
        print(f"\n✅ Detected {len(results)} PHI identifiers:\n")
        
        for key, detections in sorted(by_type.items()):
            print(f"  {key.upper()} ({len(detections)}):")
            for det in detections[:5]:  # Show first 5
                print(f"    - '{det['value']}' "
                      f"(confidence: {det['confidence']:.2f}, "
                      f"pos: {det['start']}-{det['end']})")
            if len(detections) > 5:
                print(f"    ... and {len(detections) - 5} more")
        
        # Show breakdown by source
        tier1_count = sum(1 for r in results if r.get('source') != 'ner')
        tier2_count = sum(1 for r in results if r.get('source') == 'ner')
        print(f"\n  Breakdown: Tier 1 (regex): {tier1_count}, Tier 2 (NER): {tier2_count}")

if __name__ == "__main__":
    main()

