from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

from .service import CourseService
from models.base import db
from models.user import User, UserRole
from models.course import Course
from models.department import Department

courses_bp = Blueprint('courses', __name__)
course_service = CourseService()

@courses_bp.route('/', methods=['GET'])
@jwt_required()
def get_courses():
    """Get courses based on user role and department"""
    try:
        # Ensure clean session state
        db.session.rollback()
        
        user_id = int(get_jwt_identity())
        user = db.session.get(User, int(user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get courses based on user role
        if user.role == UserRole.ADMIN:
            courses = Course.query.all()
        elif user.role == UserRole.INSTRUCTOR:
            courses = Course.query.filter_by(created_by=user_id).all()
        else:  # Student
            courses = Course.query.filter_by(department_id=user.department_id).all()
        
        return jsonify({
            'success': True,
            'data': [course.to_dict() for course in courses]
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error in get_courses: {str(e)}")
        return jsonify({'error': 'Failed to fetch courses'}), 500

@courses_bp.route('/ai-tutor', methods=['GET'])
@jwt_required()
def get_courses_for_ai_tutor():
    """Get courses for AI tutor dropdown (simplified data)"""
    try:
        # Ensure clean session state
        db.session.rollback()
        
        user_id = int(get_jwt_identity())
        user = db.session.get(User, int(user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get courses based on user role
        if user.role == UserRole.ADMIN:
            courses = Course.query.all()
        elif user.role == UserRole.INSTRUCTOR:
            courses = Course.query.filter_by(created_by=user_id).all()
        else:  # Student
            courses = Course.query.filter_by(department_id=user.department_id).all()
        
        # Return simplified course data for AI tutor
        course_data = []
        for course in courses:
            course_data.append({
                'id': course.id,
                'title': course.title,
                'code': course.department.name[:2].upper() if course.department else 'N/A',  # Generate code from department name
                'department': course.department.name if course.department else 'Unknown'
            })
        
        return jsonify({
            'success': True,
            'data': course_data
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@courses_bp.route('/<int:course_id>/topics', methods=['GET'])
@jwt_required()
def get_course_topics(course_id):
    """Get topics/resources for a specific course"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(int(user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Check if course exists
        course = Course.query.get(course_id)
        if not course:
            return jsonify({'error': 'Course not found'}), 404
        
        # Check if user has access to this course
        if user.role == UserRole.STUDENT and course.department_id != user.department_id:
            return jsonify({'error': 'Access denied'}), 403
        elif user.role == UserRole.INSTRUCTOR and course.created_by != user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        # Get resources/topics for the course
        from models.resource import Resource
        resources = Resource.query.filter_by(course_id=course_id).all()
        
        # Return simplified topic data
        topics = []
        for resource in resources:
            topics.append({
                'id': resource.id,
                'title': resource.title,
                'type': resource.type.value if resource.type else 'text',
                'description': resource.description
            })
        
        return jsonify({
            'success': True,
            'data': topics
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@courses_bp.route('/<int:course_id>', methods=['GET'])
@jwt_required()
def get_course(course_id):
    """Get a specific course"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(int(user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        course = Course.query.get(course_id)
        if not course:
            return jsonify({'error': 'Course not found'}), 404
        
        # Check access permissions
        if user.role == UserRole.STUDENT and course.department_id != user.department_id:
            return jsonify({'error': 'Access denied'}), 403
        
        if user.role == UserRole.INSTRUCTOR and course.created_by != user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        return jsonify({
            'course': course.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@courses_bp.route('/', methods=['POST'])
@jwt_required()
def create_course():
    """Create a new course (instructors and admins only)"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(int(user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if user.role not in [UserRole.INSTRUCTOR, UserRole.ADMIN]:
            return jsonify({'error': 'Only instructors and admins can create courses'}), 403
        
        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        # Handle department field (can be name or ID)
        department = None
        if 'department' in data:
            # Department name provided
            department = Department.query.filter_by(name=data['department']).first()
        elif 'department_id' in data:
            # Department ID provided
            department = Department.query.get(data['department_id'])
        
        if not department:
            return jsonify({'error': 'Invalid department'}), 400
        
        if not all(key in data for key in ['title', 'description']):
            return jsonify({'error': 'Title and description are required'}), 400
        
        # Check if instructor can create course in this department
        if user.role == UserRole.INSTRUCTOR and user.department_id != department.id:
            return jsonify({'error': 'You can only create courses in your department'}), 403
        
        course = Course(
            title=data['title'],
            description=data['description'],
            department_id=department.id,
            created_by=user_id
        )
        
        db.session.add(course)
        db.session.commit()
        
        return jsonify({
            'message': 'Course created successfully',
            'course': course.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@courses_bp.route('/<int:course_id>', methods=['PUT'])
@jwt_required()
def update_course(course_id):
    """Update a course (creator or admin only)"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(int(user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        course = Course.query.get(course_id)
        if not course:
            return jsonify({'error': 'Course not found'}), 404
        
        # Check permissions
        if user.role == UserRole.STUDENT:
            return jsonify({'error': 'Students cannot modify courses'}), 403
        
        if user.role == UserRole.INSTRUCTOR and course.created_by != user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        data = request.get_json()
        
        # Update allowed fields
        if 'title' in data:
            course.title = data['title']
        if 'description' in data:
            course.description = data['description']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Course updated successfully',
            'course': course.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@courses_bp.route('/<int:course_id>', methods=['DELETE'])
@jwt_required()
def delete_course(course_id):
    """Delete a course (creator or admin only)"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(int(user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        course = Course.query.get(course_id)
        if not course:
            return jsonify({'error': 'Course not found'}), 404
        
        # Check permissions
        if user.role == UserRole.STUDENT:
            return jsonify({'error': 'Students cannot delete courses'}), 403
        
        if user.role == UserRole.INSTRUCTOR and course.created_by != user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        db.session.delete(course)
        db.session.commit()
        
        return jsonify({
            'message': 'Course deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@courses_bp.route('/department/<int:department_id>', methods=['GET'])
@jwt_required()
def get_courses_by_department(department_id):
    """Get courses by department"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(int(user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Check if user has access to this department
        if user.role == UserRole.STUDENT and user.department_id != department_id:
            return jsonify({'error': 'Access denied'}), 403
        
        courses = Course.query.filter_by(department_id=department_id).all()
        
        return jsonify({
            'success': True,
            'data': [course.to_dict() for course in courses]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

