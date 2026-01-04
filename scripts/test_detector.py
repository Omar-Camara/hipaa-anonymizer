#!/usr/bin/env python3
"""
Interactive CLI script for testing the HIPAA Anonymizer detectors.

Usage:
    python scripts/test_detector.py
    python scripts/test_detector.py --text "Your text here"
    python scripts/test_detector.py --file sample_notes.txt
"""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.detectors.regex_detector import RegexDetector


def format_results(results):
    """Format detection results for display."""
    if not results:
        return "No PHI detected."
    
    output = []
    output.append(f"\n{'='*60}")
    output.append(f"Detected {len(results)} PHI identifier(s):")
    output.append(f"{'='*60}\n")
    
    for i, result in enumerate(results, 1):
        output.append(f"{i}. Type: {result['type'].upper()}")
        output.append(f"   Value: {result['value']}")
        output.append(f"   Position: {result['start']}-{result['end']}")
        output.append(f"   Confidence: {result['confidence']:.2f}")
        output.append("")
    
    return "\n".join(output)


def highlight_phi(text, results):
    """Create a version of text with PHI highlighted."""
    if not results:
        return text
    
    # Sort by start position (reverse to avoid index shifting)
    sorted_results = sorted(results, key=lambda x: x['start'], reverse=True)
    
    highlighted = text
    for result in sorted_results:
        start = result['start']
        end = result['end']
        value = result['value']
        phi_type = result['type'].upper()
        
        # Insert highlight markers
        highlighted = (
            highlighted[:start] + 
            f"[{phi_type}:{value}]" + 
            highlighted[end:]
        )
    
    return highlighted


def main():
    parser = argparse.ArgumentParser(
        description="Test HIPAA PHI Detection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python scripts/test_detector.py
  
  # Test specific text
  python scripts/test_detector.py --text "Patient SSN: 123-45-6789"
  
  # Test from file
  python scripts/test_detector.py --file sample_notes.txt
        """
    )
    
    parser.add_argument(
        '--text',
        type=str,
        help='Text to analyze for PHI'
    )
    
    parser.add_argument(
        '--file',
        type=str,
        help='File containing text to analyze'
    )
    
    parser.add_argument(
        '--highlight',
        action='store_true',
        help='Show text with PHI highlighted'
    )
    
    args = parser.parse_args()
    
    # Initialize detector
    print("Initializing Regex Detector...")
    detector = RegexDetector()
    print("✓ Detector ready\n")
    
    # Get input text
    if args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                text = f.read()
            print(f"Loaded text from: {args.file}\n")
        except FileNotFoundError:
            print(f"Error: File not found: {args.file}")
            sys.exit(1)
    elif args.text:
        text = args.text
        print(f"Input text: {text}\n")
    else:
        # Interactive mode
        print("Interactive Mode - Enter text to analyze (Ctrl+D or Ctrl+C to exit)")
        print("-" * 60)
        try:
            lines = []
            while True:
                try:
                    line = input()
                    lines.append(line)
                except EOFError:
                    break
            text = "\n".join(lines)
            if not text.strip():
                print("\nNo text provided. Exiting.")
                sys.exit(0)
        except KeyboardInterrupt:
            print("\n\nExiting.")
            sys.exit(0)
    
    # Detect PHI
    print("Analyzing text for PHI...")
    results = detector.detect_all(text)
    
    # Display results
    print(format_results(results))
    
    # Show highlighted version if requested
    if args.highlight and results:
        print("\n" + "="*60)
        print("Text with PHI highlighted:")
        print("="*60)
        print(highlight_phi(text, results))
    
    # Summary by type
    if results:
        type_counts = {}
        for result in results:
            phi_type = result['type']
            type_counts[phi_type] = type_counts.get(phi_type, 0) + 1
        
        print("\n" + "="*60)
        print("Summary by PHI type:")
        print("="*60)
        for phi_type, count in sorted(type_counts.items()):
            print(f"  {phi_type.upper()}: {count}")


if __name__ == "__main__":
    main()

