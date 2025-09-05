"""
Courses Management Package
"""

from .routes import courses_bp
from .service import CourseService

__all__ = ['courses_bp', 'CourseService']

