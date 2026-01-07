"""
Gradio UI for HIPAA Anonymizer.

Provides a user-friendly web interface for PHI detection and anonymization.
"""

import gradio as gr
from typing import Dict, List, Tuple
import logging

from src.pipeline import HIPAAPipeline

logger = logging.getLogger(__name__)

# Initialize pipeline (lazy-loaded)
_pipeline_cache: Dict[str, HIPAAPipeline] = {}


def get_pipeline(enable_tier2: bool = True, enable_tier3: bool = False) -> HIPAAPipeline:
    """Get or create pipeline instance."""
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
            raise
    
    return _pipeline_cache[cache_key]


def format_detections(detections: List[Dict]) -> str:
    """Format detections for display."""
    if not detections:
        return "No PHI detected."
    
    lines = []
    for i, det in enumerate(detections, 1):
        validated = " ✅ (Tier 3 validated)" if det.get('validated') else ""
        original = f" (was: {det.get('original_type')})" if det.get('original_type') else ""
        lines.append(
            f"{i}. **{det['type'].upper()}**: `{det['value']}`\n"
            f"   - Position: {det['start']}-{det['end']}\n"
            f"   - Confidence: {det.get('confidence', 1.0):.2%}\n"
            f"   - Source: {det.get('source', 'unknown')}{original}{validated}"
        )
    
    return "\n\n".join(lines)


def format_statistics(stats: Dict) -> str:
    """Format statistics for display."""
    lines = [f"**Total PHI Detected**: {stats.get('total_phi', 0)}"]
    
    if 'by_type' in stats and stats['by_type']:
        lines.append("\n**By Type:**")
        for phi_type, count in sorted(stats['by_type'].items()):
            lines.append(f"  - {phi_type}: {count}")
    
    if 'by_hipaa_category' in stats and stats['by_hipaa_category']:
        lines.append("\n**By HIPAA Category:**")
        for category, count in sorted(stats['by_hipaa_category'].items()):
            lines.append(f"  - {category.replace('_', ' ').title()}: {count}")
    
    return "\n".join(lines)


def detect_phi(
    text: str,
    enable_tier2: bool,
    enable_tier3: bool
) -> Tuple[str, str]:
    """
    Detect PHI in text.
    
    Returns:
        Tuple of (formatted detections, statistics)
    """
    if not text or not text.strip():
        return "Please enter some text to analyze.", ""
    
    try:
        pipeline = get_pipeline(enable_tier2=enable_tier2, enable_tier3=enable_tier3)
        detections = pipeline.detect(text)
        
        # Format detections
        detections_text = format_detections(detections)
        
        # Calculate statistics
        stats = {
            'total_phi': len(detections),
            'by_type': {},
            'by_hipaa_category': {}
        }
        
        for det in detections:
            phi_type = det['type']
            stats['by_type'][phi_type] = stats['by_type'].get(phi_type, 0) + 1
        
        stats_text = format_statistics(stats)
        
        return detections_text, stats_text
        
    except Exception as e:
        logger.error(f"Detection failed: {e}")
        return f"Error: {str(e)}", ""


def anonymize_text(
    text: str,
    method: str,
    enable_tier2: bool,
    enable_tier3: bool,
    show_detections: bool
) -> Tuple[str, str, str]:
    """
    Anonymize text and return results.
    
    Returns:
        Tuple of (anonymized_text, detections_text, statistics_text)
    """
    if not text or not text.strip():
        return "", "Please enter some text to anonymize.", ""
    
    try:
        pipeline = get_pipeline(enable_tier2=enable_tier2, enable_tier3=enable_tier3)
        
        # Anonymize with metadata
        result = pipeline.anonymize_with_metadata(text, method=method)
        
        anonymized = result['anonymized_text']
        
        # Format detections if requested
        detections_text = ""
        if show_detections:
            detections_text = format_detections(result['detections'])
        
        # Format statistics
        stats_text = format_statistics(result['statistics'])
        
        return anonymized, detections_text, stats_text
        
    except Exception as e:
        logger.error(f"Anonymization failed: {e}")
        return "", f"Error: {str(e)}", ""


# Example texts
EXAMPLES = [
    [
        "Patient John Smith, DOB: 1985-05-15, SSN: 123-45-6789, phone: (555) 123-4567, email: john.smith@hospital.com",
        "safe_harbor",
        True,
        False,
        True
    ],
    [
        "Dr. Sarah Johnson from Memorial Hospital in New York City treated patient Robert Williams on March 15, 2024. Contact: (212) 555-1234 or sarah.j@memorial.org",
        "pseudonymize",
        True,
        False,
        True
    ],
    [
        "Medical record for patient ID: 98765. Address: 123 Main St, Boston, MA 02101. Insurance: BlueCross BlueShield. Policy #: BC123456789",
        "safe_harbor",
        True,
        False,
        True
    ],
]


