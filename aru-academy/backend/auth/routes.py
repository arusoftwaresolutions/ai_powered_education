from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash
from datetime import timedelta
import re

from .service import AuthService
from .utils import validate_email, validate_password
from models.base import db
from sqlalchemy.orm import joinedload
from models.user import User, UserRole, UserStatus
from models.approved_user import ApprovedUser
from models.department import Department

auth_bp = Blueprint('auth', __name__)
auth_service = AuthService()

@auth_bp.route('/self-register', methods=['POST'])
def self_register():
    """Self-register user by checking database for existing info"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'email', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'{field} is required'}), 400
        
        # Validate email format
        if not validate_email(data['email']):
            return jsonify({'success': False, 'error': 'Invalid email format'}), 400
        
        # Validate password strength
        if not validate_password(data['password']):
            return jsonify({'success': False, 'error': 'Password must be at least 8 characters long'}), 400
        
        # Attempt self-registration
        result = auth_service.self_register_user(
            name=data['name'],
            email=data['email'],
            password=data['password']
        )
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'email', 'password', 'department', 'role']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'{field} is required'}), 400
        
        # Validate email format
        if not validate_email(data['email']):
            return jsonify({'success': False, 'error': 'Invalid email format'}), 400
        
        # Validate password strength
        if not validate_password(data['password']):
            return jsonify({'success': False, 'error': 'Password must be at least 8 characters with letters and numbers'}), 400
        
        # Check if user already exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'success': False, 'error': 'User with this email already exists'}), 400
        
        # Get department
        department = Department.query.filter_by(name=data['department']).first()
        if not department:
            return jsonify({'success': False, 'error': 'Invalid department'}), 400
        
        # Check if user is pre-approved for this specific department
        approved_user = ApprovedUser.query.filter_by(email=data['email'], department_id=department.id).first()
        if not approved_user:
            # Debug: Log available approved users
            all_approved = ApprovedUser.query.all()
            print(f"DEBUG: No approved user found for {data['email']} in department {data['department']}")
            print(f"DEBUG: Available approved users: {[(au.email, au.department.name if hasattr(au, 'department') and au.department else 'Unknown') for au in all_approved]}")
            return jsonify({'success': False, 'error': 'You must be approved by the admin to register. Please contact your administrator for approval.'}), 403
        
        # Validate role matches approved role (handle case differences)
        role_lower = data['role'].lower()
        approved_role_lower = approved_user.role.lower()
        if approved_role_lower != role_lower:
            return jsonify({'success': False, 'error': f'You are approved as {approved_user.role}, but you selected {data["role"]}. Please select the correct role.'}), 403
        
        # Create user
        user = User(
            name=data['name'],
            email=data['email'],
            role=UserRole(role_lower),
            department_id=department.id,
            status=UserStatus.ACTIVE
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        # Remove from approved users
        db.session.delete(approved_user)
        db.session.commit()
        
        # Ensure department relationship is loaded
        if not hasattr(user, 'department') or user.department is None:
            user = User.query.options(db.joinedload(User.department)).filter_by(id=user.id).first()
        
        return jsonify({
            'success': True,
            'message': 'User registered successfully',
            'data': {
                'user': user.to_dict()
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user and return JWT token"""
    try:
        data = request.get_json()
        
        if not data.get('email') or not data.get('password'):
            return jsonify({'success': False, 'error': 'Email and password are required'}), 400
        
        user = User.query.filter_by(email=data['email']).first()
        
        if not user:
            print(f"DEBUG: No user found for email: {data['email']}")
            return jsonify({'success': False, 'error': 'Invalid email or password'}), 401
        
        if not user.check_password(data['password']):
            print(f"DEBUG: Password check failed for user: {data['email']}")
            return jsonify({'success': False, 'error': 'Invalid email or password'}), 401
        
        if user.status != UserStatus.ACTIVE:
            return jsonify({'success': False, 'error': 'Account is not active'}), 403
        
        # Ensure department relationship is loaded
        if not hasattr(user, 'department') or user.department is None:
            user = User.query.options(db.joinedload(User.department)).filter_by(id=user.id).first()
        
        # Create access token with appropriate expiration
        remember_me = data.get('remember_me', False)
        expires_delta = timedelta(days=30) if remember_me else timedelta(hours=24)
        
        access_token = create_access_token(
            identity=str(user.id),
            expires_delta=expires_delta
        )
        
        print(f"DEBUG: Created JWT token for user {user.id}: {access_token[:50]}...")
        
        response = jsonify({
            'success': True,
            'message': 'Login successful',
            'data': {
                'user': user.to_dict(),
                'access_token': access_token
            }
        })
        
        return response, 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout user"""
    try:
        # JWT cookies are automatically cleared by the frontend
        return jsonify({'message': 'Logout successful'}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user profile"""
    try:
        user_id = get_jwt_identity()
        print(f"DEBUG: Profile request - JWT identity: {user_id} (type: {type(user_id)})")
        
        if not user_id:
            print("DEBUG: No JWT identity found")
            return jsonify({'success': False, 'error': 'No JWT identity'}), 401
        
        user = User.query.get(int(user_id))
        
        if not user:
            print(f"DEBUG: No user found for ID: {user_id}")
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        print(f"DEBUG: Found user: {user.email}")
        return jsonify({
            'success': True,
            'data': {
                'user': user.to_dict()
            }
        }), 200
        
    except Exception as e:
        print(f"DEBUG: Profile error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update current user profile"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        # Update allowed fields
        if 'name' in data:
            user.name = data['name']
        
        if 'password' in data and data['password']:
            if not validate_password(data['password']):
                return jsonify({'success': False, 'error': 'Password must be at least 8 characters with letters and numbers'}), 400
            user.set_password(data['password'])
        
        db.session.commit()
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@auth_bp.route('/check-auth', methods=['GET'])
@jwt_required()
def check_auth():
    """Check if user is authenticated"""
    try:
        user_id = get_jwt_identity()
        print(f"DEBUG: Check auth - JWT identity: {user_id}")
        user = User.query.get(int(user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'authenticated': True,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        print(f"DEBUG: Check auth error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

