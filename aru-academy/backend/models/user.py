from .base import db, TimestampMixin
from werkzeug.security import generate_password_hash, check_password_hash
from enum import Enum

class UserRole(Enum):
    STUDENT = 'student'
    INSTRUCTOR = 'instructor'
    ADMIN = 'admin'

class UserStatus(Enum):
    PENDING = 'pending'
    ACTIVE = 'active'
    SUSPENDED = 'suspended'

class User(db.Model, TimestampMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(UserRole), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    status = db.Column(db.Enum(UserStatus), default=UserStatus.PENDING)
    
    # Relationships
    courses_created = db.relationship('Course', backref='creator', lazy=True)
    progress_records = db.relationship('Progress', backref='user_ref', lazy=True)
    quiz_submissions = db.relationship('QuizSubmission', lazy=True)
    ai_calls = db.relationship('AiCallLog', lazy=True)
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role.value.title() if self.role else None,  # Capitalize first letter
            'department_id': self.department_id,
            'department_name': self.department.name if hasattr(self, 'department') and self.department else None,
            'status': self.status.value if self.status else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def to_dict_public(self):
        """Return user data without sensitive information"""
        return {
            'id': self.id,
            'name': self.name,
            'role': self.role.value.title() if self.role else None,  # Capitalize first letter
            'department_name': self.department.name if hasattr(self, 'department') and self.department else None,
            'status': self.status.value if self.status else None
        }

