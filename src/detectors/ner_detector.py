"""
Tier 2 BioBERT NER Detector for HIPAA PHI Anonymization.

This module provides contextual Named Entity Recognition using BioBERT
to detect PHI that requires medical domain understanding, including
names, locations, dates, and organizations.
"""

import re
from typing import List, Dict, Optional, Tuple

# Optional imports - handle gracefully if not available
try:
    import torch
    from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    torch = None


class NERDetector:
    """
    Detects PHI using BioBERT-based Named Entity Recognition.
    
    Uses pre-trained biomedical models to identify contextual PHI
    including names, locations, dates, and organizations that regex
    patterns cannot reliably detect.
    """
    
    # Label mapping from NER labels to HIPAA categories
    # Supports both standard spaCy labels and biomedical model labels
    LABEL_MAPPING = {
        # Person names (standard spaCy: PERSON)
        'B-PER': 'name',
        'I-PER': 'name',
        'PER': 'name',
        'PERSON': 'name',
        
        # Organizations (standard spaCy: ORG)
        'B-ORG': 'organization',
        'I-ORG': 'organization',
        'ORG': 'organization',
        'ORGANIZATION': 'organization',
        
        # Locations (standard spaCy: GPE, FAC, LOC)
        'B-LOC': 'location',
        'I-LOC': 'location',
        'LOC': 'location',
        'LOCATION': 'location',
        'GPE': 'location',  # Geopolitical entity (standard spaCy)
        'FAC': 'location',  # Facility (standard spaCy)
        
        # Dates (standard spaCy: DATE)
        'B-DATE': 'date',
        'I-DATE': 'date',
        'DATE': 'date',
        'TIME': 'date',
        
        # Medical entities (biomedical models)
        'B-MED': 'medical_record_number',
        'I-MED': 'medical_record_number',
        'MED': 'medical_record_number',
    }
    
    def __init__(
        self,
        model_name: Optional[str] = None,  # Auto-detect best available model
        use_spacy: bool = True,
        confidence_threshold: float = 0.5,
        device: Optional[str] = None
    ):
        """
        Initialize the NER detector.
        
        Args:
            model_name: Name of the model to use. Options:
                - "en_core_sci_sm" (spaCy biomedical model) - Recommended for start
                - "dmis-lab/biobert-base-cased-v1.2" (BioBERT) - Requires fine-tuning
            use_spacy: If True, use spaCy model. If False, use transformers.
            confidence_threshold: Minimum confidence score for detections (0-1).
            device: Device to use ('cuda', 'cpu', or None for auto-detection).
        """
        # Auto-detect model if not specified
        if model_name is None:
            model_name = self._detect_best_model()
        
        self.model_name = model_name
        self.use_spacy = use_spacy
        
        if not use_spacy and not TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "Transformers library not available. Install with: pip install transformers torch"
            )
        
        self.confidence_threshold = confidence_threshold
        
        # Set device
        if device:
            self.device = device
        elif TRANSFORMERS_AVAILABLE and torch and torch.cuda.is_available():
            self.device = 'cuda'
        else:
            self.device = 'cpu'
        
        # Lazy loading - models loaded on first use
        self._tokenizer = None
        self._model = None
        self._nlp = None
        self._ner_pipeline = None
        self._initialized = False
    
    def _detect_best_model(self) -> str:
        """
        Detect the best available spaCy model.
        
        Returns:
            Model name to use.
        """
        import spacy
        
        # Try models in order of preference
        # Standard English model is preferred for general PHI detection
        # (names, locations, organizations, dates)
        preferred_models = [
            "en_core_web_sm",  # Standard English (best for general NER - RECOMMENDED)
            "en_core_sci_sm",  # Biomedical (good for medical terminology, but less accurate for names/locations)
        ]
        
        for model_name in preferred_models:
            try:
                # Try to load the model
                nlp = spacy.load(model_name)
                return model_name
            except (OSError, IOError):
                continue
        
        # Fallback to standard English model
        return "en_core_web_sm"  # Default fallback
    
    def _initialize(self):
        """Lazy initialization of models."""
        if self._initialized:
            return
        
        try:
            if self.use_spacy:
                self._initialize_spacy()
            else:
                self._initialize_transformers()
            self._initialized = True
        except Exception as e:
            raise RuntimeError(
                f"Failed to initialize NER detector: {e}\n"
                f"Make sure you have installed the required model:\n"
                f"  python -m spacy download {self.model_name}"
                if self.use_spacy else
                f"  The model {self.model_name} should be available on Hugging Face"
            )
    
    def _initialize_spacy(self):
        """Initialize spaCy biomedical model."""
        try:
            import spacy
            self._nlp = spacy.load(self.model_name)
        except OSError:
            raise RuntimeError(
                f"spaCy model '{self.model_name}' not found. "
                f"Install it with: python -m spacy download {self.model_name}"
            )
    
    def _initialize_transformers(self):
        """Initialize transformers-based BioBERT model."""
        try:
            # For now, we'll use a general NER model
            # In production, you'd fine-tune BioBERT on i2b2 dataset
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self._model = AutoModelForTokenClassification.from_pretrained(
                self.model_name
            )
            self._model.to(self.device)
            self._model.eval()
            
            # Create NER pipeline
            self._ner_pipeline = pipeline(
                "ner",
                model=self._model,
                tokenizer=self._tokenizer,
                device=0 if self.device == 'cuda' else -1,
                aggregation_strategy="simple"
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to load transformers model '{self.model_name}': {e}"
            )
    
    def detect(self, text: str) -> List[Dict]:
        """
        Detect all PHI entities in the given text.
        
        Args:
            text: Input text to scan for PHI.
            
        Returns:
            List of detection dictionaries, each containing:
            - type: str - HIPAA category (name, location, date, organization, etc.)
            - value: str - The detected text
            - start: int - Start position in text
            - end: int - End position in text
            - confidence: float - Confidence score (0-1)
            - source: str - Detection source ('ner')
        """
        if not text or not text.strip():
            return []
        
        self._initialize()
        
        if self.use_spacy:
            return self._detect_spacy(text)
        else:
            return self._detect_transformers(text)
    
    def _detect_spacy(self, text: str) -> List[Dict]:
        """Detect entities using spaCy model."""
        doc = self._nlp(text)
        results = []
        
        # Common abbreviations that should not be treated as PHI
        common_abbreviations = {
            'ssn', 'mrn', 'dob', 'pid', 'id', 'mr', 'mrs', 'ms', 'dr',
            'ph', 'fax', 'tel', 'email', 'e-mail', 'url', 'ip', 'http',
            'https', 'www', 'api', 'sql', 'xml', 'json', 'csv', 'pdf'
        }
        
        for ent in doc.ents:
            # Skip common abbreviations (often misclassified as organizations)
            ent_text_lower = ent.text.lower().rstrip(':')
            if ent_text_lower in common_abbreviations:
                continue
            
            # Map spaCy label to HIPAA category
            hipaa_type = self._map_label_to_hipaa(ent.label_)
            
            # If generic ENTITY label, try to classify it
            if hipaa_type == 'entity':
                hipaa_type = self._classify_entity(ent.text, text[max(0, ent.start_char-50):ent.end_char+50])
                if not hipaa_type:
                    continue  # Skip if we can't classify it
            
            # Filter false positives
            if hipaa_type == 'date':
                # Skip age expressions like "68-year-old"
                if re.search(r'\d+\s*-\s*year\s*-\s*old', ent.text, re.IGNORECASE):
                    continue
                # Skip zip codes (state + zip like "MA 02118")
                if re.match(r'^[A-Z]{2}\s+\d{5}$', ent.text):
                    continue
                # Skip standalone years (already handled by date regex if needed)
                if re.match(r'^\d{4}$', ent.text.strip()):
                    continue
            
            if hipaa_type == 'name':
                # Skip common false positives
                false_positive_names = {'physician', 'patient', 'doctor', 'nurse', 'nurse practitioner'}
                if ent_text_lower in false_positive_names:
                    continue
                # Remove common prefixes if present (keep the name part)
                # Common prefixes: Dr., Mr., Mrs., Ms., Prof., Professor
                prefixes = ['Dr. ', 'Mr. ', 'Mrs. ', 'Ms. ', 'Prof. ', 'Professor ']
                ent_text = ent.text
                ent_start = ent.start_char
                for prefix in prefixes:
                    if ent.text.startswith(prefix):
                        ent_text = ent.text[len(prefix):]  # Remove prefix
                        ent_start = ent.start_char + len(prefix)
                        break
            
            if hipaa_type and ent.start_char < len(text):
                # Calculate confidence (spaCy doesn't provide confidence by default)
                # Use a heuristic based on entity length and context
                confidence = self._calculate_confidence(ent, text)
                
                if confidence >= self.confidence_threshold:
                    # Use adjusted text/position for names with prefixes
                    if hipaa_type == 'name' and ent_text != ent.text:
                        results.append({
                            'type': hipaa_type,
                            'value': ent_text,
                            'start': ent_start,
                            'end': ent.end_char,
                            'confidence': confidence,
                            'source': 'ner',
                            'subtype': self._get_subtype(ent.label_, hipaa_type)
                        })
                    else:
                        results.append({
                            'type': hipaa_type,
                            'value': ent.text,
                            'start': ent.start_char,
                            'end': ent.end_char,
                            'confidence': confidence,
                            'source': 'ner',
                            'subtype': self._get_subtype(ent.label_, hipaa_type)
                        })
        
        return results
    
    def _detect_transformers(self, text: str) -> List[Dict]:
        """Detect entities using transformers pipeline."""
        # Handle long texts by chunking
        max_length = 512  # Typical BERT max length
        if len(text) <= max_length:
            chunks = [text]
            chunk_offsets = [0]
        else:
            # Simple chunking by sentences
            chunks = self._chunk_text(text, max_length)
            chunk_offsets = self._calculate_chunk_offsets(text, chunks)
        
        results = []
        
        for chunk, offset in zip(chunks, chunk_offsets):
            ner_results = self._ner_pipeline(chunk)
            
            for entity in ner_results:
                hipaa_type = self._map_label_to_hipaa(entity.get('entity_group', ''))
                
                if hipaa_type:
                    confidence = entity.get('score', 0.5)
                    
                    if confidence >= self.confidence_threshold:
                        # Adjust positions for chunk offset
                        start = entity['start'] + offset
                        end = entity['end'] + offset
                        
                        results.append({
                            'type': hipaa_type,
                            'value': entity['word'],
                            'start': start,
                            'end': end,
                            'confidence': float(confidence),
                            'source': 'ner',
                            'subtype': self._get_subtype(entity.get('entity_group', ''), hipaa_type)
                        })
        
        # Merge overlapping entities
        results = self._merge_overlapping(results)
        
        return results
    
    def detect_names(self, text: str) -> List[Dict]:
        """
        Detect person and organization names.
        
        Args:
            text: Input text to scan.
            
        Returns:
            List of name detections.
        """
        all_results = self.detect(text)
        return [r for r in all_results if r['type'] == 'name']
    
    def detect_locations(self, text: str) -> List[Dict]:
        """
        Detect geographic locations.
        
        Args:
            text: Input text to scan.
            
        Returns:
            List of location detections.
        """
        all_results = self.detect(text)
        return [r for r in all_results if r['type'] == 'location']
    
    def detect_dates(self, text: str) -> List[Dict]:
        """
        Detect dates and temporal expressions.
        
        Args:
            text: Input text to scan.
            
        Returns:
            List of date detections.
        """
        all_results = self.detect(text)
        return [r for r in all_results if r['type'] == 'date']
    
    def detect_organizations(self, text: str) -> List[Dict]:
        """
        Detect organization names.
        
        Args:
            text: Input text to scan.
            
        Returns:
            List of organization detections.
        """
        all_results = self.detect(text)
        return [r for r in all_results if r['type'] == 'organization']
    
    def _map_label_to_hipaa(self, label: str) -> Optional[str]:
        """
        Map NER label to HIPAA category.
        
        Args:
            label: NER model label.
            
        Returns:
            HIPAA category or None if not a PHI type.
        """
        # Normalize label
        label = label.upper().replace('_', '-')
        
        # Direct mapping
        if label in self.LABEL_MAPPING:
            return self.LABEL_MAPPING[label]
        
        # Handle generic "ENTITY" label from biomedical models
        # We'll classify these based on heuristics in _classify_entity
        if label == 'ENTITY':
            return 'entity'  # Special marker for later classification
        
        # Check prefix matches (for BIO format)
        for ner_label, hipaa_type in self.LABEL_MAPPING.items():
            if label.startswith(ner_label.split('-')[0]):
                return hipaa_type
        
        return None
    
    def _classify_entity(self, entity_text: str, context: str = "") -> Optional[str]:
        """
        Classify a generic ENTITY into a HIPAA category using heuristics.
        
        Args:
            entity_text: The entity text to classify.
            context: Surrounding context (optional).
            
        Returns:
            HIPAA category or None.
        """
        text_lower = entity_text.lower()
        
        # Exclude common abbreviations that are not PHI
        # These are often misclassified as organizations by NER models
        common_abbreviations = {
            'ssn', 'mrn', 'dob', 'pid', 'id', 'mr', 'mrs', 'ms', 'dr',
            'ph', 'fax', 'tel', 'email', 'e-mail', 'url', 'ip', 'http',
            'https', 'www', 'api', 'sql', 'xml', 'json', 'csv', 'pdf'
        }
        if text_lower in common_abbreviations or text_lower.endswith(':'):
            return None  # Not PHI
        
        # Person name patterns
        if any(title in text_lower for title in ['dr.', 'doctor', 'mr.', 'mrs.', 'ms.', 'professor', 'prof.']):
            return 'name'
        if text_lower in ['patient', 'physician', 'doctor', 'nurse', 'attending']:
            return 'name'  # Medical role words
        
        # Organization patterns
        if any(org_word in text_lower for org_word in ['hospital', 'medical center', 'clinic', 'health', 'healthcare']):
            return 'organization'
        if text_lower.endswith(('hospital', 'center', 'clinic', 'medical')):
            return 'organization'
        
        # Location patterns
        if text_lower in ['boston', 'massachusetts', 'new york', 'california']:
            return 'location'
        if any(loc_word in text_lower for loc_word in ['street', 'avenue', 'road', 'city', 'state']):
            return 'location'
        
        # Date patterns
        if any(month in text_lower for month in ['january', 'february', 'march', 'april', 'may', 'june',
                                                  'july', 'august', 'september', 'october', 'november', 'december']):
            return 'date'
        
        # If it looks like a name (capitalized, 2+ words, or title + name)
        words = entity_text.split()
        if len(words) >= 2 and words[0][0].isupper() and words[1][0].isupper():
            return 'name'
        
        return None
    
    def _calculate_confidence(self, entity, text: str) -> float:
        """
        Calculate confidence score for an entity.
        
        Args:
            entity: spaCy entity object.
            text: Full text.
            
        Returns:
            Confidence score between 0 and 1.
        """
        # Base confidence
        confidence = 0.7
        
        # Boost confidence for longer entities (less likely to be false positive)
        if len(entity.text) > 5:
            confidence += 0.1
        
        # Boost for capitalized entities (likely names/locations)
        if entity.text[0].isupper():
            confidence += 0.1
        
        # Reduce confidence for very short entities
        if len(entity.text) < 3:
            confidence -= 0.2
        
        return min(1.0, max(0.0, confidence))
    
    def _get_subtype(self, label: str, hipaa_type: str) -> Optional[str]:
        """Get entity subtype if available."""
        label_upper = label.upper()
        
        if hipaa_type == 'name':
            if 'ORG' in label_upper:
                return 'organization'
            elif 'PER' in label_upper or 'PERSON' in label_upper:
                return 'person'
        
        return None
    
    def _chunk_text(self, text: str, max_length: int) -> List[str]:
        """Split text into chunks for processing."""
        # Simple sentence-based chunking
        sentences = re.split(r'[.!?]\s+', text)
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence)
            if current_length + sentence_length > max_length and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [sentence]
                current_length = sentence_length
            else:
                current_chunk.append(sentence)
                current_length += sentence_length + 1
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks if chunks else [text]
    
    def _calculate_chunk_offsets(self, text: str, chunks: List[str]) -> List[int]:
        """Calculate character offsets for chunks."""
        offsets = [0]
        current_offset = 0
        
        for chunk in chunks[:-1]:
            # Find the chunk in the original text
            idx = text.find(chunk, current_offset)
            if idx != -1:
                current_offset = idx + len(chunk)
                offsets.append(current_offset)
            else:
                # Fallback: estimate offset
                current_offset += len(chunk)
                offsets.append(current_offset)
        
        return offsets
    
    def _merge_overlapping(self, results: List[Dict]) -> List[Dict]:
        """Merge overlapping entities, keeping highest confidence."""
        if not results:
            return []
        
        # Sort by start position
        sorted_results = sorted(results, key=lambda x: x['start'])
        merged = []
        
        for result in sorted_results:
            if not merged:
                merged.append(result)
            else:
                last = merged[-1]
                # Check for overlap
                if result['start'] < last['end']:
                    # Overlap detected - keep higher confidence
                    if result['confidence'] > last['confidence']:
                        merged[-1] = result
                else:
                    merged.append(result)
        
        return merged

