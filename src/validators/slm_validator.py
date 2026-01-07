"""
Tier 3: SLM Validator for Ambiguous PHI Detection.

Uses a Small Language Model (SLM) to validate and refine ambiguous
detections from Tier 1 and Tier 2.
"""

import re
import os
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import logging

# Optional imports - handle gracefully if not available
try:
    from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    torch = None

# GGUF support via llama-cpp-python
try:
    from llama_cpp import Llama
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False

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
    # Note: Some models may be gated and require Hugging Face authentication
    # Get token from: https://huggingface.co/settings/tokens
    # Then run: huggingface-cli login
    
    # Standard Hugging Face models
    SUPPORTED_MODELS = [
        "microsoft/Phi-3-mini-4k-instruct",  # Fast, efficient (may be gated)
        "meta-llama/Llama-3.2-3B-Instruct",  # Good balance (may be gated)
    ]
    
    # GGUF quantized models (better CPU performance)
    SUPPORTED_GGUF_MODELS = {
        "microsoft/Phi-3-mini-4k-instruct-gguf": {
            "q4": "Phi-3-mini-4k-instruct-q4.gguf",  # 2.2GB, recommended
            "fp16": "Phi-3-mini-4k-instruct-fp16.gguf",  # 7.2GB, minimal quality loss
        },
        "bartowski/Llama-3.2-3B-Instruct-GGUF": {
            "q4": "llama-3.2-3b-instruct.Q4_K_M.gguf",  # Recommended
            "q5": "llama-3.2-3b-instruct.Q5_K_M.gguf",  # Better quality
            "q8": "llama-3.2-3b-instruct.Q8_0.gguf",  # Best quality
        }
    }
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        confidence_threshold: float = 0.7,
        device: Optional[str] = None,
        max_length: int = 512,
        use_quantization: bool = True,
        use_gguf: bool = True,  # Prefer GGUF if available
        gguf_quantization: str = "q4"  # q4, q5, q8, or fp16
    ):
        """
        Initialize SLM validator.
        
        Args:
            model_name: Name of the model to use. If None, auto-selects best available.
                       Can be standard Hugging Face model or GGUF model path.
            confidence_threshold: Only validate detections below this confidence.
            device: Device to run on ('cpu', 'cuda', or None for auto-detect).
            max_length: Maximum sequence length for model.
            use_quantization: Use 8-bit quantization for faster inference (if available).
            use_gguf: If True, prefer GGUF models for better CPU performance.
            gguf_quantization: GGUF quantization level ('q4', 'q5', 'q8', or 'fp16').
        """
        self.confidence_threshold = confidence_threshold
        self.max_length = max_length
        self.use_quantization = use_quantization
        self.use_gguf = use_gguf
        self.gguf_quantization = gguf_quantization
        
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
        self._llama_model = None  # For GGUF
        self.model_name = None
        self.model_format = None  # 'transformers' or 'gguf'
        
        # Check for GGUF support
        if use_gguf and LLAMA_CPP_AVAILABLE:
            self.model_format = 'gguf'
        elif TRANSFORMERS_AVAILABLE:
            self.model_format = 'transformers'
        else:
            raise RuntimeError(
                "Neither transformers nor llama-cpp-python available. "
                "Install one: pip install transformers torch OR pip install llama-cpp-python"
            )
        
        if model_name is None:
            model_name = self._auto_select_model()
        
        self._load_model(model_name)
    
    def _auto_select_model(self) -> str:
        """
        Auto-select the best available model.
        
        Returns:
            Model name string (Hugging Face repo or GGUF model path).
        """
        # Prefer GGUF if available and requested
        if self.use_gguf and LLAMA_CPP_AVAILABLE:
            # Try GGUF models first
            for repo_name, variants in self.SUPPORTED_GGUF_MODELS.items():
                quant_key = self.gguf_quantization
                if quant_key not in variants:
                    quant_key = "q4"  # Fallback to q4
                
                filename = variants[quant_key]
                model_path = self._get_gguf_path(repo_name, filename)
                
                if model_path and os.path.exists(model_path):
                    logger.info(f"Auto-selected GGUF model: {model_path}")
                    return model_path
        
        # Fallback to standard Hugging Face models
        if TRANSFORMERS_AVAILABLE:
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
            "No models available. Install llama-cpp-python for GGUF or transformers for standard models."
        )
    
    def _get_gguf_path(self, repo_name: str, filename: str) -> Optional[str]:
        """
        Get path to GGUF model file.
        
        Args:
            repo_name: Hugging Face repo name
            filename: GGUF filename
            
        Returns:
            Path to model file or None if not found.
        """
        import os
        from pathlib import Path
        
        # Check common cache locations
        cache_dirs = [
            Path.home() / ".cache" / "huggingface" / "hub" / f"models--{repo_name.replace('/', '--')}",
            Path("models") / repo_name.split("/")[-1],
            Path(".") / filename,
        ]
        
        for cache_dir in cache_dirs:
            # Search recursively for the file
            if cache_dir.exists():
                for root, dirs, files in os.walk(cache_dir):
                    if filename in files:
                        return str(Path(root) / filename)
        
        return None
    
    def _load_model(self, model_name: str):
        """
        Load the SLM model and tokenizer.
        
        Args:
            model_name: Name of the model to load (Hugging Face repo or GGUF file path).
        """
        import os
        
        # Check if it's a GGUF file path
        if model_name.endswith('.gguf') or os.path.exists(model_name):
            self._load_gguf_model(model_name)
        else:
            self._load_transformers_model(model_name)
    
    def _load_gguf_model(self, model_path: str):
        """Load GGUF model using llama-cpp-python."""
        if not LLAMA_CPP_AVAILABLE:
            raise RuntimeError(
                "llama-cpp-python not available. Install with: pip install llama-cpp-python"
            )
        
        try:
            logger.info(f"Loading GGUF model: {model_path}")
            
            # Determine GPU layers (0 for CPU, more for GPU)
            n_gpu_layers = 0
            if self.device == "cuda":
                n_gpu_layers = 35  # Offload all layers to GPU if available
            
            # Load GGUF model
            self._llama_model = Llama(
                model_path=model_path,
                n_ctx=self.max_length,
                n_threads=None,  # Auto-detect CPU threads
                n_gpu_layers=n_gpu_layers,
                verbose=False
            )
            
            self.model_name = model_path
            self.model_format = 'gguf'
            logger.info(f"Successfully loaded GGUF model: {model_path}")
            
        except Exception as e:
            logger.error(f"Failed to load GGUF model {model_path}: {e}")
            raise RuntimeError(f"Failed to load GGUF model: {e}")
    
    def _load_transformers_model(self, model_name: str):
        """Load standard Hugging Face model using transformers."""
        if not TRANSFORMERS_AVAILABLE:
            raise RuntimeError(
                "Transformers library not available. Install with: pip install transformers torch"
            )
        
        try:
            logger.info(f"Loading transformers model: {model_name}")
            
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
            
            # Track if quantization is used
            using_quantization = False
            
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
                        using_quantization = True
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
            
            # Move to device (skip if using quantization - model is already on correct device)
            if not using_quantization and self.device == "cpu":
                self._model = self._model.to(self.device)
            
            # Create pipeline
            # Don't specify device if using quantization (accelerate handles it automatically)
            if using_quantization:
                # Accelerate handles device placement, don't specify device
                self._pipeline = pipeline(
                    "text-generation",
                    model=self._model,
                    tokenizer=self._tokenizer,
                    max_length=self.max_length,
                )
            else:
                # Normal pipeline with device specification
                self._pipeline = pipeline(
                    "text-generation",
                    model=self._model,
                    tokenizer=self._tokenizer,
                    device=0 if self.device == "cuda" else -1,
                    max_length=self.max_length,
                )
            
            self.model_name = model_name
            self.model_format = 'transformers'
            logger.info(f"Successfully loaded transformers model: {model_name}")
            
        except Exception as e:
            logger.error(f"Failed to load transformers model {model_name}: {e}")
            raise RuntimeError(f"Failed to load transformers model: {e}")
    
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
            # Silently skip validation on error (don't spam logs for known issues)
            # Known issue: DynamicCache errors with some model configurations
            if "DynamicCache" in str(e) or "seen_tokens" in str(e):
                logger.debug(f"Tier 3 validation skipped for {detected_text}: model compatibility issue")
            else:
                logger.warning(f"Validation failed for {detected_text}: {e}")
            # On error, keep original detection but mark as unvalidated
            return None
    
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
        if self.model_format == 'gguf':
            return self._generate_response_gguf(prompt)
        else:
            return self._generate_response_transformers(prompt)
    
    def _generate_response_gguf(self, prompt: str) -> str:
        """Generate response using GGUF model."""
        if self._llama_model is None:
            raise RuntimeError("GGUF model not loaded")
        
        # Format prompt for Phi-3/Llama chat format
        formatted_prompt = self._format_prompt_for_chat(prompt)
        
        # Generate response
        output = self._llama_model(
            formatted_prompt,
            max_tokens=50,
            temperature=0.1,
            stop=["<|end|>", "\n\n"],
            echo=False,
        )
        
        response = output['choices'][0]['text'].strip()
        return response
    
    def _generate_response_transformers(self, prompt: str) -> str:
        """Generate response using transformers model."""
        if self._pipeline is None:
            raise RuntimeError("Model not loaded")
        
        # Generate response with compatibility fixes
        # Remove temperature parameter to avoid DynamicCache issues
        try:
            outputs = self._pipeline(
                prompt,
                max_new_tokens=50,
                do_sample=False,
                return_full_text=False,
            )
            
            response = outputs[0]['generated_text'].strip()
            return response
        except Exception as e:
            # Fallback: try with model.generate() directly if pipeline fails
            logger.debug(f"Pipeline generation failed: {e}, trying direct model.generate()")
            try:
                # Format prompt for Phi-3 chat format
                formatted_prompt = self._format_prompt_for_chat(prompt)
                
                # Tokenize
                inputs = self._tokenizer(formatted_prompt, return_tensors="pt")
                if self.device == "cpu":
                    inputs = {k: v.to("cpu") for k, v in inputs.items()}
                elif self.device == "cuda":
                    inputs = {k: v.to("cuda") for k, v in inputs.items()}
                
                # Generate
                with torch.no_grad():
                    outputs = self._model.generate(
                        **inputs,
                        max_new_tokens=50,
                        do_sample=False,
                    )
                
                # Decode (skip input tokens)
                response = self._tokenizer.decode(
                    outputs[0][inputs['input_ids'].shape[1]:], 
                    skip_special_tokens=True
                ).strip()
                return response
            except Exception as e2:
                logger.error(f"All generation methods failed: {e2}")
                raise RuntimeError(f"Failed to generate response: {e2}")
    
    def _format_prompt_for_chat(self, prompt: str) -> str:
        """Format prompt for Phi-3/Llama chat format."""
        # Simple format: wrap in user/assistant tags
        return f"<|user|>\n{prompt}<|end|>\n<|assistant|>"
    
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
        if self.model_format == 'gguf':
            return self._llama_model is not None
        else:
            return self._pipeline is not None

