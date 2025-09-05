"""
Admin Management Package
"""

from .routes import admin_bp
from .service import AdminService

__all__ = ['admin_bp', 'AdminService']

