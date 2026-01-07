"""
FastAPI API interface for HIPAA Anonymizer.

Provides REST endpoints for PHI detection and anonymization.
"""

from src.api.app import app

__all__ = ['app']

