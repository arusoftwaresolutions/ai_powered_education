from .base import db, TimestampMixin

class AiCallLog(db.Model, TimestampMixin):
    __tablename__ = 'ai_call_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    endpoint = db.Column(db.String(100), nullable=False)  # ask, generate-questions
    request_data = db.Column(db.JSON, nullable=True)
    response_data = db.Column(db.JSON, nullable=True)
    success = db.Column(db.Boolean, default=True)
    error_message = db.Column(db.Text, nullable=True)
    processing_time = db.Column(db.Float, nullable=True)  # in seconds
    
    # Relationships
    user = db.relationship('User', backref='ai_calls_ref')
    
    def __repr__(self):
        return f'<AiCallLog {self.user_id}-{self.endpoint}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.name if self.user else None,
            'endpoint': self.endpoint,
            'request_data': self.request_data,
            'response_data': self.response_data,
            'success': self.success,
            'error_message': self.error_message,
            'processing_time': self.processing_time,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

