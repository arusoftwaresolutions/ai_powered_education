from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
import os
import uuid
from werkzeug.utils import secure_filename
from datetime import datetime

from .service import ResourceService
from models.base import db
from models.user import User, UserRole
from models.resource import Resource, ResourceType
from models.course import Course
from models.progress import Progress, ProgressStatus

resources_bp = Blueprint('resources', __name__)
resource_service = ResourceService()

def allowed_file(filename):
    """Check if file type is allowed"""
    ALLOWED_EXTENSIONS = {
        # Documents
        'pdf', 'txt', 'doc', 'docx', 'rtf',
        # Presentations
        'ppt', 'pptx', 'odp',
        # Spreadsheets
        'xls', 'xlsx', 'csv', 'ods',
        # Images
        'jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp',
        # Videos
        'mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv',
        # Audio
        'mp3', 'wav', 'ogg', 'aac', 'flac',
        # Archives
        'zip', 'rar', '7z', 'tar', 'gz',
        # Code files
        'js', 'py', 'html', 'css', 'java', 'cpp', 'c', 'php', 'rb', 'go', 'rs',
        'json', 'xml', 'yaml', 'yml', 'md', 'sql'
    }
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_resource_type_from_extension(filename):
    """Determine resource type from file extension"""
    if not filename or '.' not in filename:
        return ResourceType.TEXT
    
    file_ext = filename.rsplit('.', 1)[1].lower()
    
    # Document types
    if file_ext in ['pdf']:
        return ResourceType.PDF
    elif file_ext in ['doc', 'docx', 'rtf']:
        return ResourceType.DOCUMENT
    elif file_ext in ['ppt', 'pptx', 'odp']:
        return ResourceType.PRESENTATION
    elif file_ext in ['xls', 'xlsx', 'csv', 'ods']:
        return ResourceType.SPREADSHEET
    elif file_ext in ['txt', 'md']:
        return ResourceType.TEXT
    
    # Media types
    elif file_ext in ['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv']:
        return ResourceType.VIDEO
    elif file_ext in ['mp3', 'wav', 'ogg', 'aac', 'flac']:
        return ResourceType.AUDIO
    elif file_ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp']:
        return ResourceType.IMAGE
    
    # Archive types
    elif file_ext in ['zip', 'rar', '7z', 'tar', 'gz']:
        return ResourceType.ARCHIVE
    
    # Code types
    elif file_ext in ['js', 'py', 'html', 'css', 'java', 'cpp', 'c', 'php', 'rb', 'go', 'rs', 'json', 'xml', 'yaml', 'yml', 'sql']:
        return ResourceType.CODE
    
    # Default fallback
    else:
        return ResourceType.TEXT

