"""
Resources Management Package
"""

from .routes import resources_bp
from .service import ResourceService

__all__ = ['resources_bp', 'ResourceService']

