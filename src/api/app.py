"""
FastAPI application for HIPAA Anonymizer API.

Provides REST endpoints for PHI detection and anonymization.
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from typing import Dict

# Optional Gradio import
try:
    import gradio as gr
    GRADIO_AVAILABLE = True
except ImportError:
    GRADIO_AVAILABLE = False
    gr = None

from src.api.models import (
    DetectionRequest,
    DetectionResponseModel,
    AnonymizeRequest,
    AnonymizeResponse,
    HealthResponse,
    DetectionResponse
)
from src.pipeline import HIPAAPipeline

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="HIPAA Anonymizer API",
    description="Production-ready HIPAA-compliant PHI anonymization API with three-tier detection pipeline",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Mount Gradio UI (optional - can be disabled)
if GRADIO_AVAILABLE:
    try:
        from src.ui.gradio_app import create_interface
        gradio_app = create_interface()
        app = gr.mount_gradio_app(app, gradio_app, path="/ui")
        logger.info("Gradio UI mounted at /ui")
    except Exception as e:
        logger.warning(f"Could not mount Gradio UI: {e}. UI will not be available.")
else:
    logger.info("Gradio not available. UI will not be mounted. Install with: pip install gradio")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global pipeline instance (lazy-loaded)
_pipeline_cache: Dict[str, HIPAAPipeline] = {}


def get_pipeline(enable_tier2: bool = True, enable_tier3: bool = False) -> HIPAAPipeline:
    """
    Get or create pipeline instance.
    
    Args:
        enable_tier2: Enable Tier 2 (NER)
        enable_tier3: Enable Tier 3 (SLM validation)
        
    Returns:
        HIPAAPipeline instance
    """
    cache_key = f"{enable_tier2}_{enable_tier3}"
    
    if cache_key not in _pipeline_cache:
        try:
            _pipeline_cache[cache_key] = HIPAAPipeline(
                enable_tier2=enable_tier2,
                enable_tier3=enable_tier3
            )
            logger.info(f"Created pipeline: tier2={enable_tier2}, tier3={enable_tier3}")
        except Exception as e:
            logger.error(f"Failed to create pipeline: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Failed to initialize pipeline: {str(e)}"
            )
    
    return _pipeline_cache[cache_key]


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "message": "HIPAA Anonymizer API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    
    Returns the status of the service and available tiers.
    """
    try:
        # Check Tier 1 (always available)
        tier1_available = True
        
        # Check Tier 2
        tier2_available = False
        try:
            pipeline = get_pipeline(enable_tier2=True, enable_tier3=False)
            tier2_available = pipeline.ner_detector is not None
        except Exception:
            pass
        
        # Check Tier 3 availability without loading
        tier3_available = False
        try:
            # Check if dependencies are available without loading model
            # Use hasattr to check if module can be imported safely
            import importlib.util
            spec = importlib.util.find_spec("transformers")
            transformers_available = spec is not None
            
            spec = importlib.util.find_spec("llama_cpp")
            llama_cpp_available = spec is not None
            
            tier3_available = transformers_available or llama_cpp_available
        except Exception:
            # If check fails, assume Tier 3 is not available
            tier3_available = False
        
        return HealthResponse(
            status="healthy",
            version="1.0.0",
            tiers_available={
                "tier1": tier1_available,
                "tier2": tier2_available,
                "tier3": tier3_available
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unhealthy: {str(e)}"
        )


@app.post("/detect", response_model=DetectionResponseModel, tags=["Detection"])
async def detect_phi(request: DetectionRequest):
    """
    Detect PHI in text.
    
    Uses the three-tier detection pipeline:
    - Tier 1: Regex patterns (SSN, phone, email, IP, URL)
    - Tier 2: NER (names, locations, dates, organizations)
    - Tier 3: SLM validation (ambiguous cases)
    
    Returns list of detected PHI with positions and confidence scores.
    """
    try:
        pipeline = get_pipeline(
            enable_tier2=request.enable_tier2,
            enable_tier3=request.enable_tier3
        )
        
        # Detect PHI
        detections = pipeline.detect(request.text)
        
        # Convert to response format
        detection_responses = [
            DetectionResponse(**detection) for detection in detections
        ]
        
        return DetectionResponseModel(
            detections=detection_responses,
            total=len(detection_responses),
            text_length=len(request.text)
        )
        
    except Exception as e:
        logger.error(f"Detection failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Detection failed: {str(e)}"
        )


@app.post("/anonymize", response_model=AnonymizeResponse, tags=["Anonymization"])
async def anonymize_text(request: AnonymizeRequest):
    """
    Anonymize PHI in text.
    
    Detects and anonymizes PHI using the specified method:
    - safe_harbor: Replace with generic placeholders (HIPAA standard)
    - pseudonymize: Replace with consistent pseudonyms
    - redact: Remove PHI entirely
    - tag: Replace with tagged format [TYPE:N]
    
    Returns anonymized text and detection metadata.
    """
    try:
        pipeline = get_pipeline(
            enable_tier2=request.enable_tier2,
            enable_tier3=request.enable_tier3
        )
        
        # Anonymize with metadata
        result = pipeline.anonymize_with_metadata(
            request.text,
            method=request.method
        )
        
        # Convert detections to response format
        detection_responses = [
            DetectionResponse(**detection) for detection in result['detections']
        ]
        
        return AnonymizeResponse(
            anonymized_text=result['anonymized_text'],
            original_text=result['original_text'],
            detections=detection_responses,
            statistics=result['statistics']
        )
        
    except Exception as e:
        logger.error(f"Anonymization failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Anonymization failed: {str(e)}"
        )


@app.post("/batch/detect", tags=["Batch"])
async def batch_detect(texts: list[str], enable_tier2: bool = True, enable_tier3: bool = False):
    """
    Batch detect PHI in multiple texts.
    
    Args:
        texts: List of texts to process
        enable_tier2: Enable Tier 2 (NER)
        enable_tier3: Enable Tier 3 (SLM validation)
        
    Returns:
        List of detection results for each text
    """
    try:
        pipeline = get_pipeline(enable_tier2=enable_tier2, enable_tier3=enable_tier3)
        
        results = []
        for text in texts:
            detections = pipeline.detect(text)
            results.append({
                "text": text,
                "detections": [DetectionResponse(**d) for d in detections],
                "total": len(detections)
            })
        
        return {"results": results, "total_texts": len(texts)}
        
    except Exception as e:
        logger.error(f"Batch detection failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch detection failed: {str(e)}"
        )


@app.post("/batch/anonymize", tags=["Batch"])
async def batch_anonymize(
    texts: list[str],
    method: str = "safe_harbor",
    enable_tier2: bool = True,
    enable_tier3: bool = False
):
    """
    Batch anonymize multiple texts.
    
    Args:
        texts: List of texts to anonymize
        method: Anonymization method
        enable_tier2: Enable Tier 2 (NER)
        enable_tier3: Enable Tier 3 (SLM validation)
        
    Returns:
        List of anonymized results
    """
    try:
        pipeline = get_pipeline(enable_tier2=enable_tier2, enable_tier3=enable_tier3)
        
        results = []
        for text in texts:
            result = pipeline.anonymize_with_metadata(text, method=method)
            results.append({
                "original_text": result['original_text'],
                "anonymized_text": result['anonymized_text'],
                "detections": [DetectionResponse(**d) for d in result['detections']],
                "statistics": result['statistics']
            })
        
        return {"results": results, "total_texts": len(texts)}
        
    except Exception as e:
        logger.error(f"Batch anonymization failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch anonymization failed: {str(e)}"
        )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error", "error": str(exc)}
    )

