import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    
    # Database settings - Use SQLite for local development, MySQL for production
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL') or (
        f"mysql+pymysql://{os.getenv('MYSQL_USER', 'aru_user')}:"
        f"{os.getenv('MYSQL_PASSWORD', 'aru_password')}@"
        f"{os.getenv('MYSQL_HOST', 'localhost')}:"
        f"{os.getenv('MYSQL_PORT', '3306')}/"
        f"{os.getenv('MYSQL_DB', 'aru_academy')}"
        if os.getenv('MYSQL_HOST') else 'sqlite:///aru_academy.db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 180,  # Recycle connections every 3 minutes
        'pool_timeout': 10,   # Reduced timeout
        'pool_size': 5,       # Reduced pool size
        'max_overflow': 10,   # Reduced overflow
        'pool_reset_on_return': 'commit',
        'connect_args': {
            'connect_timeout': 10,
            'read_timeout': 10,
            'write_timeout': 10,
            'autocommit': True
        }
    }
    
    # JWT settings - Use headers only for cross-domain compatibility
    JWT_TOKEN_LOCATION = ['headers']  # Remove cookies for cross-domain
    JWT_COOKIE_SECURE = False  # Not using cookies
    JWT_COOKIE_CSRF_PROTECT = False  # Not using cookies
    JWT_ACCESS_TOKEN_EXPIRES = False  # No expiration for development
    
    # CORS settings - Allow all origins for cross-domain compatibility
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
    
    # File upload settings
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_UPLOAD_MB', 25)) * 1024 * 1024
    UPLOAD_FOLDER = 'storage/departments'
    
    # Hugging Face settings
    HF_API_URL = os.getenv('HF_API_URL', 'https://api-inference.huggingface.co/models/distilgpt2')
    HF_API_TOKEN = os.getenv('HF_API_TOKEN')
    
    # Rate limiting
    RATE_LIMIT_PER_MIN = int(os.getenv('RATE_LIMIT_PER_MIN', 60))

class DevelopmentConfig(Config):
    DEBUG = True
    FLASK_ENV = 'development'

class ProductionConfig(Config):
    DEBUG = False
    FLASK_ENV = 'production'
    JWT_COOKIE_SECURE = True

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

