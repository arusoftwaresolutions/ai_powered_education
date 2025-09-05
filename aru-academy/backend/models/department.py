from .base import db, TimestampMixin

class Department(db.Model, TimestampMixin):
    __tablename__ = 'departments'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    
    # Relationships
    users = db.relationship('User', backref='department', lazy=True)
    courses = db.relationship('Course', backref='department', lazy=True)
    approved_users_list = db.relationship('ApprovedUser', backref='department_ref', lazy=True)
    
    def __repr__(self):
        return f'<Department {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

