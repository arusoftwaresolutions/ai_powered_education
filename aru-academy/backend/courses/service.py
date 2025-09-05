from models.base import db
from models.course import Course
from models.department import Department
from models.user import User, UserRole
from typing import List, Optional

class CourseService:
    """Service layer for course operations"""
    
    def get_courses_for_user(self, user: User) -> List[Course]:
        """Get courses based on user role and department"""
        if user.role == UserRole.ADMIN:
            return Course.query.all()
        elif user.role == UserRole.INSTRUCTOR:
            return Course.query.filter_by(created_by=user.id).all()
        else:  # Student
            return Course.query.filter_by(department_id=user.department_id).all()
    
    def get_course_by_id(self, course_id: int) -> Optional[Course]:
        """Get course by ID"""
        return Course.query.get(course_id)
    
    def create_course(self, user: User, course_data: dict) -> Course:
        """Create a new course"""
        try:
            # Validate department
            department = Department.query.filter_by(name=course_data['department']).first()
            if not department:
                raise ValueError('Invalid department')
            
            # Check permissions
            if user.role not in [UserRole.INSTRUCTOR, UserRole.ADMIN]:
                raise ValueError('Insufficient permissions')
            
            if user.role == UserRole.INSTRUCTOR and user.department_id != department.id:
                raise ValueError('You can only create courses in your department')
            
            # Create course
            course = Course(
                title=course_data['title'],
                description=course_data['description'],
                department_id=department.id,
                created_by=user.id
            )
            
            db.session.add(course)
            db.session.commit()
            
            return course
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    def update_course(self, user: User, course_id: int, update_data: dict) -> Course:
        """Update an existing course"""
        try:
            course = Course.query.get(course_id)
            if not course:
                raise ValueError('Course not found')
            
            # Check permissions
            if user.role == UserRole.STUDENT:
                raise ValueError('Students cannot modify courses')
            
            if user.role == UserRole.INSTRUCTOR and course.created_by != user.id:
                raise ValueError('Access denied')
            
            # Update fields
            if 'title' in update_data:
                course.title = update_data['title']
            if 'description' in update_data:
                course.description = update_data['description']
            
            db.session.commit()
            
            return course
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    def delete_course(self, user: User, course_id: int) -> bool:
        """Delete a course"""
        try:
            course = Course.query.get(course_id)
            if not course:
                raise ValueError('Course not found')
            
            # Check permissions
            if user.role == UserRole.STUDENT:
                raise ValueError('Students cannot delete courses')
            
            if user.role == UserRole.INSTRUCTOR and course.created_by != user.id:
                raise ValueError('Access denied')
            
            db.session.delete(course)
            db.session.commit()
            
            return True
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    def get_courses_by_department(self, user: User, department_id: int) -> List[Course]:
        """Get courses by department with permission check"""
        if user.role == UserRole.STUDENT and user.department_id != department_id:
            raise ValueError('Access denied')
        
        return Course.query.filter_by(department_id=department_id).all()
    
    def search_courses(self, user: User, search_term: str) -> List[Course]:
        """Search courses by title or description"""
        courses = self.get_courses_for_user(user)
        
        if not search_term:
            return courses
        
        search_term = search_term.lower()
        filtered_courses = []
        
        for course in courses:
            if (search_term in course.title.lower() or 
                search_term in course.description.lower()):
                filtered_courses.append(course)
        
        return filtered_courses

