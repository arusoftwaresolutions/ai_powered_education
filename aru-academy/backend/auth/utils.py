import re
from typing import Tuple

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password: str) -> bool:
    """Validate password strength"""
    if len(password) < 8:
        return False
    
    if not re.search(r'[a-zA-Z]', password):
        return False
    
    if not re.search(r'\d', password):
        return False
    
    return True

def sanitize_input(text: str) -> str:
    """Sanitize user input to prevent XSS"""
    if not text:
        return ""
    
    # Remove potentially dangerous characters
    dangerous_chars = ['<', '>', '"', "'", '&', ';']
    for char in dangerous_chars:
        text = text.replace(char, '')
    
    return text.strip()

def validate_role(role: str) -> bool:
    """Validate user role"""
    valid_roles = ['student', 'instructor', 'admin']
    return role.lower() in valid_roles

def validate_department(department: str) -> bool:
    """Validate department name"""
    valid_departments = [
        'Computer Science',
        'Electrical Engineering', 
        'Mechanical Engineering',
        'Business Administration'
    ]
    return department in valid_departments

