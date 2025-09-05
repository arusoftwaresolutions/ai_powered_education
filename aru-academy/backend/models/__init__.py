"""
Database Models Package
"""

from .base import db, migrate, TimestampMixin
from .department import Department
from .user import User, UserRole, UserStatus
from .approved_user import ApprovedUser
from .course import Course
from .resource import Resource, ResourceType
from .progress import Progress, ProgressStatus
from .quiz import Quiz, QuizQuestion, QuizSubmission, QuestionType
from .ai_log import AiCallLog

__all__ = [
    'db',
    'migrate', 
    'TimestampMixin',
    'Department',
    'User',
    'UserRole',
    'UserStatus',
    'ApprovedUser',
    'Course',
    'Resource',
    'ResourceType',
    'Progress',
    'ProgressStatus',
    'Quiz',
    'QuizQuestion',
    'QuizSubmission',
    'QuestionType',
    'AiCallLog'
]

