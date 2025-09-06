"""
Health checker for ARU Academy
"""

import psutil
import time
import requests
from datetime import datetime, timedelta
from models.base import db
from models.user import User
from models.ai_log import AiCallLog
from config.settings import Config
import logging

logger = logging.getLogger(__name__)

class HealthChecker:
    """Health checker for system monitoring"""
    
    def __init__(self):
        self.config = Config()
        self.start_time = datetime.now()
    
    def check_basic_health(self):
        """Basic health check"""
        return {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'uptime': str(datetime.now() - self.start_time),
            'version': '1.0.0'
        }
    
    def check_detailed_health(self):
        """Detailed health check"""
        return {
            'basic': self.check_basic_health(),
            'database': self.check_database_health(),
            'ai': self.check_ai_health(),
            'system': self.check_system_health()
        }
    
    def check_database_health(self):
        """Check database connectivity and performance"""
        try:
            start_time = time.time()
            
            # Clear any existing transactions and start fresh
            db.session.rollback()
            
            # Test database connection
            db.session.execute('SELECT 1')
            db.session.commit()
            response_time = time.time() - start_time
            
            # Get comprehensive stats with fresh session
            from models.department import Department
            from models.course import Course
            from models.resource import Resource
            from models.approved_user import ApprovedUser
            
            # Use individual try-catch for each query to avoid cascading failures
            try:
                user_count = User.query.count()
            except Exception:
                user_count = 0
                
            try:
                dept_count = Department.query.count()
            except Exception:
                dept_count = 0
                
            try:
                course_count = Course.query.count()
            except Exception:
                course_count = 0
                
            try:
                resource_count = Resource.query.count()
            except Exception:
                resource_count = 0
                
            try:
                approved_user_count = ApprovedUser.query.count()
            except Exception:
                approved_user_count = 0
            
            # Determine seeding status
            seeding_status = 'completed' if dept_count > 0 and course_count > 0 else 'pending'
            
            return {
                'status': 'healthy',
                'response_time': round(response_time * 1000, 2),  # ms
                'seeding_status': seeding_status,
                'counts': {
                    'users': user_count,
                    'departments': dept_count,
                    'courses': course_count,
                    'resources': resource_count,
                    'approved_users': approved_user_count
                },
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            db.session.rollback()  # Ensure clean state
            return {
                'status': 'unhealthy',
                'error': str(e),
                'seeding_status': 'failed',
                'timestamp': datetime.now().isoformat()
            }
    
    def check_ai_health(self):
        """Check AI service health"""
        try:
            # Check if Hugging Face API is accessible
            if not hasattr(self.config, 'HF_API_TOKEN') or not self.config.HF_API_TOKEN:
                return {
                    'status': 'degraded',
                    'error': 'HF API token not configured',
                    'timestamp': datetime.now().isoformat()
                }
            
            headers = {
                'Authorization': f'Bearer {self.config.HF_API_TOKEN}',
                'Content-Type': 'application/json'
            }
            
            # Simple test request
            test_data = {
                'inputs': 'Hello, how are you?',
                'parameters': {
                    'max_length': 50,
                    'temperature': 0.7
                }
            }
            
            start_time = time.time()
            response = requests.post(
                self.config.HF_API_URL,
                headers=headers,
                json=test_data,
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                return {
                    'status': 'healthy',
                    'response_time': round(response_time * 1000, 2),  # ms
                    'api_status': 'accessible',
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'degraded',
                    'api_status': f'HTTP {response.status_code}',
                    'response_time': round(response_time * 1000, 2),
                    'timestamp': datetime.now().isoformat()
                }
                
        except requests.exceptions.Timeout:
            return {
                'status': 'unhealthy',
                'error': 'AI API timeout',
                'timestamp': datetime.now().isoformat()
            }
        except requests.exceptions.RequestException as e:
            return {
                'status': 'unhealthy',
                'error': f'AI API error: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"AI health check failed: {str(e)}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def check_system_health(self):
        """Check system resources"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            # Network stats
            network = psutil.net_io_counters()
            
            return {
                'status': 'healthy',
                'cpu_percent': cpu_percent,
                'memory': {
                    'total_gb': round(memory.total / (1024**3), 2),
                    'available_gb': round(memory.available / (1024**3), 2),
                    'percent': memory.percent
                },
                'disk': {
                    'total_gb': round(disk.total / (1024**3), 2),
                    'free_gb': round(disk.free / (1024**3), 2),
                    'percent': round((disk.used / disk.total) * 100, 2)
                },
                'network': {
                    'bytes_sent_mb': round(network.bytes_sent / (1024**2), 2),
                    'bytes_recv_mb': round(network.bytes_recv / (1024**2), 2)
                },
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"System health check failed: {str(e)}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_health_metrics(self):
        """Get health metrics for monitoring"""
        try:
            # Get recent AI calls
            recent_ai_calls = AiCallLog.query.filter(
                AiCallLog.created_at >= datetime.now() - timedelta(hours=24)
            ).count()
            
            # Get successful AI calls
            successful_ai_calls = AiCallLog.query.filter(
                AiCallLog.created_at >= datetime.now() - timedelta(hours=24),
                AiCallLog.success == True
            ).count()
            
            # Calculate success rate
            success_rate = (successful_ai_calls / recent_ai_calls * 100) if recent_ai_calls > 0 else 0
            
            return {
                'ai_calls_24h': recent_ai_calls,
                'ai_success_rate': round(success_rate, 2),
                'system_uptime': str(datetime.now() - self.start_time),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Health metrics failed: {str(e)}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_overall_status(self):
        """Get overall system status"""
        try:
            db_status = self.check_database_health()
            ai_status = self.check_ai_health()
            system_status = self.check_system_health()
            
            # Determine overall status
            if all(status['status'] == 'healthy' for status in [db_status, ai_status, system_status]):
                overall_status = 'healthy'
            elif any(status['status'] == 'unhealthy' for status in [db_status, ai_status, system_status]):
                overall_status = 'unhealthy'
            else:
                overall_status = 'degraded'
            
            return {
                'overall_status': overall_status,
                'components': {
                    'database': db_status,
                    'ai': ai_status,
                    'system': system_status
                },
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Overall status failed: {str(e)}")
            return {
                'overall_status': 'unknown',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
