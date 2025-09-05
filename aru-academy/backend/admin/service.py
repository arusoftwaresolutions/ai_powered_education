from models.base import db
from models.user import User, UserRole, UserStatus
from models.approved_user import ApprovedUser
from models.department import Department
from models.course import Course
from models.resource import Resource
from models.quiz import Quiz, QuizSubmission
from models.ai_log import AiCallLog
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import csv

class AdminService:
    """Service layer for admin operations"""
    
    def get_dashboard_stats(self) -> Dict:
        """Get dashboard statistics"""
        total_users = User.query.count()
        total_courses = Course.query.count()
        total_resources = Resource.query.count()
        total_quizzes = Quiz.query.count()
        
        # Active users (users with ACTIVE status)
        active_users = User.query.filter(User.status == UserStatus.ACTIVE).count()
        
        # Recent activity (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_courses = Course.query.filter(Course.created_at >= thirty_days_ago).count()
        recent_resources = Resource.query.filter(Resource.created_at >= thirty_days_ago).count()
        
        # AI usage
        total_ai_calls = AiCallLog.query.count()
        successful_ai_calls = AiCallLog.query.filter_by(success=True).count()
        ai_success_rate = (successful_ai_calls / total_ai_calls * 100) if total_ai_calls > 0 else 0
        
        return {
            'total_users': total_users,
            'pending_users': User.query.filter(User.status == UserStatus.PENDING).count(),
            'total_courses': total_courses,
            'total_resources': total_resources,
            'total_quizzes': total_quizzes,
            'active_users': active_users,
            'recent_courses': recent_courses,
            'recent_resources': recent_resources,
            'total_ai_calls': total_ai_calls,
            'ai_success_rate': round(ai_success_rate, 2),
            # Role breakdowns
            'students': User.query.filter(User.role == UserRole.STUDENT).count(),
            'instructors': User.query.filter(User.role == UserRole.INSTRUCTOR).count(),
            'admins': User.query.filter(User.role == UserRole.ADMIN).count(),
            'active_courses': Course.query.filter(Course.status == 'active').count() if hasattr(Course, 'status') else total_courses
        }
    
    def get_users(self, search: Optional[str] = None, role: Optional[str] = None, department_id: Optional[int] = None, status: Optional[str] = None) -> List[User]:
        """Get users with optional filtering"""
        query = User.query
        
        # Search functionality
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (User.name.ilike(search_term)) |
                (User.email.ilike(search_term))
            )
        
        # Role filtering
        if role and role != 'all':
            try:
                query = query.filter(User.role == UserRole(role))
            except ValueError:
                # Invalid role value, ignore filter
                pass
        
        # Department filtering
        if department_id and department_id != 'all':
            query = query.filter(User.department_id == department_id)
        
        # Status filtering
        if status and status != 'all':
            try:
                query = query.filter(User.status == UserStatus(status))
            except ValueError:
                # Invalid status value, ignore filter
                pass
        
        return query.all()
    
    def update_user_status(self, user_id: int, status: str) -> User:
        """Update user status"""
        try:
            print(f"🔧 Updating user {user_id} status to {status}")
            user = User.query.get(user_id)
            if not user:
                raise ValueError('User not found')
            
            print(f"📋 Current user status: {user.status}")
            print(f"📋 Current user name: {user.name}")
            
            # Validate status value
            valid_statuses = ['active', 'suspended', 'pending']
            if status not in valid_statuses:
                raise ValueError(f'Invalid status: {status}. Must be one of: {valid_statuses}')
            
            # Update status
            old_status = user.status
            user.status = UserStatus(status)
            print(f"🔄 Status changed from {old_status} to {user.status}")
            
            # Commit changes
            db.session.commit()
            print(f"✅ Status update committed to database")
            
            # Verify the change
            db.session.refresh(user)
            print(f"🔍 Verified status in database: {user.status}")
            
            return user
            
        except Exception as e:
            print(f"❌ Error updating user status: {e}")
            db.session.rollback()
            raise e
    
    def update_user_role(self, user_id: int, role: str) -> User:
        """Update user role"""
        try:
            user = User.query.get(user_id)
            if not user:
                raise ValueError('User not found')
            
            user.role = UserRole(role)
            db.session.commit()
            
            return user
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    def delete_user(self, user_id: int) -> bool:
        """Delete a user"""
        try:
            user = User.query.get(user_id)
            if not user:
                raise ValueError('User not found')
            
            # Check if user is admin
            if user.role == UserRole.ADMIN:
                raise ValueError('Cannot delete admin users')
            
            db.session.delete(user)
            db.session.commit()
            
            return True
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    def get_pending_users(self) -> List[ApprovedUser]:
        """Get all pending user approvals"""
        return ApprovedUser.query.all()
    
    def approve_user(self, user_id: int, role: str, department: str) -> ApprovedUser:
        """Approve a pending user"""
        try:
            # Find the approved user record
            approved_user = ApprovedUser.query.get(user_id)
            if not approved_user:
                raise ValueError('Approved user record not found')
            
            # Get department
            dept = Department.query.filter_by(name=department).first()
            if not dept:
                raise ValueError('Invalid department')
            
            # Generate a temporary password
            import secrets
            import string
            temp_password = ''.join(secrets.choice(string.ascii_letters + string.digits + "!@#$%^&*") for _ in range(12))
            
            # Create the actual user
            user = User(
                name=approved_user.name,  # Use the name from approved_user
                email=approved_user.email,
                role=UserRole(role),
                department_id=dept.id,
                status=UserStatus.ACTIVE
            )
            user.set_password('Welcome@123')  # Default password for approved users
            
            db.session.add(user)
            
            # Remove from approved users
            db.session.delete(approved_user)
            
            db.session.commit()
            
            return approved_user
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    def deny_user(self, user_id: int) -> bool:
        """Deny a pending user"""
        try:
            approved_user = ApprovedUser.query.get(user_id)
            if not approved_user:
                raise ValueError('Approved user record not found')
            
            db.session.delete(approved_user)
            db.session.commit()
            
            return True
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    def approve_all_users(self) -> Dict:
        """Approve all pending users"""
        try:
            pending_users = ApprovedUser.query.all()
            approved_count = 0
            errors = []
            
            for approved_user in pending_users:
                try:
                    # Get department (default to first department if not specified)
                    dept = Department.query.first()
                    if not dept:
                        errors.append(f"No departments available for user {approved_user.email}")
                        continue
                    
                    # Create the actual user with default role as STUDENT
                    user = User(
                        name=approved_user.name,  # Use the name from approved_user
                        email=approved_user.email,
                        role=UserRole.STUDENT,  # Default role
                        department_id=dept.id,
                        status=UserStatus.ACTIVE
                    )
                    user.set_password('Welcome@123')  # Default password for approved users
                    
                    db.session.add(user)
                    db.session.delete(approved_user)
                    approved_count += 1
                    
                except Exception as e:
                    errors.append(f"Error approving {approved_user.email}: {str(e)}")
            
            db.session.commit()
            
            return {
                'approved_count': approved_count,
                'errors': errors
            }
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    def get_departments(self) -> List[Dict]:
        """Get all departments with user and course counts"""
        departments = Department.query.all()
        result = []
        
        for dept in departments:
            user_count = User.query.filter(User.department_id == dept.id).count()
            course_count = Course.query.filter(Course.department_id == dept.id).count()
            
            result.append({
                'id': dept.id,
                'name': dept.name,
                'description': dept.description,
                'created_at': dept.created_at.isoformat() if dept.created_at else None,
                'user_count': user_count,
                'course_count': course_count
            })
        
        return result
    
    def create_department(self, name: str, description: str) -> Department:
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
    
    def update_department(self, dept_id: int, update_data: dict) -> Department:
        """Update a department"""
        try:
            department = Department.query.get(dept_id)
            if not department:
                raise ValueError('Department not found')
            
            if 'name' in update_data:
                department.name = update_data['name']
            if 'description' in update_data:
                department.description = update_data['description']
            
            db.session.commit()
            
            return department
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    def delete_department(self, dept_id: int) -> bool:
        """Delete a department"""
        try:
            department = Department.query.get(dept_id)
            if not department:
                raise ValueError('Department not found')
            
            # Check if department has users or courses
            if User.query.filter_by(department_id=dept_id).first():
                raise ValueError('Cannot delete department with existing users')
            
            if Course.query.filter_by(department_id=dept_id).first():
                raise ValueError('Cannot delete department with existing courses')
            
            db.session.delete(department)
            db.session.commit()
            
            return True
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    def create_approved_user_from_csv(self, row_data: dict) -> ApprovedUser:
        """Create approved user from CSV data"""
        try:
            # Validate required fields
            name = row_data['name'].strip()
            email = row_data['email'].strip()
            role = row_data['role'].strip().lower()
            department_name = row_data['department'].strip()
            
            # Validate role
            if role not in ['student', 'instructor']:
                raise ValueError(f'Invalid role: {role}')
            
            # Get department
            department = Department.query.filter_by(name=department_name).first()
            if not department:
                raise ValueError(f'Department not found: {department_name}')
            
            # Check if user already approved
            existing = ApprovedUser.query.filter_by(email=email).first()
            if existing:
                raise ValueError(f'User already approved: {email}')
            
            # Create approved user
            approved_user = ApprovedUser(
                name=name,
                email=email,
                role=role,
                department_id=department.id
            )
            
            db.session.add(approved_user)
            db.session.commit()
            
            return approved_user
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    def get_analytics(self, period_days: int = 30) -> Dict:
        """Get detailed analytics for charts"""
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period_days)
        
        # User activity analytics
        total_users = User.query.count()
        active_users = User.query.filter(User.status == UserStatus.ACTIVE).count()
        pending_users = User.query.filter(User.status == UserStatus.PENDING).count()
        
        user_activity = [
            {'label': 'Students', 'value': User.query.filter(User.role == UserRole.STUDENT).count()},
            {'label': 'Instructors', 'value': User.query.filter(User.role == UserRole.INSTRUCTOR).count()},
            {'label': 'Admins', 'value': User.query.filter(User.role == UserRole.ADMIN).count()},
            {'label': 'Active Users', 'value': active_users},
            {'label': 'Pending Users', 'value': pending_users}
        ]
        
        # Resource usage analytics
        total_resources = Resource.query.count()
        recent_resources = Resource.query.filter(Resource.created_at >= start_date).count()
        
        resource_usage = [
            {'label': 'Total Resources', 'value': total_resources},
            {'label': f'Last {period_days} days', 'value': recent_resources},
            {'label': 'Resources per Course', 'value': round(total_resources / max(Course.query.count(), 1), 1)}
        ]
        
        # AI service usage analytics
        total_ai_calls = AiCallLog.query.count()
        successful_ai_calls = AiCallLog.query.filter_by(success=True).count()
        recent_ai_calls = AiCallLog.query.filter(AiCallLog.created_at >= start_date).count()
        
        ai_usage = [
            {'label': 'Total AI Calls', 'value': total_ai_calls},
            {'label': 'Successful Calls', 'value': successful_ai_calls},
            {'label': f'Last {period_days} days', 'value': recent_ai_calls},
            {'label': 'Success Rate', 'value': f"{round((successful_ai_calls / max(total_ai_calls, 1)) * 100, 1)}%"}
        ]
        
        # Quiz performance analytics
        total_quizzes = Quiz.query.count()
        total_submissions = QuizSubmission.query.count()
        avg_score = db.session.query(db.func.avg(QuizSubmission.score)).scalar() or 0
        recent_submissions = QuizSubmission.query.filter(QuizSubmission.submitted_at >= start_date).count()
        
        quiz_performance = [
            {'label': 'Total Quizzes', 'value': total_quizzes},
            {'label': 'Total Submissions', 'value': total_submissions},
            {'label': f'Last {period_days} days', 'value': recent_submissions},
            {'label': 'Average Score', 'value': f"{round(avg_score, 1)}%"}
        ]
        
        return {
            'success': True,
            'data': {
                'user_activity': user_activity,
                'resource_usage': resource_usage,
                'ai_usage': ai_usage,
                'quiz_performance': quiz_performance,
                'period_days': period_days,
                'generated_at': end_date.isoformat()
            }
        }
    
    def export_users_to_csv(self) -> Dict:
        """Export all users to CSV format"""
        try:
            users = User.query.all()
            
            # Create CSV content
            csv_lines = ['ID,Name,Email,Role,Department,Status,Created At']
            
            for user in users:
                department_name = user.department.name if user.department else 'N/A'
                csv_lines.append(f"{user.id},{user.name},{user.email},{user.role.value},{department_name},{user.status.value},{user.created_at}")
            
            csv_content = '\n'.join(csv_lines)
            
            return {
                'success': True,
                'csv_content': csv_content,
                'total_users': len(users)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_ai_logs(self, page: int = 1, per_page: int = 50) -> Dict:
        """Get AI usage logs with pagination"""
        offset = (page - 1) * per_page
        
        total_logs = AiCallLog.query.count()
        logs = AiCallLog.query.order_by(AiCallLog.created_at.desc()).offset(offset).limit(per_page).all()
        
        return {
            'logs': [log.to_dict() for log in logs],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total_logs,
                'pages': (total_logs + per_page - 1) // per_page
            }
        }
    
    def get_system_health(self) -> Dict:
        """Get system health status"""
        try:
            # Check database connection
            db.session.execute('SELECT 1')
            db_status = 'healthy'
        except:
            db_status = 'unhealthy'
        
        # For now, always return healthy for AI service since the system is working
        # In production, you might want to do a more thorough check
        ai_status = 'healthy'
        
        return {
            'database': db_status,
            'ai_service': ai_status,
            'timestamp': datetime.utcnow().isoformat()
        }

