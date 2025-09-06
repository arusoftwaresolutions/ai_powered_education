from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

from .service import QuizService
from models.base import db
from models.user import User, UserRole
from models.quiz import Quiz, QuizQuestion, QuizSubmission
from models.course import Course

quizzes_bp = Blueprint('quizzes', __name__)
quiz_service = QuizService()

@quizzes_bp.route('/', methods=['GET'])
@jwt_required()
def get_quizzes():
    """Get quizzes based on user role and department"""
    try:
        # Ensure clean session state
        db.session.rollback()
        
        user_id = int(get_jwt_identity())
        user = db.session.get(User, int(user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        course_id = request.args.get('course_id', type=int)
        
        if course_id:
            quizzes = quiz_service.get_quizzes_by_course(user, course_id)
        else:
            quizzes = quiz_service.get_quizzes_for_user(user)
        
        return jsonify({
            'quizzes': [quiz.to_dict() for quiz in quizzes]
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error in get_quizzes: {str(e)}")
        return jsonify({'error': 'Failed to fetch quizzes'}), 500

@quizzes_bp.route('/<int:quiz_id>', methods=['GET'])
@jwt_required()
def get_quiz(quiz_id):
    """Get a specific quiz with questions"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(int(user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        quiz = quiz_service.get_quiz_by_id(user, quiz_id)
        if not quiz:
            return jsonify({'error': 'Quiz not found'}), 404
        
        # Get questions (without answers for students)
        questions = []
        for question in quiz.questions:
            q_data = question.to_dict()
            if user.role == UserRole.STUDENT:
                # Remove answer and explanation for students
                q_data.pop('answer', None)
                q_data.pop('explanation', None)
            questions.append(q_data)
        
        quiz_data = quiz.to_dict()
        quiz_data['questions'] = questions
        
        return jsonify({
            'quiz': quiz_data
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@quizzes_bp.route('/', methods=['POST'])
@jwt_required()
def create_quiz():
    """Create a new quiz (instructors and admins only)"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(int(user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if user.role not in [UserRole.INSTRUCTOR, UserRole.ADMIN]:
            return jsonify({'error': 'Only instructors and admins can create quizzes'}), 403
        
        data = request.get_json()
        
        if not all(key in data for key in ['title', 'course_id', 'topic', 'questions']):
            return jsonify({'error': 'Title, course_id, topic, and questions are required'}), 400
        
        # Verify course exists and user has access
        course = Course.query.get(data['course_id'])
        if not course:
            return jsonify({'error': 'Course not found'}), 404
        
        if user.role == UserRole.INSTRUCTOR and course.created_by != user_id:
            return jsonify({'error': 'Access denied to this course'}), 403
        
        quiz = quiz_service.create_quiz(user, data)
        
        return jsonify({
            'message': 'Quiz created successfully',
            'quiz': quiz.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@quizzes_bp.route('/<int:quiz_id>', methods=['PUT'])
@jwt_required()
def update_quiz(quiz_id):
    """Update a quiz (creator or admin only)"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(int(user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        quiz = Quiz.query.get(quiz_id)
        if not quiz:
            return jsonify({'error': 'Quiz not found'}), 404
        
        # Check permissions
        if user.role == UserRole.STUDENT:
            return jsonify({'error': 'Students cannot modify quizzes'}), 403
        
        course = Course.query.get(quiz.course_id)
        if user.role == UserRole.INSTRUCTOR and course.created_by != user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        data = request.get_json()
        
        # Update allowed fields
        if 'title' in data:
            quiz.title = data['title']
        if 'topic' in data:
            quiz.topic = data['topic']
        if 'description' in data:
            quiz.description = data['description']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Quiz updated successfully',
            'quiz': quiz.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@quizzes_bp.route('/<int:quiz_id>', methods=['DELETE'])
@jwt_required()
def delete_quiz(quiz_id):
    """Delete a quiz (creator or admin only)"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(int(user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        quiz = Quiz.query.get(quiz_id)
        if not quiz:
            return jsonify({'error': 'Quiz not found'}), 404
        
        # Check permissions
        if user.role == UserRole.STUDENT:
            return jsonify({'error': 'Students cannot delete quizzes'}), 403
        
        course = Course.query.get(quiz.course_id)
        if user.role == UserRole.INSTRUCTOR and course.created_by != user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        db.session.delete(quiz)
        db.session.commit()
        
        return jsonify({
            'message': 'Quiz deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@quizzes_bp.route('/<int:quiz_id>/submit', methods=['POST'])
@jwt_required()
def submit_quiz(quiz_id):
    """Submit quiz answers and get score"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(int(user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if user.role != UserRole.STUDENT:
            return jsonify({'error': 'Only students can submit quizzes'}), 403
        
        data = request.get_json()
        answers = data.get('answers', {})
        
        if not answers:
            return jsonify({'error': 'Answers are required'}), 400
        
        # Submit quiz and get results
        submission = quiz_service.submit_quiz(user_id, quiz_id, answers)
        
        return jsonify({
            'message': 'Quiz submitted successfully',
            'submission': submission.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@quizzes_bp.route('/<int:quiz_id>/results', methods=['GET'])
@jwt_required()
def get_quiz_results(quiz_id):
    """Get quiz results for a specific user"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(int(user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get quiz submission
        submission = QuizSubmission.query.filter_by(
            quiz_id=quiz_id, 
            user_id=user_id
        ).first()
        
        if not submission:
            return jsonify({'error': 'No submission found for this quiz'}), 404
        
        # Get quiz details
        quiz = Quiz.query.get(quiz_id)
        if not quiz:
            return jsonify({'error': 'Quiz not found'}), 404
        
        # Get questions with correct answers for review
        questions = []
        for question in quiz.questions:
            q_data = question.to_dict()
            questions.append(q_data)
        
        return jsonify({
            'submission': submission.to_dict(),
            'quiz': quiz.to_dict(),
            'questions': questions
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@quizzes_bp.route('/history', methods=['GET'])
@jwt_required()
def get_quiz_history():
    """Get user's quiz submission history"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(int(user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        submissions = quiz_service.get_user_quiz_history(user_id)
        
        return jsonify({
            'submissions': [sub.to_dict() for sub in submissions]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@quizzes_bp.route('/import', methods=['POST'])
@jwt_required()
def import_quiz():
    """Import a quiz from file (instructors and admins only)"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(int(user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if user.role not in [UserRole.INSTRUCTOR, UserRole.ADMIN]:
            return jsonify({'error': 'Only instructors and admins can import quizzes'}), 403
        
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Get form data
        course_id = request.form.get('course_id')
        title = request.form.get('title', '')
        description = request.form.get('description', '')
        difficulty = request.form.get('difficulty', 'intermediate')
        
        if not course_id:
            return jsonify({'error': 'Course ID is required'}), 400
        
        # Verify course exists and user has access
        course = Course.query.get(course_id)
        if not course:
            return jsonify({'error': 'Course not found'}), 404
        
        if user.role == UserRole.INSTRUCTOR and course.created_by != user_id:
            return jsonify({'error': 'Access denied to this course'}), 403
        
        # Import quiz from file
        quiz = quiz_service.import_quiz_from_file(
            user, file, course_id, title, description, difficulty
        )
        
        return jsonify({
            'message': 'Quiz imported successfully',
            'quiz': quiz.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

