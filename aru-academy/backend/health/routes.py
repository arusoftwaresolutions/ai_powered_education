"""
Health check routes for ARU Academy
"""

from flask import Blueprint, jsonify, request
from .checker import HealthChecker

import logging

logger = logging.getLogger(__name__)

health_bp = Blueprint('health', __name__)
health_checker = HealthChecker()

def success_response(data=None, message="Success", status_code=200):
    """Simple success response helper"""
    response = {
        'success': True,
        'message': message,
        'data': data
    }
    return response, status_code

def error_response(message="Error", status_code=400, data=None):
    """Simple error response helper"""
    response = {
        'success': False,
        'message': message,
        'data': data
    }
    return response, status_code

@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    Basic health check endpoint
    """
    try:
        status = health_checker.check_basic_health()
        return success_response(
            data=status,
            message="System health check completed"
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return error_response(
            message="Health check failed",
            status_code=500
        )

@health_bp.route('/health/detailed', methods=['GET'])
def detailed_health_check():
    """
    Detailed health check endpoint
    """
    try:
        status = health_checker.check_detailed_health()
        return success_response(
            data=status,
            message="Detailed health check completed"
        )
    except Exception as e:
        logger.error(f"Detailed health check failed: {str(e)}")
        return error_response(
            message="Detailed health check failed",
            status_code=500
        )

@health_bp.route('/health/database', methods=['GET'])
def database_health_check():
    """
    Database health check endpoint
    """
    try:
        status = health_checker.check_database_health()
        return success_response(
            data=status,
            message="Database health check completed"
        )
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return error_response(
            message="Database health check failed",
            status_code=500
        )

@health_bp.route('/health/ai', methods=['GET'])
def ai_health_check():
    """
    AI service health check endpoint
    """
    try:
        status = health_checker.check_ai_health()
        return success_response(
            data=status,
            message="AI service health check completed"
        )
    except Exception as e:
        logger.error(f"AI health check failed: {str(e)}")
        return error_response(
            message="AI health check failed",
            status_code=500
        )

@health_bp.route('/health/system', methods=['GET'])
def system_health_check():
    """
    System resources health check endpoint
    """
    try:
        status = health_checker.check_system_health()
        return success_response(
            data=status,
            message="System resources health check completed"
        )
    except Exception as e:
        logger.error(f"System health check failed: {str(e)}")
        return error_response(
            message="System health check failed",
            status_code=500
        )

@health_bp.route('/health/metrics', methods=['GET'])
def health_metrics():
    """
    Health metrics endpoint
    """
    try:
        metrics = health_checker.get_health_metrics()
        return success_response(
            data=metrics,
            message="Health metrics retrieved"
        )
    except Exception as e:
        logger.error(f"Health metrics failed: {str(e)}")
        return error_response(
            message="Health metrics failed",
            status_code=500
        )

@health_bp.route('/health/status', methods=['GET'])
def overall_status():
    """
    Overall system status endpoint
    """
    try:
        status = health_checker.get_overall_status()
        return success_response(
            data=status,
            message="Overall system status retrieved"
        )
    except Exception as e:
        logger.error(f"Overall status failed: {str(e)}")
        return error_response(
            message="Overall status failed",
            status_code=500
        )

@health_bp.route('/seed-database', methods=['POST'])
def seed_database():
    """
    Seed the database with initial data
    """
    try:
        from app import create_approved_users, seed_database_if_empty
        
        # Always create approved users first
        create_approved_users()
        
        # Then run full seeding if needed
        seed_database_if_empty()
        
        return success_response(
            message="Database seeding completed successfully!"
        )
        
    except Exception as e:
        logger.error(f"Database seeding failed: {str(e)}")
        return error_response(
            message=f"Database seeding failed: {str(e)}",
            status_code=500
        )

@health_bp.route('/force-seed-database', methods=['POST'])
def force_seed_database():
    """
    Force seed the database with new content (deletes existing courses/resources)
    """
    try:
        from app import force_seed_database
        
        # Run force seeding
        force_seed_database()
        
        return success_response(
            message="Force database seeding completed successfully! All courses and resources have been recreated with new content."
        )
        
    except Exception as e:
        logger.error(f"Force database seeding failed: {str(e)}")
        return error_response(
            message=f"Force database seeding failed: {str(e)}",
            status_code=500
        )

@health_bp.route('/check-approved-users', methods=['GET'])
def check_approved_users():
    """
    Check the current state of approved users
    """
    try:
        from models.approved_user import ApprovedUser
        from models.department import Department
        from models.user import User
        
        approved_users = ApprovedUser.query.all()
        departments = Department.query.all()
        users = User.query.all()
        
        return success_response(
            data={
                'approved_users_count': len(approved_users),
                'approved_users': [{'email': au.email, 'role': au.role, 'department': au.department.name if au.department else 'None'} for au in approved_users],
                'departments_count': len(departments),
                'departments': [{'name': d.name} for d in departments],
                'users_count': len(users),
                'users': [{'email': u.email, 'role': u.role.value if u.role else 'None', 'status': u.status.value if u.status else 'None'} for u in users]
            },
            message="Database state checked successfully"
        )
        
    except Exception as e:
        logger.error(f"Database check failed: {str(e)}")
        return error_response(
            message=f"Database check failed: {str(e)}",
            status_code=500
        )

@health_bp.route('/test-auth', methods=['GET'])
def test_auth():
    """
    Test authentication endpoint
    """
    try:
        from flask_jwt_extended import get_jwt_identity
        from models.user import User
        
        user_id = get_jwt_identity()
        if not user_id:
            return error_response("No JWT token provided", 401)
        
        user = User.query.get(int(user_id))
        if not user:
            return error_response("User not found", 404)
        
        return success_response(
            data={
                'user_id': user_id,
                'user_email': user.email,
                'user_role': user.role.value if user.role else 'None',
                'user_status': user.status.value if user.status else 'None'
            },
            message="Authentication test successful"
        )
        
    except Exception as e:
        logger.error(f"Auth test failed: {str(e)}")
        return error_response(
            message=f"Auth test failed: {str(e)}",
            status_code=500
        )