def create_interface():
    """Create and return Gradio interface."""
    
    with gr.Blocks(title="HIPAA Anonymizer") as app:
        gr.Markdown(
            """
            # 🔒 HIPAA Anonymizer
            
            Production-ready HIPAA-compliant PHI anonymization system with three-tier detection pipeline.
            
            **Features:**
            - **Tier 1**: Regex patterns (SSN, phone, email, IP, URL)
            - **Tier 2**: NER (names, locations, dates, organizations)
            - **Tier 3**: SLM validation (ambiguous cases) - *Optional*
            """
        )
        
        with gr.Tabs():
            # Detection Tab
            with gr.Tab("🔍 Detect PHI"):
                gr.Markdown("### Detect Protected Health Information (PHI) in text")
                
                with gr.Row():
                    with gr.Column(scale=2):
                        detect_input = gr.Textbox(
                            label="Input Text",
                            placeholder="Enter text containing PHI...",
                            lines=5,
                            value="Patient John Smith, SSN: 123-45-6789, phone: (555) 123-4567"
                        )
                        
                        with gr.Row():
                            detect_tier2 = gr.Checkbox(
                                label="Enable Tier 2 (NER)",
                                value=True,
                                info="Contextual understanding of names, locations, dates"
                            )
                            detect_tier3 = gr.Checkbox(
                                label="Enable Tier 3 (SLM Validation)",
                                value=False,
                                info="Validates ambiguous cases (requires model download)"
                            )
                        
                        detect_btn = gr.Button("Detect PHI", variant="primary", size="lg")
                    
                    with gr.Column(scale=1):
                        detect_output = gr.Markdown(
                            label="Detected PHI",
                            value="Detections will appear here..."
                        )
                        detect_stats = gr.Markdown(
                            label="Statistics",
                            value=""
                        )
                
                detect_btn.click(
                    fn=detect_phi,
                    inputs=[detect_input, detect_tier2, detect_tier3],
                    outputs=[detect_output, detect_stats]
                )
            
            # Anonymization Tab
            with gr.Tab("🛡️ Anonymize"):
                gr.Markdown("### Anonymize PHI in text")
                
                with gr.Row():
                    with gr.Column(scale=2):
                        anonymize_input = gr.Textbox(
                            label="Input Text",
                            placeholder="Enter text containing PHI...",
                            lines=5,
                            value="Patient John Smith, SSN: 123-45-6789, phone: (555) 123-4567"
                        )
                        
                        anonymize_method = gr.Radio(
                            label="Anonymization Method",
                            choices=["safe_harbor", "pseudonymize", "redact", "tag"],
                            value="safe_harbor",
                            info="Safe Harbor: HIPAA-compliant placeholders | Pseudonymize: Consistent replacements | Redact: Remove | Tag: Numbered tags"
                        )
                        
                        with gr.Row():
                            anonymize_tier2 = gr.Checkbox(
                                label="Enable Tier 2 (NER)",
                                value=True
                            )
                            anonymize_tier3 = gr.Checkbox(
                                label="Enable Tier 3 (SLM Validation)",
                                value=False
                            )
                            show_detections = gr.Checkbox(
                                label="Show Detections",
                                value=True
                            )
                        
                        anonymize_btn = gr.Button("Anonymize", variant="primary", size="lg")
                    
                    with gr.Column(scale=1):
                        anonymize_output = gr.Textbox(
                            label="Anonymized Text",
                            lines=5,
                            value=""
                        )
                        anonymize_detections = gr.Markdown(
                            label="Detected PHI",
                            value=""
                        )
                        anonymize_stats = gr.Markdown(
                            label="Statistics",
                            value=""
                        )
                
                anonymize_btn.click(
                    fn=anonymize_text,
                    inputs=[
                        anonymize_input,
                        anonymize_method,
                        anonymize_tier2,
                        anonymize_tier3,
                        show_detections
                    ],
                    outputs=[anonymize_output, anonymize_detections, anonymize_stats]
                )
                
                gr.Examples(
                    examples=EXAMPLES,
                    inputs=[
                        anonymize_input,
                        anonymize_method,
                        anonymize_tier2,
                        anonymize_tier3,
                        show_detections
                    ],
                    label="Example Texts"
                )
            
            # About Tab
            with gr.Tab("ℹ️ About"):
                gr.Markdown(
                    """
                    ## HIPAA Anonymizer
                    
                    A production-ready system for detecting and anonymizing Protected Health Information (PHI) 
                    in compliance with HIPAA regulations.
                    
                    ### Detection Tiers
                    
                    **Tier 1: Regex Detector**
                    - Deterministic pattern matching
                    - Detects: SSN, phone numbers, email addresses, IP addresses, URLs
                    - Fast and reliable
                    
                    **Tier 2: NER Detector**
                    - Named Entity Recognition using spaCy
                    - Detects: Names, locations, dates, organizations
                    - Contextual understanding
                    
                    **Tier 3: SLM Validation** (Optional)
                    - Small Language Model validation
                    - Validates ambiguous detections
                    - Refines PHI type classifications
                    - Requires model download (~2-7GB)
                    
                    ### Anonymization Methods
                    
                    - **Safe Harbor**: HIPAA-compliant replacement with generic placeholders
                    - **Pseudonymize**: Consistent replacements (same PHI → same pseudonym)
                    - **Redact**: Complete removal of PHI
                    - **Tag**: Numbered placeholders [TYPE:N]
                    
                    ### HIPAA Compliance
                    
                    This system detects all 18 HIPAA identifiers:
                    1. Names
                    2. Geographic subdivisions
                    3. Dates
                    4. Phone numbers
                    5. Fax numbers
                    6. Email addresses
                    7. Social Security Numbers
                    8. Medical record numbers
                    9. Health plan beneficiary numbers
                    10. Account numbers
                    11. Certificate/license numbers
                    12. Vehicle identifiers
                    13. Device identifiers
                    14. Web URLs
                    15. IP addresses
                    16. Biometric identifiers
                    17. Full face photos
                    18. Any other unique identifier
                    
                    ### API Access
                    
                    This UI is also available as a REST API. See `/docs` for API documentation.
                    """
                )
    
    return app


if __name__ == "__main__":
    # Create and launch interface
    app = create_interface()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        theme=gr.themes.Soft()  # Move theme to launch() for Gradio 6.0+
    )

