from models.base import db
from models.resource import Resource, ResourceType
from models.user import User, UserRole
from models.course import Course
from models.progress import Progress, ProgressStatus
from typing import List, Optional
from datetime import datetime

class ResourceService:
    """Service layer for resource operations"""
    
    def get_resources_for_user(self, user: User) -> List[Resource]:
        """Get resources based on user role and department"""
        if user.role == UserRole.ADMIN:
            return Resource.query.all()
        elif user.role == UserRole.INSTRUCTOR:
            # Get resources from courses created by the instructor
            course_ids = [course.id for course in user.courses_created]
            return Resource.query.filter(Resource.course_id.in_(course_ids)).all()
        else:  # Student
            # Get resources from user's department
            return Resource.query.join(Course).filter(Course.department_id == user.department_id).all()
    
    def get_resources_by_course(self, user: User, course_id: int) -> List[Resource]:
        """Get resources for a specific course with permission check"""
        course = Course.query.get(course_id)
        if not course:
            raise ValueError('Course not found')
        
        # Check access permissions
        if user.role == UserRole.STUDENT and course.department_id != user.department_id:
            raise ValueError('Access denied to this course')
        
        if user.role == UserRole.INSTRUCTOR and course.created_by != user.id:
            raise ValueError('Access denied to this course')
        
        return Resource.query.filter_by(course_id=course_id).all()
    
    def get_resource_by_id(self, user: User, resource_id: int) -> Optional[Resource]:
        """Get a specific resource with permission check"""
        resource = Resource.query.get(resource_id)
        if not resource:
            return None
        
        course = Course.query.get(resource.course_id)
        if not course:
            return None
        
        # Check access permissions
        if user.role == UserRole.STUDENT and course.department_id != user.department_id:
            raise ValueError('Access denied to this resource')
        
        if user.role == UserRole.INSTRUCTOR and course.created_by != user.id:
            raise ValueError('Access denied to this resource')
        
        return resource
    
    def create_resource(self, user: User, resource_data: dict) -> Resource:
        """Create a new resource"""
        try:
            # Validate course exists and user has access
            course = Course.query.get(resource_data['course_id'])
            if not course:
                raise ValueError('Course not found')
            
            if user.role == UserRole.INSTRUCTOR and course.created_by != user.id:
                raise ValueError('Access denied to this course')
            
            # Create resource
            resource = Resource(
                title=resource_data['title'],
                type=ResourceType(resource_data['type']),
                course_id=resource_data['course_id'],
                file_path_or_url=resource_data.get('file_path_or_url'),
                text_content=resource_data.get('text_content'),
                description=resource_data.get('description', '')
            )
            
            db.session.add(resource)
            db.session.commit()
            
            return resource
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    def update_resource(self, user: User, resource_id: int, update_data: dict) -> Resource:
        """Update an existing resource"""
        try:
            resource = Resource.query.get(resource_id)
            if not resource:
                raise ValueError('Resource not found')
            
            course = Course.query.get(resource.course_id)
            if not course:
                raise ValueError('Course not found')
            
            # Check permissions
            if user.role == UserRole.STUDENT:
                raise ValueError('Students cannot modify resources')
            
            if user.role == UserRole.INSTRUCTOR and course.created_by != user.id:
                raise ValueError('Access denied')
            
            # Update fields
            if 'title' in update_data:
                resource.title = update_data['title']
            if 'description' in update_data:
                resource.description = update_data['description']
            if 'text_content' in update_data and resource.type == ResourceType.TEXT:
                resource.text_content = update_data['text_content']
            
            db.session.commit()
            
            return resource
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    def delete_resource(self, user: User, resource_id: int) -> bool:
        """Delete a resource"""
        try:
            resource = Resource.query.get(resource_id)
            if not resource:
                raise ValueError('Resource not found')
            
            course = Course.query.get(resource.course_id)
            if not course:
                raise ValueError('Course not found')
            
            # Check permissions
            if user.role == UserRole.STUDENT:
                raise ValueError('Students cannot delete resources')
            
            if user.role == UserRole.INSTRUCTOR and course.created_by != user.id:
                raise ValueError('Access denied')
            
            db.session.delete(resource)
            db.session.commit()
            
            return True
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    def update_progress(self, user_id: int, resource_id: int, status: str = None, completion_percentage: float = None) -> Progress:
        """Update or create progress record for a resource"""
        try:
            # Get existing progress or create new one
            progress = Progress.query.filter_by(
                user_id=user_id,
                resource_id=resource_id
            ).first()
            
            if not progress:
                progress = Progress(
                    user_id=user_id,
                    resource_id=resource_id,
                    status=ProgressStatus.IN_PROGRESS,
                    completion_percentage=0
                )
                db.session.add(progress)
            
            # Update progress
            if status:
                progress.status = ProgressStatus(status)
            if completion_percentage is not None:
                progress.completion_percentage = completion_percentage
            
            progress.last_accessed_at = datetime.utcnow()
            
            db.session.commit()
            
            return progress
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    def get_user_progress(self, user_id: int) -> List[Progress]:
        """Get all progress records for a user"""
        return Progress.query.filter_by(user_id=user_id).all()
    
    def get_resource_progress(self, resource_id: int) -> List[Progress]:
        """Get all progress records for a resource"""
        return Progress.query.filter_by(resource_id=resource_id).all()