@resources_bp.route('/', methods=['GET'])
@jwt_required()
def get_resources():
    """Get resources based on user role and department"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(int(user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        course_id = request.args.get('course_id', type=int)
        
        if course_id:
            # Get resources for specific course
            resources = resource_service.get_resources_by_course(user, course_id)
        else:
            # Get all accessible resources
            resources = resource_service.get_resources_for_user(user)
        
        return jsonify({
            'resources': [resource.to_dict() for resource in resources]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@resources_bp.route('/<int:resource_id>', methods=['GET'])
@jwt_required()
def get_resource(resource_id):
    """Get a specific resource"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(int(user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        resource = resource_service.get_resource_by_id(user, resource_id)
        if not resource:
            return jsonify({'error': 'Resource not found'}), 404
        
        # Update progress if student
        if user.role == UserRole.STUDENT:
            resource_service.update_progress(user.id, resource_id)
        
        return jsonify({
            'resource': resource.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@resources_bp.route('/', methods=['POST'])
@jwt_required()
def create_resource():
    """Create a new resource (instructors and admins only)"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(int(user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if user.role not in [UserRole.INSTRUCTOR, UserRole.ADMIN]:
            return jsonify({'error': 'Only instructors and admins can create resources'}), 403
        
        # Check if it's a file upload or text resource
        if 'file' in request.files:
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            if not allowed_file(file.filename):
                return jsonify({'error': 'File type not allowed'}), 400
            
            # Get course info
            course_id = request.form.get('course_id')
            if not course_id:
                return jsonify({'error': 'Course ID is required'}), 400
            
            course = Course.query.get(course_id)
            if not course:
                return jsonify({'error': 'Course not found'}), 400
            
            # Check permissions
            if user.role == UserRole.INSTRUCTOR and course.created_by != user_id:
                return jsonify({'error': 'Access denied to this course'}), 403
            
            # Save file
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"
            
            # Create department folder if it doesn't exist
            dept_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], course.department.name.lower().replace(' ', '_'))
            os.makedirs(dept_folder, exist_ok=True)
            
            file_path = os.path.join(dept_folder, unique_filename)
            file.save(file_path)
            
            # Determine resource type from file extension
            resource_type = get_resource_type_from_extension(filename)
            
            resource = Resource(
                title=request.form.get('title', filename),
                type=resource_type,
                course_id=course_id,
                file_path_or_url=file_path,
                description=request.form.get('description', '')
            )
            
        else:
            # Text resource
            data = request.get_json()
            if not all(key in data for key in ['title', 'course_id', 'text_content']):
                return jsonify({'error': 'Title, course_id, and text_content are required'}), 400
            
            course = Course.query.get(data['course_id'])
            if not course:
                return jsonify({'error': 'Course not found'}), 400
            
            # Check permissions
            if user.role == UserRole.INSTRUCTOR and course.created_by != user_id:
                return jsonify({'error': 'Access denied to this course'}), 403
            
            resource = Resource(
                title=data['title'],
                type=ResourceType.TEXT,
                course_id=data['course_id'],
                text_content=data['text_content'],
                description=data.get('description', '')
            )
        
        db.session.add(resource)
        db.session.commit()
        
        return jsonify({
            'message': 'Resource created successfully',
            'resource': resource.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@resources_bp.route('/<int:resource_id>', methods=['PUT'])
@jwt_required()
def update_resource(resource_id):
    """Update a resource (creator or admin only)"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(int(user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        resource = Resource.query.get(resource_id)
        if not resource:
            return jsonify({'error': 'Resource not found'}), 404
        
        # Check permissions
        if user.role == UserRole.STUDENT:
            return jsonify({'error': 'Students cannot modify resources'}), 403
        
        course = Course.query.get(resource.course_id)
        if user.role == UserRole.INSTRUCTOR and course.created_by != user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        data = request.get_json()
        
        # Update allowed fields
        if 'title' in data:
            resource.title = data['title']
        if 'description' in data:
            resource.description = data['description']
        if 'text_content' in data and resource.type == ResourceType.TEXT:
            resource.text_content = data['text_content']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Resource updated successfully',
            'resource': resource.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@resources_bp.route('/<int:resource_id>', methods=['DELETE'])
@jwt_required()
def delete_resource(resource_id):
    """Delete a resource (creator or admin only)"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(int(user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        resource = Resource.query.get(resource_id)
        if not resource:
            return jsonify({'error': 'Resource not found'}), 404
        
        # Check permissions
        if user.role == UserRole.STUDENT:
            return jsonify({'error': 'Students cannot delete resources'}), 403
        
        course = Course.query.get(resource.course_id)
        if user.role == UserRole.INSTRUCTOR and course.created_by != user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        # Delete file if it exists
        if resource.file_path_or_url and os.path.exists(resource.file_path_or_url):
            os.remove(resource.file_path_or_url)
        
        db.session.delete(resource)
        db.session.commit()
        
        return jsonify({
            'message': 'Resource deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@resources_bp.route('/<int:resource_id>/progress', methods=['POST'])
@jwt_required()
def update_progress(resource_id):
    """Update student progress on a resource"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(int(user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if user.role != UserRole.STUDENT:
            return jsonify({'error': 'Only students can update progress'}), 403
        
        data = request.get_json()
        status = data.get('status')
        completion_percentage = data.get('completion_percentage', 0)
        
        if status not in ['not_started', 'in_progress', 'completed']:
            return jsonify({'error': 'Invalid status'}), 400
        
        progress = resource_service.update_progress(
            user_id, 
            resource_id, 
            status, 
            completion_percentage
        )
        
        return jsonify({
            'message': 'Progress updated successfully',
            'progress': progress.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@resources_bp.route('/<int:resource_id>/view', methods=['GET'])
@jwt_required()
def view_resource(resource_id):
    """View a resource file (for file viewer)"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(int(user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        resource = resource_service.get_resource_by_id(user, resource_id)
        if not resource:
            return jsonify({'error': 'Resource not found'}), 404
        
        # Update progress if student
        if user.role == UserRole.STUDENT:
            resource_service.update_progress(user.id, resource_id, 'in_progress', 50)
        
        # Handle different resource types
        if resource.type.value == 'text':
            # For text resources, return the text content
            from flask import Response
            return Response(resource.text_content or 'No content available', 
                          mimetype='text/plain', 
                          headers={'Content-Disposition': f'inline; filename="{resource.title}.txt"'})
        else:
            # For file-based resources (PDF, VIDEO, DOCUMENT, etc.)
            if not resource.file_path_or_url or not os.path.exists(resource.file_path_or_url):
                return jsonify({'error': 'File not found'}), 404
            
            # Return file content with appropriate MIME type
            from flask import send_file
            return send_file(resource.file_path_or_url, as_attachment=False)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@resources_bp.route('/<int:resource_id>/download', methods=['GET'])
@jwt_required()
def download_resource(resource_id):
    """Download a resource file"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(int(user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        resource = resource_service.get_resource_by_id(user, resource_id)
        if not resource:
            return jsonify({'error': 'Resource not found'}), 404
        
        # Update progress if student
        if user.role == UserRole.STUDENT:
            resource_service.update_progress(user.id, resource_id, 'completed', 100)
        
        # Handle different resource types
        if resource.type.value == 'text':
            # For text resources, return the text content as a downloadable file
            from flask import Response
            return Response(resource.text_content or 'No content available', 
                          mimetype='text/plain', 
                          headers={'Content-Disposition': f'attachment; filename="{resource.title}.txt"'})
        else:
            # For file-based resources (PDF, VIDEO, etc.)
            if not resource.file_path_or_url or not os.path.exists(resource.file_path_or_url):
                return jsonify({'error': 'File not found'}), 404
            
            # Return file for download
            from flask import send_file
            return send_file(resource.file_path_or_url, as_attachment=True, download_name=resource.title)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

