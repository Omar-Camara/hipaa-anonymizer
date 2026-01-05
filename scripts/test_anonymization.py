#!/usr/bin/env python3
"""
Test script for anonymization functionality.

Demonstrates Safe Harbor, pseudonymization, and redaction methods.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline import HIPAAPipeline


def main():
    print("=" * 70)
    print("HIPAA Anonymization Test")
    print("=" * 70)
    
    # Initialize pipeline
    pipeline = HIPAAPipeline(enable_tier2=True)
    
    # Sample medical text with PHI
    text = """
    PATIENT MEDICAL RECORD
    
    Patient Name: John Smith
    Date of Birth: 01/15/1985
    Social Security Number: 123-45-6789
    Medical Record Number: MR-123456
    
    Contact Information:
    - Phone: (555) 123-4567
    - Email: john.smith@hospital.com
    - Address: 123 Main Street, Boston, MA 02115
    
    Emergency Contact:
    - Name: Jane Smith
    - Phone: 555-987-6543
    - Email: jane.smith+emergency@example.com
    
    Clinical Notes:
    The patient presented with chest pain. Blood pressure was 140/90.
    Patient reports taking medications including Lisinopril 10mg daily.
    Previous visit on 03/15/2024 showed similar symptoms.
    """
    
    print("\n📝 Original Text:")
    print("-" * 70)
    print(text)
    
    # Test Safe Harbor (default)
    print("\n" + "=" * 70)
    print("1. Safe Harbor Anonymization (HIPAA Standard)")
    print("=" * 70)
    safe_harbor = pipeline.anonymize(text, method="safe_harbor")
    print(safe_harbor)
    
    # Test Pseudonymization
    print("\n" + "=" * 70)
    print("2. Pseudonymization (Consistent Replacements)")
    print("=" * 70)
    pseudonymized = pipeline.anonymize(text, method="pseudonymize")
    print(pseudonymized)
    
    # Test Redaction
    print("\n" + "=" * 70)
    print("3. Redaction (Complete Removal)")
    print("=" * 70)
    redacted = pipeline.anonymize(text, redact=True)
    print(redacted)
    
    # Test Tagged Format
    print("\n" + "=" * 70)
    print("4. Tagged Format ([TYPE:N])")
    print("=" * 70)
    tagged = pipeline.anonymize(text, tag=True)
    print(tagged)
    
    # Test with metadata
    print("\n" + "=" * 70)
    print("5. Anonymization with Metadata")
    print("=" * 70)
    result = pipeline.anonymize_with_metadata(text, method="safe_harbor")
    
    print(f"\n📊 Statistics:")
    print(f"  Total PHI detected: {result['statistics']['total_phi']}")
    print(f"\n  By Type:")
    for phi_type, count in sorted(result['statistics']['by_type'].items()):
        print(f"    {phi_type}: {count}")
    print(f"\n  By HIPAA Category:")
    for category, count in sorted(result['statistics']['by_hipaa_category'].items()):
        print(f"    {category}: {count}")
    
    # Show pseudonym consistency
    print("\n" + "=" * 70)
    print("6. Pseudonym Consistency Test")
    print("=" * 70)
    # Use simpler text to avoid "SSN:" being detected as organization
    text1 = "Patient John Smith, 123-45-6789"
    text2 = "Another record: John Smith, 123-45-6789"
    
    # Get detections first to see what's detected
    detections1 = pipeline.detect(text1)
    detections2 = pipeline.detect(text2)
    
    result1 = pipeline.anonymize(text1, method="pseudonymize")
    result2 = pipeline.anonymize(text2, method="pseudonymize")
    
    print(f"Text 1: {text1}")
    print(f"Detections: {len(detections1)} PHI found")
    for d in detections1:
        print(f"  - {d['type']}: '{d['value']}'")
    print(f"Result: {result1}")
    
    print(f"\nText 2: {text2}")
    print(f"Detections: {len(detections2)} PHI found")
    for d in detections2:
        print(f"  - {d['type']}: '{d['value']}'")
    print(f"Result: {result2}")
    
    # Extract SSN pseudonyms using regex (format: XXX-XX-XXXX)
    import re
    ssn_pattern = r'\d{3}-\d{2}-\d{4}'
    ssn1 = re.findall(ssn_pattern, result1)
    ssn2 = re.findall(ssn_pattern, result2)
    
    if ssn1 and ssn2:
        consistent = ssn1[0] == ssn2[0]
        print(f"\n✅ SSN Pseudonym Consistency:")
        print(f"   Text 1 SSN: {ssn1[0]}")
        print(f"   Text 2 SSN: {ssn2[0]}")
        print(f"   Same pseudonym: {consistent}")
    else:
        print(f"\n⚠️  Could not extract SSN pseudonyms for comparison")
    
    # Also check name consistency
    # Look for name patterns (two capitalized words, excluding common words)
    # Extract the actual pseudonymized names (not surrounding context)
    name_pattern = r'\b([A-Z][a-z]+ [A-Z][a-z]+)\b'
    name1_matches = re.findall(name_pattern, result1)
    name2_matches = re.findall(name_pattern, result2)
    
    # Filter out common non-name words
    exclude_words = {'Patient', 'Another', 'Medical', 'Record', 'Contact', 'Emergency', 
                     'Clinical', 'Previous', 'Social', 'Security', 'Number'}
    
    name1 = [n for n in name1_matches if not any(word in n for word in exclude_words)]
    name2 = [n for n in name2_matches if not any(word in n for word in exclude_words)]
    
    if name1 and name2:
        # Check if any name pseudonym appears in both results
        name_consistent = any(n1 == n2 for n1 in name1 for n2 in name2)
        print(f"\n✅ Name Pseudonym Consistency:")
        print(f"   Text 1 Names: {', '.join(name1)}")
        print(f"   Text 2 Names: {', '.join(name2)}")
        if name_consistent:
            common_names = [n for n in name1 if n in name2]
            print(f"   Common pseudonym(s): {', '.join(common_names)}")
        print(f"   Same pseudonym: {name_consistent}")


if __name__ == "__main__":
    main()

