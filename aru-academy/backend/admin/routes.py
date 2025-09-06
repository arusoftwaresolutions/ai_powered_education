from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import csv
import io
from functools import wraps

from .service import AdminService
from models.base import db
from models.user import User, UserRole, UserStatus
from models.approved_user import ApprovedUser
from models.department import Department
from models.course import Course
from models.resource import Resource
from models.quiz import Quiz, QuizSubmission
from models.ai_log import AiCallLog

admin_bp = Blueprint('admin', __name__)
admin_service = AdminService()

def require_admin(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            user_id = int(get_jwt_identity())
            
            # Use a fresh session for the query
            from models.base import db
            user = db.session.get(User, user_id)
            
            if not user or user.role != UserRole.ADMIN:
                return jsonify({'error': 'Admin access required'}), 403
            
            return f(*args, **kwargs)
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': f'Authentication error: {str(e)}'}), 500
    return decorated_function

@admin_bp.route('/dashboard', methods=['GET'])
@jwt_required()
@require_admin
def get_dashboard():
    """Get admin dashboard statistics"""
    try:
        stats = admin_service.get_dashboard_stats()
        return jsonify({
            'success': True,
            'data': stats
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users', methods=['GET'])
@jwt_required()
@require_admin
def get_users():
    """Get all users with filtering"""
    try:
        search = request.args.get('search')
        role = request.args.get('role')
        department_id = request.args.get('department_id', type=int)
        status = request.args.get('status')
        
        users = admin_service.get_users(search, role, department_id, status)
        
        return jsonify({
            'success': True,
            'data': [user.to_dict() for user in users],
            'total': len(users)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
@require_admin
def update_user(user_id):
    """Update user status or role"""
    try:
        data = request.get_json()
        print(f"🔧 Update user request for ID {user_id}: {data}")
        
        if 'status' in data:
            print(f"📋 Updating status to: {data['status']}")
            user = admin_service.update_user_status(user_id, data['status'])
            print(f"✅ Status update successful for user {user.name}")
        elif 'role' in data:
            print(f"📋 Updating role to: {data['role']}")
            user = admin_service.update_user_role(user_id, data['role'])
            print(f"✅ Role update successful for user {user.name}")
        else:
            return jsonify({'error': 'No valid update field provided'}), 400
        
        user_dict = user.to_dict()
        print(f"📤 Returning user data: {user_dict}")
        
        return jsonify({
            'success': True,
            'message': 'User updated successfully',
            'user': user_dict
        }), 200
    except Exception as e:
        print(f"❌ Error in update_user route: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
@require_admin
def delete_user(user_id):
    """Delete a user"""
    try:
        admin_service.delete_user(user_id)
        return jsonify({'message': 'User deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/pending-users', methods=['GET'])
@jwt_required()
@require_admin
def get_pending_users():
    """Get all pending user approvals"""
    try:
        pending_users = admin_service.get_pending_users()
        return jsonify({
            'success': True,
            'data': [user.to_dict() for user in pending_users]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/pending-users/<int:user_id>/approve', methods=['POST'])
@jwt_required()
@require_admin
def approve_user(user_id):
    """Approve a pending user"""
    try:
        data = request.get_json()
        role = data.get('role')
        department = data.get('department')
        
        if not role or not department:
            return jsonify({'error': 'Role and department are required'}), 400
        
        approved_user = admin_service.approve_user(user_id, role, department)
        return jsonify({
            'message': 'User approved successfully',
            'approved_user': approved_user.to_dict()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/pending-users/<int:user_id>/deny', methods=['POST'])
@jwt_required()
@require_admin
def deny_user(user_id):
    """Deny a pending user"""
    try:
        admin_service.deny_user(user_id)
        return jsonify({'message': 'User denied successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/approve-all-users', methods=['POST'])
@jwt_required()
@require_admin
def approve_all_users():
    """Approve all pending users"""
    try:
        result = admin_service.approve_all_users()
        return jsonify({
            'success': True,
            'message': f'Approved {result["approved_count"]} users successfully',
            'approved_count': result['approved_count'],
            'errors': result['errors']
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/departments', methods=['GET'])
@jwt_required()
@require_admin
def get_departments():
    """Get all departments"""
    try:
        departments = admin_service.get_departments()
        return jsonify({
            'success': True,
            'data': departments  # Already returns list of dicts
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/departments', methods=['POST'])
@jwt_required()
@require_admin
def create_department():
    """Create a new department"""
    try:
        data = request.get_json()
        
        if not all(key in data for key in ['name', 'description']):
            return jsonify({'error': 'Name and description are required'}), 400
        
        department = admin_service.create_department(data['name'], data['description'])
        return jsonify({
            'message': 'Department created successfully',
            'department': department.to_dict()
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/departments/<int:dept_id>', methods=['PUT'])
@jwt_required()
@require_admin
def update_department(dept_id):
    """Update a department"""
    try:
        data = request.get_json()
        
        department = admin_service.update_department(dept_id, data)
        return jsonify({
            'message': 'Department updated successfully',
            'department': department.to_dict()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/departments/<int:dept_id>', methods=['DELETE'])
@jwt_required()
@require_admin
def delete_department(dept_id):
    """Delete a department"""
    try:
        admin_service.delete_department(dept_id)
        return jsonify({'message': 'Department deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/import-users', methods=['POST'])
@jwt_required()
@require_admin
def import_users():
    """Import approved users from CSV"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({'error': 'File must be a CSV'}), 400
        
        # Read CSV
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_reader = csv.DictReader(stream)
        
        imported_users = []
        errors = []
        
        for row_num, row in enumerate(csv_reader, 1):
            try:
                # Validate required fields
                required_fields = ['name', 'email', 'role', 'department']
                for field in required_fields:
                    if not row.get(field):
                        errors.append(f"Row {row_num}: Missing {field}")
                        continue
                
                # Create approved user
                approved_user = admin_service.create_approved_user_from_csv(row)
                imported_users.append(approved_user.to_dict())
                
            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")
        
        return jsonify({
            'message': f'Imported {len(imported_users)} users successfully',
            'imported_users': imported_users,
            'errors': errors
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/analytics', methods=['GET'])
@jwt_required()
@require_admin
def get_analytics():
    """Get detailed analytics"""
    try:
        period = request.args.get('period', 30, type=int)
        analytics = admin_service.get_analytics(period)
        return jsonify(analytics), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/export-users', methods=['GET'])
@jwt_required()
@require_admin
def export_users():
    """Export all users to CSV"""
    try:
        result = admin_service.export_users_to_csv()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/ai-logs', methods=['GET'])
@jwt_required()
@require_admin
def get_ai_logs():
    """Get AI usage logs"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        logs = admin_service.get_ai_logs(page, per_page)
        return jsonify(logs), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/system-health', methods=['GET'])
@jwt_required()
@require_admin
def get_system_health():
    """Get system health status"""
    try:
        health = admin_service.get_system_health()
        return jsonify({
            'success': True,
            'data': health
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

