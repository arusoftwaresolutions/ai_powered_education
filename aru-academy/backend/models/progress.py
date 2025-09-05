from .base import db, TimestampMixin
from enum import Enum

class ProgressStatus(Enum):
    NOT_STARTED = 'not_started'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'

class Progress(db.Model, TimestampMixin):
    __tablename__ = 'progress'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    resource_id = db.Column(db.Integer, db.ForeignKey('resources.id'), nullable=False)
    status = db.Column(db.Enum(ProgressStatus), default=ProgressStatus.NOT_STARTED)
    last_accessed_at = db.Column(db.DateTime, nullable=True)
    completion_percentage = db.Column(db.Float, default=0.0)
    
    # Relationships
    user = db.relationship('User', overlaps="progress_records,user_ref")
    resource = db.relationship('Resource', overlaps="progress_list")
    
    def __repr__(self):
        return f'<Progress {self.user_id}-{self.resource_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'resource_id': self.resource_id,
            'status': self.status.value if self.status else None,
            'last_accessed_at': self.last_accessed_at.isoformat() if self.last_accessed_at else None,
            'completion_percentage': self.completion_percentage,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

