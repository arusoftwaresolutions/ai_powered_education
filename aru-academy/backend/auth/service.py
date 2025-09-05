from models.base import db
from models.user import User, UserRole, UserStatus
from models.approved_user import ApprovedUser
from models.department import Department
from werkzeug.security import generate_password_hash
import re
import secrets
import string

class AuthService:
    """Service layer for authentication operations"""
    
    def create_user(self, user_data):
        """Create a new user"""
        try:
            # Validate department exists
            department = Department.query.filter_by(name=user_data['department']).first()
            if not department:
                raise ValueError('Invalid department')
            
            # Create user
            user = User(
                name=user_data['name'],
                email=user_data['email'],
                role=UserRole(user_data['role']),
                department_id=department.id,
                status=UserStatus.ACTIVE
            )
            user.set_password(user_data['password'])
            
            db.session.add(user)
            db.session.commit()
            
            return user
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    def approve_user(self, name, email, role, department_name, approved_by):
        """Approve a user for registration"""
        try:
            # Check if department exists
            department = Department.query.filter_by(name=department_name).first()
            if not department:
                raise ValueError('Invalid department')
            
            # Check if user already approved
            existing = ApprovedUser.query.filter_by(email=email).first()
            if existing:
                raise ValueError('User already approved')
            
            # Create approved user record
            approved_user = ApprovedUser(
                name=name,
                email=email,
                role=role,
                department_id=department.id,
                approved_by=approved_by
            )
            
            db.session.add(approved_user)
            db.session.commit()
            
            return approved_user
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    def get_pending_users(self):
        """Get all pending user approvals"""
        return ApprovedUser.query.all()
    
    def get_user_by_email(self, email):
        """Get user by email"""
        return User.query.filter_by(email=email).first()
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        return User.query.get(user_id)
    
    def update_user_status(self, user_id, status):
        """Update user status"""
        try:
            user = User.query.get(user_id)
            if not user:
                raise ValueError('User not found')
            
            user.status = UserStatus(status)
            db.session.commit()
            
            return user
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    def change_password(self, user_id, new_password):
        """Change user password"""
        try:
            user = User.query.get(user_id)
            if not user:
                raise ValueError('User not found')
            
            user.set_password(new_password)
            db.session.commit()
            
            return user
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    def get_departments(self):
        """Get all departments"""
        return Department.query.all()
    
    def create_department(self, name, description=None):
        """Create a new department"""
        try:
            # Check if department already exists
            existing = Department.query.filter_by(name=name).first()
            if existing:
                raise ValueError('Department already exists')
            
            department = Department(name=name, description=description)
            db.session.add(department)
            db.session.commit()
            
            return department
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    def generate_temp_password(self, length=12):
        """Generate a temporary password"""
        characters = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(characters) for _ in range(length))
    
    def self_register_user(self, name, email, password):
        """Self-register user by checking database for existing info"""
        try:
            # Check if user already exists
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                return {
                    'success': False,
                    'error': 'User with this email already exists'
                }
            
            # Check if user exists in approved_users table
            try:
                approved_user = ApprovedUser.query.filter_by(email=email).first()
            except Exception as e:
                if "Unknown column 'approved_users.name'" in str(e):
                    # Fallback: query without name column
                    result = db.session.execute(
                        db.text("SELECT * FROM approved_users WHERE email = :email"),
                        {"email": email}
                    ).fetchone()
                    if not result:
                        return {
                            'success': False,
                            'error': 'You need permission from ARU Academy to register. Please contact the administration to get your account approved.'
                        }
                    # Create a mock object with the result
                    class MockApprovedUser:
                        def __init__(self, row):
                            self.id = row[0]
                            self.email = row[2]
                            self.role = row[3]
                            self.department_id = row[4]
                            self.approved_by = row[5]
                            self.approved_at = row[6]
                            self.created_at = row[7]
                            self.updated_at = row[8]
                            # For now, skip name verification if column doesn't exist
                            self.name = name  # Use the provided name
                    
                    approved_user = MockApprovedUser(result)
                else:
                    raise e
            
            if not approved_user:
                return {
                    'success': False,
                    'error': 'You need permission from ARU Academy to register. Please contact the administration to get your account approved.'
                }
            
            # Verify name matches (case insensitive) - skip if name column doesn't exist
            try:
                if hasattr(approved_user, 'name') and approved_user.name.lower() != name.lower():
                    return {
                        'success': False,
                        'error': 'Name does not match our records. Please check your name and try again, or contact administration if you believe this is an error.'
                    }
            except AttributeError:
                # Name column doesn't exist, skip verification
                pass
            
            # Get department
            department = Department.query.get(approved_user.department_id)
            if not department:
                return {
                    'success': False,
                    'error': 'Department information not found. Please contact ARU Academy administration for assistance.'
                }
            
            # Create the user account
            user = User(
                name=approved_user.name,
                email=approved_user.email,
                role=UserRole(approved_user.role),
                department_id=approved_user.department_id,
                status=UserStatus.ACTIVE
            )
            user.set_password(password)
            
            # Remove from approved_users table
            db.session.delete(approved_user)
            db.session.add(user)
            db.session.commit()
            
            return {
                'success': True,
                'message': 'Account created successfully! Welcome to ARU Academy!',
                'user': {
                    'id': user.id,
                    'name': user.name,
                    'email': user.email,
                    'role': user.role.value,
                    'department': department.name
                }
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': f'Registration failed: {str(e)}'
            }

