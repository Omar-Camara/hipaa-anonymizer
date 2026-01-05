"""
HIPAA PHI Detection Pipeline.

Three-tier detection system:
1. Tier 1: Regex (deterministic patterns)
2. Tier 2: BioBERT NER (contextual understanding)
3. Tier 3: SLM validation (ambiguous cases)
"""

from typing import List, Dict, Optional
from src.detectors.regex_detector import RegexDetector
from src.detectors.ner_detector import NERDetector


class HIPAAPipeline:
    """
    Main pipeline for HIPAA PHI detection and anonymization.
    
    Integrates all three detection tiers and provides unified interface.
    """
    
    def __init__(self, enable_tier2: bool = True):
        """
        Initialize the detection pipeline with all tiers.
        
        Args:
            enable_tier2: If True, enable Tier 2 (NER) detection. 
                         Set to False if spaCy biomedical model is not installed.
        """
        # Tier 1: Regex detector (deterministic)
        self.regex_detector = RegexDetector()
        
        # Tier 2: BioBERT NER (contextual understanding)
        self.ner_detector = None
        if enable_tier2:
            try:
                self.ner_detector = NERDetector()
            except Exception as e:
                print(f"Warning: Tier 2 (NER) not available: {e}")
                print("Continuing with Tier 1 only. Install spaCy biomedical model:")
                print("  python -m spacy download en_core_sci_sm")
        
        # Tier 3: SLM validator (to be implemented)
        # self.slm_validator = None
    
    def detect(self, text: str) -> List[Dict]:
        """
        Detect all PHI in the given text using all available tiers.
        
        Args:
            text: Input text to scan for PHI.
            
        Returns:
            List of detection dictionaries with aggregated results from all tiers.
        """
        results = []
        
        # Tier 1: Regex detection (fast, deterministic)
        regex_results = self.regex_detector.detect_all(text)
        results.extend(regex_results)
        
        # Tier 2: BioBERT NER (contextual understanding)
        if self.ner_detector is not None:
            try:
                ner_results = self.ner_detector.detect(text)
                results.extend(ner_results)
            except Exception as e:
                # Log error but continue with Tier 1 results
                print(f"Warning: Tier 2 detection failed: {e}")
        
        # Tier 3: SLM validation for ambiguous cases (to be implemented)
        # validated_results = self.slm_validator.validate(results, text)
        # results = validated_results
        
        # Deduplicate and merge overlapping detections
        results = self._deduplicate(results)
        
        # Sort by start position
        results.sort(key=lambda x: x['start'])
        
        return results
    
    def _deduplicate(self, results: List[Dict]) -> List[Dict]:
        """
        Remove duplicate detections from multiple tiers.
        
        Prioritizes higher confidence and more specific detections.
        """
        if not results:
            return []
        
        # Sort by confidence (descending), then by specificity
        sorted_results = sorted(
            results,
            key=lambda x: (x.get('confidence', 0), -(x['end'] - x['start'])),
            reverse=True
        )
        
        deduplicated = []
        seen_positions = set()
        
        for result in sorted_results:
            # Create a position key
            pos_key = (result['start'], result['end'], result['type'])
            
            # Check for overlap with existing results
            overlaps = False
            for start, end, _ in seen_positions:
                if not (result['end'] <= start or result['start'] >= end):
                    overlaps = True
                    break
            
            if not overlaps:
                deduplicated.append(result)
                seen_positions.add((result['start'], result['end'], result['type']))
        
        return deduplicated
    
    def anonymize(self, text: str, method: str = "safe_harbor") -> str:
        """
        Anonymize detected PHI in the text.
        
        Args:
            text: Input text containing PHI.
            method: Anonymization method ('safe_harbor', 'pseudonymize', etc.)
            
        Returns:
            Anonymized text with PHI replaced.
        """
        detections = self.detect(text)
        
        # TODO: Implement anonymization strategies
        # For now, just return the text with markers
        # This will be implemented in the anonymizers module
        
        return text

