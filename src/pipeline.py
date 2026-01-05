"""
HIPAA PHI Detection Pipeline.

Three-tier detection system:
1. Tier 1: Regex (deterministic patterns)
2. Tier 2: NER (contextual understanding)
3. Tier 3: SLM validation (ambiguous cases - Small Language Model)
"""

from typing import List, Dict, Optional
from src.detectors.regex_detector import RegexDetector
from src.detectors.ner_detector import NERDetector
from src.anonymizers.safe_harbor import SafeHarborAnonymizer
from src.anonymizers.pseudonymizer import Pseudonymizer
from src.anonymizers.category_tagger import CategoryTagger
from src.validators.slm_validator import SLMValidator


class HIPAAPipeline:
    """
    Main pipeline for HIPAA PHI detection and anonymization.
    
    Integrates all three detection tiers and provides unified interface.
    """
    
    def __init__(self, enable_tier2: bool = True, enable_tier3: bool = False):
        """
        Initialize the detection pipeline with all tiers.
        
        Args:
            enable_tier2: If True, enable Tier 2 (NER) detection. 
                         Set to False if spaCy biomedical model is not installed.
            enable_tier3: If True, enable Tier 3 (SLM validation). 
                         Set to False by default as it requires model download.
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
        
        # Tier 3: SLM validator (for ambiguous cases)
        self.slm_validator = None
        if enable_tier3:
            try:
                self.slm_validator = SLMValidator()
                print("Tier 3 (SLM validation) enabled")
            except Exception as e:
                print(f"Warning: Tier 3 (SLM validation) not available: {e}")
                print("Continuing without Tier 3. To enable:")
                print("  pip install transformers torch")
                print("  Note: Model will be downloaded on first use (~2-7GB)")
        
        # Anonymization components
        self.safe_harbor = SafeHarborAnonymizer()
        self.pseudonymizer = Pseudonymizer()
        self.category_tagger = CategoryTagger()
    
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
        
        # Tier 3: SLM validation for ambiguous cases
        if self.slm_validator is not None and self.slm_validator.is_available():
            try:
                results = self.slm_validator.validate(results, text)
            except Exception as e:
                # Log error but continue with unvalidated results
                print(f"Warning: Tier 3 validation failed: {e}")
        
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
    
    def anonymize(
        self, 
        text: str, 
        method: str = "safe_harbor",
        redact: bool = False,
        tag: bool = False
    ) -> str:
        """
        Anonymize detected PHI in the text.
        
        Args:
            text: Input text containing PHI.
            method: Anonymization method:
                - 'safe_harbor': Replace with generic placeholders (default)
                - 'pseudonymize': Replace with consistent pseudonyms
                - 'redact': Remove PHI entirely
                - 'tag': Replace with tagged placeholders [TYPE:N]
            redact: If True, remove PHI instead of replacing (overrides method).
            tag: If True, use tagged format [TYPE:N] (overrides method).
            
        Returns:
            Anonymized text with PHI replaced or removed.
        """
        detections = self.detect(text)
        
        if not detections:
            return text
        
        # Tag detections with HIPAA categories
        tagged_detections = self.category_tagger.tag(detections)
        
        # Apply anonymization method
        if redact:
            return self.safe_harbor.anonymize_with_redaction(text, tagged_detections)
        elif tag:
            return self.safe_harbor.anonymize_with_tags(text, tagged_detections)
        elif method == "pseudonymize":
            return self.pseudonymizer.pseudonymize(text, tagged_detections)
        else:  # safe_harbor (default)
            return self.safe_harbor.anonymize(text, tagged_detections)
    
    def anonymize_with_metadata(
        self, 
        text: str, 
        method: str = "safe_harbor"
    ) -> Dict:
        """
        Anonymize text and return both anonymized text and metadata.
        
        Args:
            text: Input text containing PHI.
            method: Anonymization method.
            
        Returns:
            Dictionary with:
            - 'anonymized_text': Anonymized text
            - 'detections': List of detected PHI with metadata
            - 'statistics': Anonymization statistics
        """
        detections = self.detect(text)
        tagged_detections = self.category_tagger.tag(detections)
        
        anonymized = self.anonymize(text, method=method)
        
        # Calculate statistics
        stats = {
            'total_phi': len(detections),
            'by_type': {},
            'by_hipaa_category': {},
        }
        
        for det in tagged_detections:
            phi_type = det['type']
            hipaa_cat = det.get('hipaa_category', 'unknown')
            
            stats['by_type'][phi_type] = stats['by_type'].get(phi_type, 0) + 1
            stats['by_hipaa_category'][hipaa_cat] = stats['by_hipaa_category'].get(hipaa_cat, 0) + 1
        
        return {
            'anonymized_text': anonymized,
            'detections': tagged_detections,
            'statistics': stats,
            'original_text': text,
        }

