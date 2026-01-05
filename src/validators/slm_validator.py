"""
Tier 3: SLM Validator for Ambiguous PHI Detection.

Uses a Small Language Model (SLM) to validate and refine ambiguous
detections from Tier 1 and Tier 2.
"""

import re
from typing import List, Dict, Optional, Tuple
import logging

# Optional imports - handle gracefully if not available
try:
    from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    torch = None

logger = logging.getLogger(__name__)


class SLMValidator:
    """
    Validates ambiguous PHI detections using a Small Language Model.
    
    Uses local SLM models (LLaMA 3.2 3B or Phi-3 Mini) to:
    - Validate low-confidence detections
    - Refine PHI type classifications
    - Filter false positives
    - Handle context-dependent cases
    """
    
    # Supported models (in order of preference)
    SUPPORTED_MODELS = [
        "microsoft/Phi-3-mini-4k-instruct",  # Fast, efficient
        "meta-llama/Llama-3.2-3B-Instruct",  # Good balance
    ]
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        confidence_threshold: float = 0.7,
        device: Optional[str] = None,
        max_length: int = 512,
        use_quantization: bool = True
    ):
        """
        Initialize SLM validator.
        
        Args:
            model_name: Name of the model to use. If None, auto-selects best available.
            confidence_threshold: Only validate detections below this confidence.
            device: Device to run on ('cpu', 'cuda', or None for auto-detect).
            max_length: Maximum sequence length for model.
            use_quantization: Use 8-bit quantization for faster inference (if available).
        """
        self.confidence_threshold = confidence_threshold
        self.max_length = max_length
        self.use_quantization = use_quantization
        
        # Auto-detect device
        if device is None:
            if torch is not None and torch.cuda.is_available():
                device = "cuda"
            else:
                device = "cpu"
        self.device = device
        
        # Initialize model
        self._model = None
        self._tokenizer = None
        self._pipeline = None
        self.model_name = None
        
        if not TRANSFORMERS_AVAILABLE:
            raise RuntimeError(
                "Transformers library not available. Install with: pip install transformers torch"
            )
        
        if model_name is None:
            model_name = self._auto_select_model()
        
        self._load_model(model_name)
    
    def _auto_select_model(self) -> str:
        """
        Auto-select the best available model.
        
        Returns:
            Model name string.
        """
        for model in self.SUPPORTED_MODELS:
            try:
                # Try to load tokenizer as a test
                tokenizer = AutoTokenizer.from_pretrained(model, trust_remote_code=True)
                logger.info(f"Auto-selected model: {model}")
                return model
            except Exception as e:
                logger.debug(f"Model {model} not available: {e}")
                continue
        
        raise RuntimeError(
            f"None of the supported models are available: {self.SUPPORTED_MODELS}\n"
            "Please install one of the models or provide a custom model_name."
        )
    
    def _load_model(self, model_name: str):
        """
        Load the SLM model and tokenizer.
        
        Args:
            model_name: Name of the model to load.
        """
        try:
            logger.info(f"Loading SLM model: {model_name}")
            
            # Load tokenizer
            self._tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                trust_remote_code=True
            )
            
            # Configure model loading
            model_kwargs = {
                "trust_remote_code": True,
                "torch_dtype": torch.float16 if self.device == "cuda" else torch.float32,
            }
            
            # Add quantization if requested and available
            if self.use_quantization and self.device == "cpu":
                try:
                    # Check for both bitsandbytes and accelerate (both required)
                    import bitsandbytes
                    import accelerate
                    if hasattr(accelerate, '__version__'):
                        from transformers import BitsAndBytesConfig
                        quantization_config = BitsAndBytesConfig(
                            load_in_8bit=True,
                            llm_int8_threshold=6.0
                        )
                        model_kwargs["quantization_config"] = quantization_config
                    else:
                        raise ImportError("accelerate version check failed")
                except (ImportError, AttributeError):
                    logger.warning("bitsandbytes or accelerate not available, skipping quantization")
                    # Remove quantization_config if it was added
                    model_kwargs.pop("quantization_config", None)
            
            # Load model
            self._model = AutoModelForCausalLM.from_pretrained(
                model_name,
                **model_kwargs
            )
            
            # Move to device
            if self.device == "cpu":
                self._model = self._model.to(self.device)
            
            # Create pipeline
            self._pipeline = pipeline(
                "text-generation",
                model=self._model,
                tokenizer=self._tokenizer,
                device=0 if self.device == "cuda" else -1,
                max_length=self.max_length,
            )
            
            self.model_name = model_name
            logger.info(f"Successfully loaded model: {model_name}")
            
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            raise RuntimeError(f"Failed to load SLM model: {e}")
    
    def validate(
        self,
        detections: List[Dict],
        text: str,
        context_window: int = 100
    ) -> List[Dict]:
        """
        Validate ambiguous detections using SLM.
        
        Args:
            detections: List of PHI detections from Tier 1 & 2.
            text: Original text containing the detections.
            context_window: Number of characters of context to include around detection.
            
        Returns:
            List of validated detections (filtered and refined).
        """
        if not detections:
            return []
        
        # Identify ambiguous detections
        ambiguous = self._identify_ambiguous(detections)
        
        if not ambiguous:
            return detections  # No ambiguous cases, return as-is
        
        logger.info(f"Validating {len(ambiguous)} ambiguous detections")
        
        validated = []
        validated_indices = set()
        
        for idx, detection in enumerate(detections):
            if idx in ambiguous:
                # Validate ambiguous detection
                result = self._validate_single(detection, text, context_window)
                if result:
                    validated.append(result)
                    validated_indices.add(idx)
            else:
                # Keep non-ambiguous detections as-is
                validated.append(detection)
                validated_indices.add(idx)
        
        return validated
    
    def _identify_ambiguous(self, detections: List[Dict]) -> set:
        """
        Identify which detections are ambiguous and need validation.
        
        Args:
            detections: List of detections.
            
        Returns:
            Set of indices for ambiguous detections.
        """
        ambiguous = set()
        
        for idx, detection in enumerate(detections):
            confidence = detection.get('confidence', 1.0)
            
            # Low confidence detections
            if confidence < self.confidence_threshold:
                ambiguous.add(idx)
                continue
            
            # Check for overlapping detections (same text, different types)
            for other_idx, other in enumerate(detections):
                if idx == other_idx:
                    continue
                
                # Check if detections overlap
                if self._overlaps(detection, other):
                    if detection.get('type') != other.get('type'):
                        ambiguous.add(idx)
                        ambiguous.add(other_idx)
        
        return ambiguous
    
    def _overlaps(self, det1: Dict, det2: Dict) -> bool:
        """Check if two detections overlap in position."""
        return not (
            det1['end'] <= det2['start'] or
            det1['start'] >= det2['end']
        )
    
    def _validate_single(
        self,
        detection: Dict,
        text: str,
        context_window: int
    ) -> Optional[Dict]:
        """
        Validate a single ambiguous detection.
        
        Args:
            detection: Detection to validate.
            text: Original text.
            context_window: Context window size.
            
        Returns:
            Validated detection dict or None if rejected.
        """
        # Extract context
        start = max(0, detection['start'] - context_window)
        end = min(len(text), detection['end'] + context_window)
        context = text[start:end]
        detected_text = detection['value']
        detected_type = detection.get('type', 'unknown')
        confidence = detection.get('confidence', 0.5)
        
        # Generate prompt
        prompt = self._create_validation_prompt(
            context, detected_text, detected_type, confidence
        )
        
        try:
            # Generate response
            response = self._generate_response(prompt)
            
            # Parse response
            is_phi, refined_type = self._parse_response(response)
            
            if not is_phi:
                # False positive - reject detection
                logger.debug(f"Rejected false positive: {detected_text}")
                return None
            
            # Update detection with refined information
            validated = detection.copy()
            validated['validated'] = True  # Mark as validated by SLM
            
            if refined_type and refined_type != detected_type:
                validated['type'] = refined_type
                validated['original_type'] = detected_type
                logger.debug(f"Refined type: {detected_type} -> {refined_type}")
            elif refined_type:
                # Type confirmed (same as detected)
                validated['type'] = refined_type
            
            validated['confidence'] = min(1.0, confidence + 0.2)  # Boost confidence
            validated['source'] = 'slm_validated'
            
            return validated
            
        except Exception as e:
            logger.warning(f"Validation failed for {detected_text}: {e}")
            # On error, keep original detection
            return detection
    
    def _create_validation_prompt(
        self,
        context: str,
        detected_text: str,
        detected_type: str,
        confidence: float
    ) -> str:
        """Create validation prompt for SLM."""
        prompt = f"""You are a HIPAA compliance expert. Determine if the following text contains Protected Health Information (PHI).

Context: {context}
Detected Text: "{detected_text}"
Detected Type: {detected_type}
Confidence: {confidence:.2f}

Is this actually PHI? Respond with:
- "YES" if it is PHI
- "NO" if it is not PHI

If YES, what is the correct PHI type? (ssn, phone, email, name, location, date, organization, ip, url, or other)

Response:"""
        return prompt
    
    def _generate_response(self, prompt: str) -> str:
        """
        Generate response from SLM.
        
        Args:
            prompt: Input prompt.
            
        Returns:
            Generated response text.
        """
        if self._pipeline is None:
            raise RuntimeError("Model not loaded")
        
        # Generate response
        outputs = self._pipeline(
            prompt,
            max_new_tokens=50,
            temperature=0.1,  # Low temperature for deterministic responses
            do_sample=False,
            return_full_text=False,
        )
        
        response = outputs[0]['generated_text'].strip()
        return response
    
    def _parse_response(self, response: str) -> Tuple[bool, Optional[str]]:
        """
        Parse SLM response to extract validation result.
        
        Args:
            response: SLM response text.
            
        Returns:
            Tuple of (is_phi: bool, refined_type: Optional[str]).
        """
        response_lower = response.lower()
        
        # Check for YES/NO
        is_phi = False
        if 'yes' in response_lower and 'no' not in response_lower[:10]:
            is_phi = True
        elif 'no' in response_lower and 'yes' not in response_lower[:10]:
            is_phi = False
        else:
            # Default to keeping if uncertain
            is_phi = True
        
        # Extract PHI type
        refined_type = None
        phi_types = ['ssn', 'phone', 'email', 'name', 'location', 'date', 
                     'organization', 'ip', 'url', 'other']
        
        for phi_type in phi_types:
            if phi_type in response_lower:
                refined_type = phi_type
                break
        
        return is_phi, refined_type
    
    def is_available(self) -> bool:
        """Check if validator is available and ready."""
        return self._pipeline is not None

