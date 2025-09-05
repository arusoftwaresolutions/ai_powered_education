from .base import db, TimestampMixin
from enum import Enum

class ApprovedUser(db.Model, TimestampMixin):
    __tablename__ = 'approved_users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(db.String(20), nullable=False)  # student, instructor
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    department = db.relationship('Department', overlaps="approved_users_list,department_ref")
    approver = db.relationship('User', backref='approved_users')
    
    def __repr__(self):
        return f'<ApprovedUser {self.email}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'department_id': self.department_id,
            'department_name': self.department.name if self.department else None,
            'approved_by': self.approved_by,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

