#!/usr/bin/env python3
"""
Download GGUF quantized models for Tier 3 SLM validation.

Downloads optimized GGUF models for better CPU performance.
"""

import sys
from pathlib import Path
import argparse

try:
    from huggingface_hub import hf_hub_download
    HF_HUB_AVAILABLE = True
except ImportError:
    HF_HUB_AVAILABLE = False
    print("Warning: huggingface_hub not available. Install with: pip install huggingface-hub")


# Model configurations
GGUF_MODELS = {
    "phi3-mini": {
        "repo": "microsoft/Phi-3-mini-4k-instruct-gguf",
        "files": {
            "q4": "Phi-3-mini-4k-instruct-q4.gguf",  # 2.2GB, recommended
            "fp16": "Phi-3-mini-4k-instruct-fp16.gguf",  # 7.2GB
        }
    },
    "llama3.2-3b": {
        "repo": "bartowski/Llama-3.2-3B-Instruct-GGUF",
        "files": {
            "q4": "llama-3.2-3b-instruct.Q4_K_M.gguf",  # Recommended
            "q5": "llama-3.2-3b-instruct.Q5_K_M.gguf",  # Better quality
            "q8": "llama-3.2-3b-instruct.Q8_0.gguf",  # Best quality
        }
    }
}


def download_model(model_name: str, quantization: str = "q4", output_dir: str = "models"):
    """
    Download a GGUF model from Hugging Face.
    
    Args:
        model_name: Model name ('phi3-mini' or 'llama3.2-3b')
        quantization: Quantization level ('q4', 'q5', 'q8', or 'fp16')
        output_dir: Directory to save the model
    """
    if not HF_HUB_AVAILABLE:
        print("Error: huggingface_hub not installed. Install with: pip install huggingface-hub")
        return False
    
    if model_name not in GGUF_MODELS:
        print(f"Error: Unknown model '{model_name}'. Available: {list(GGUF_MODELS.keys())}")
        return False
    
    config = GGUF_MODELS[model_name]
    
    if quantization not in config["files"]:
        print(f"Error: Quantization '{quantization}' not available for {model_name}")
        print(f"Available: {list(config['files'].keys())}")
        return False
    
    filename = config["files"][quantization]
    repo_id = config["repo"]
    
    print(f"Downloading {model_name} ({quantization})...")
    print(f"Repository: {repo_id}")
    print(f"File: {filename}")
    print(f"Output: {output_dir}/")
    print()
    
    try:
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Download model
        model_path = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            local_dir=output_dir,
            local_dir_use_symlinks=False
        )
        
        print(f"✅ Successfully downloaded: {model_path}")
        print(f"\nYou can now use this model with:")
        print(f"  from src.validators.slm_validator import SLMValidator")
        print(f"  validator = SLMValidator(")
        print(f"      model_name='{model_path}',")
        print(f"      use_gguf=True")
        print(f"  )")
        
        return True
        
    except Exception as e:
        print(f"❌ Error downloading model: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure you're logged in: huggingface-cli login")
        print("2. Request access to the model on Hugging Face")
        print("3. Check your internet connection")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Download GGUF quantized models for Tier 3 SLM validation"
    )
    parser.add_argument(
        "model",
        choices=list(GGUF_MODELS.keys()),
        help="Model to download"
    )
    parser.add_argument(
        "--quantization",
        "-q",
        default="q4",
        choices=["q4", "q5", "q8", "fp16"],
        help="Quantization level (default: q4)"
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        default="models",
        help="Output directory (default: models)"
    )
    
    args = parser.parse_args()
    
    success = download_model(
        args.model,
        args.quantization,
        args.output_dir
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

