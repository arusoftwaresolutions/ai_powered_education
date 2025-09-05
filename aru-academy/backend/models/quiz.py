from .base import db, TimestampMixin
from enum import Enum

class QuestionType(Enum):
    MULTIPLE_CHOICE = 'multiple_choice'
    SHORT_ANSWER = 'short_answer'

class Quiz(db.Model, TimestampMixin):
    __tablename__ = 'quizzes'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    topic = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # Relationships
    questions = db.relationship('QuizQuestion', backref='quiz', lazy=True, cascade='all, delete-orphan')
    submissions = db.relationship('QuizSubmission', backref='quiz', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Quiz {self.title}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'course_id': self.course_id,
            'course_title': self.course.title if self.course else None,
            'topic': self.topic,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'question_count': len(self.questions)
        }

class QuizQuestion(db.Model, TimestampMixin):
    __tablename__ = 'quiz_questions'
    
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    question_type = db.Column(db.Enum(QuestionType), nullable=False)
    question = db.Column(db.Text, nullable=False)
    options = db.Column(db.JSON, nullable=True)  # For multiple choice questions
    answer = db.Column(db.Text, nullable=False)
    explanation = db.Column(db.Text)
    points = db.Column(db.Integer, default=1)
    
    def __repr__(self):
        return f'<QuizQuestion {self.id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'quiz_id': self.quiz_id,
            'question_type': self.question_type.value if self.question_type else None,
            'question': self.question,
            'options': self.options,
            'answer': self.answer,
            'explanation': self.explanation,
            'points': self.points
        }

class QuizSubmission(db.Model, TimestampMixin):
    __tablename__ = 'quiz_submissions'
    
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    score = db.Column(db.Float, nullable=False)
    max_score = db.Column(db.Float, nullable=False)
    answers = db.Column(db.JSON, nullable=True)  # Store user answers
    submitted_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    user = db.relationship('User', backref='quiz_submissions_ref')
    
    def __repr__(self):
        return f'<QuizSubmission {self.user_id}-{self.quiz_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'quiz_id': self.quiz_id,
            'user_id': self.user_id,
            'score': self.score,
            'max_score': self.max_score,
            'percentage': round((self.score / self.max_score) * 100, 2) if self.max_score > 0 else 0,
            'answers': self.answers,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

