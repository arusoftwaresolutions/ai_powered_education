from .base import db, TimestampMixin
from enum import Enum

class ResourceType(Enum):
    PDF = 'pdf'
    TEXT = 'text'
    LINK = 'link'
    VIDEO = 'video'

class Resource(db.Model, TimestampMixin):
    __tablename__ = 'resources'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    type = db.Column(db.Enum(ResourceType), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    file_path_or_url = db.Column(db.String(500), nullable=True)
    text_content = db.Column(db.Text, nullable=True)
    description = db.Column(db.Text)
    
    # Relationships
    progress_list = db.relationship('Progress', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Resource {self.title}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'type': self.type.value if self.type else None,
            'course_id': self.course_id,
            'course_title': self.course.title if self.course else None,
            'file_path_or_url': self.file_path_or_url,
            'text_content': self.text_content,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

