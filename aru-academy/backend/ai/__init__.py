"""
AI Integration Package
"""

from .routes import ai_bp
from .huggingface_provider import HuggingFaceProvider

__all__ = ['ai_bp', 'HuggingFaceProvider']

