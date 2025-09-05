from models.base import db
from models.quiz import Quiz, QuizQuestion, QuizSubmission, QuestionType
from models.user import User, UserRole
from models.course import Course
from typing import List, Optional, Dict
from datetime import datetime

class QuizService:
    """Service layer for quiz operations"""
    
    def get_quizzes_for_user(self, user: User) -> List[Quiz]:
        """Get quizzes based on user role and department"""
        if user.role == UserRole.ADMIN:
            return Quiz.query.all()
        elif user.role == UserRole.INSTRUCTOR:
            # Get quizzes from courses created by the instructor
            course_ids = [course.id for course in user.courses_created]
            return Quiz.query.filter(Quiz.course_id.in_(course_ids)).all()
        else:  # Student
            # Get quizzes from user's department
            return Quiz.query.join(Course).filter(Course.department_id == user.department_id).all()
    
    def get_quizzes_by_course(self, user: User, course_id: int) -> List[Quiz]:
        """Get quizzes for a specific course with permission check"""
        course = Course.query.get(course_id)
        if not course:
            raise ValueError('Course not found')
        
        # Check access permissions
        if user.role == UserRole.STUDENT and course.department_id != user.department_id:
            raise ValueError('Access denied to this course')
        
        if user.role == UserRole.INSTRUCTOR and course.created_by != user.id:
            raise ValueError('Access denied to this course')
        
        return Quiz.query.filter_by(course_id=course_id).all()
    
    def get_quiz_by_id(self, user: User, quiz_id: int) -> Optional[Quiz]:
        """Get a specific quiz with permission check"""
        quiz = Quiz.query.get(quiz_id)
        if not quiz:
            return None
        
        course = Course.query.get(quiz.course_id)
        if not course:
            return None
        
        # Check access permissions
        if user.role == UserRole.STUDENT and course.department_id != user.department_id:
            raise ValueError('Access denied to this quiz')
        
        if user.role == UserRole.INSTRUCTOR and course.created_by != user.id:
            raise ValueError('Access denied to this quiz')
        
        return quiz
    
    def create_quiz(self, user: User, quiz_data: dict) -> Quiz:
        """Create a new quiz"""
        try:
            # Validate course exists and user has access
            course = Course.query.get(quiz_data['course_id'])
            if not course:
                raise ValueError('Course not found')
            
            if user.role == UserRole.INSTRUCTOR and course.created_by != user.id:
                raise ValueError('Access denied to this course')
            
            # Create quiz
            quiz = Quiz(
                title=quiz_data['title'],
                course_id=quiz_data['course_id'],
                topic=quiz_data['topic'],
                description=quiz_data.get('description', '')
            )
            
            db.session.add(quiz)
            db.session.flush()  # Get quiz ID
            
            # Create quiz questions
            for q_data in quiz_data['questions']:
                question = QuizQuestion(
                    quiz_id=quiz.id,
                    question_type=QuestionType(q_data['type']),
                    question=q_data['question'],
                    options=q_data.get('options'),
                    answer=q_data['answer'],
                    explanation=q_data.get('explanation', ''),
                    points=q_data.get('points', 1)
                )
                db.session.add(question)
            
            db.session.commit()
            
            return quiz
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    def update_quiz(self, user: User, quiz_id: int, update_data: dict) -> Quiz:
        """Update an existing quiz"""
        try:
            quiz = Quiz.query.get(quiz_id)
            if not quiz:
                raise ValueError('Quiz not found')
            
            course = Course.query.get(quiz.course_id)
            if not course:
                raise ValueError('Course not found')
            
            # Check permissions
            if user.role == UserRole.STUDENT:
                raise ValueError('Students cannot modify quizzes')
            
            if user.role == UserRole.INSTRUCTOR and course.created_by != user.id:
                raise ValueError('Access denied')
            
            # Update fields
            if 'title' in update_data:
                quiz.title = update_data['title']
            if 'topic' in update_data:
                quiz.topic = update_data['topic']
            if 'description' in update_data:
                quiz.description = update_data['description']
            
            db.session.commit()
            
            return quiz
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    def delete_quiz(self, user: User, quiz_id: int) -> bool:
        """Delete a quiz"""
        try:
            quiz = Quiz.query.get(quiz_id)
            if not quiz:
                raise ValueError('Quiz not found')
            
            course = Course.query.get(quiz.course_id)
            if not course:
                raise ValueError('Course not found')
            
            # Check permissions
            if user.role == UserRole.STUDENT:
                raise ValueError('Students cannot delete quizzes')
            
            if user.role == UserRole.INSTRUCTOR and course.created_by != user.id:
                raise ValueError('Access denied')
            
            db.session.delete(quiz)
            db.session.commit()
            
            return True
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    def submit_quiz(self, user_id: int, quiz_id: int, answers: Dict) -> QuizSubmission:
        """Submit quiz answers and calculate score"""
        try:
            quiz = Quiz.query.get(quiz_id)
            if not quiz:
                raise ValueError('Quiz not found')
            
            # Check if user already submitted this quiz
            existing_submission = QuizSubmission.query.filter_by(
                quiz_id=quiz_id,
                user_id=user_id
            ).first()
            
            if existing_submission:
                raise ValueError('Quiz already submitted')
            
            # Calculate score
            score = 0
            max_score = 0
            
            for question in quiz.questions:
                max_score += question.points
                question_id = str(question.id)
                
                if question_id in answers:
                    user_answer = answers[question_id]
                    
                    if question.question_type == QuestionType.MULTIPLE_CHOICE:
                        if user_answer == question.answer:
                            score += question.points
                    elif question.question_type == QuestionType.SHORT_ANSWER:
                        # Simple text matching for short answers
                        if user_answer.lower().strip() == question.answer.lower().strip():
                            score += question.points
                        # Partial credit for similar answers
                        elif self._calculate_similarity(user_answer, question.answer) > 0.7:
                            score += question.points * 0.5
            
            # Create submission
            submission = QuizSubmission(
                quiz_id=quiz_id,
                user_id=user_id,
                score=score,
                max_score=max_score,
                answers=answers,
                submitted_at=datetime.utcnow()
            )
            
            db.session.add(submission)
            db.session.commit()
            
            return submission
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings"""
        # Simple similarity calculation
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def get_user_quiz_history(self, user_id: int) -> List[QuizSubmission]:
        """Get user's quiz submission history"""
        return QuizSubmission.query.filter_by(user_id=user_id).order_by(QuizSubmission.submitted_at.desc()).all()
    
    def get_quiz_results(self, quiz_id: int) -> List[QuizSubmission]:
        """Get all submissions for a quiz"""
        return QuizSubmission.query.filter_by(quiz_id=quiz_id).order_by(QuizSubmission.score.desc()).all()
    
    def get_quiz_statistics(self, quiz_id: int) -> Dict:
        """Get statistics for a quiz"""
        submissions = QuizSubmission.query.filter_by(quiz_id=quiz_id).all()
        
        if not submissions:
            return {
                'total_submissions': 0,
                'average_score': 0,
                'highest_score': 0,
                'lowest_score': 0
            }
        
        scores = [sub.score for sub in submissions]
        
        return {
            'total_submissions': len(submissions),
            'average_score': sum(scores) / len(scores),
            'highest_score': max(scores),
            'lowest_score': min(scores)
        }

