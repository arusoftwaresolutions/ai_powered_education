"""
Quizzes Management Package
"""

from .routes import quizzes_bp
from .service import QuizService

__all__ = ['quizzes_bp', 'QuizService']

