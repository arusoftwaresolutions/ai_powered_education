from .base import db, TimestampMixin

class Course(db.Model, TimestampMixin):
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    resources = db.relationship('Resource', backref='course', lazy=True, cascade='all, delete-orphan')
    quizzes = db.relationship('Quiz', backref='course', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Course {self.title}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'department_id': self.department_id,
            'department_name': self.department.name if hasattr(self, 'department') and self.department else None,
            'created_by': self.created_by,
            'creator_name': self.creator.name if hasattr(self, 'creator') and self.creator else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'resource_count': len(self.resources) if hasattr(self, 'resources') else 0,
            'quiz_count': len(self.quizzes) if hasattr(self, 'quizzes') else 0
        }

