"""
Production Configuration for AI Life Coach Application
"""
import os
import logging
import time
from datetime import timedelta

class ProductionConfig:
    """Production configuration settings"""
    
    # Flask Configuration
    SECRET_KEY = os.environ.get('SESSION_SECRET', os.urandom(32))
    DEBUG = False
    TESTING = False
    
    # Security Configuration
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # CORS Configuration
    CORS_ORIGINS = [
        'https://*.replit.app',
        'https://*.replit.dev',
        'https://*.netlify.app',
        'https://*.netlify.com'
    ]
    
    # Rate Limiting
    RATELIMIT_STORAGE_URL = "memory://"
    RATELIMIT_DEFAULT = "100 per hour"
    RATELIMIT_HEADERS_ENABLED = True
    
    # Logging Configuration
    LOG_LEVEL = logging.INFO
    LOG_FORMAT = '%(asctime)s %(levelname)s %(name)s %(message)s'
    
    # Security Headers
    SECURITY_HEADERS = {
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Content-Security-Policy': (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://cdn.replit.com; "
            "font-src 'self' https://cdnjs.cloudflare.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https://api.openai.com; "
            "frame-ancestors 'none'"
        ),
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Permissions-Policy': 'camera=(), microphone=(), geolocation=self'
    }
    
    # Performance Configuration
    SEND_FILE_MAX_AGE_DEFAULT = timedelta(days=365)  # Static file caching
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
    
    # External Services
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    OPENAI_MODEL = 'gpt-4'
    OPENAI_MAX_TOKENS = 1000
    OPENAI_TEMPERATURE = 0.7
    
    # Email Configuration (for notifications)
    SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
    SMTP_USERNAME = os.environ.get('SMTP_USERNAME')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')
    
    # File Storage
    DATA_DIRECTORY = os.environ.get('DATA_DIRECTORY', './data')
    BACKUP_DIRECTORY = os.environ.get('BACKUP_DIRECTORY', './backups')
    LOG_DIRECTORY = os.environ.get('LOG_DIRECTORY', './logs')
    
    # Health Check Configuration
    HEALTH_CHECK_TIMEOUT = 30
    HEALTH_CHECK_ENDPOINTS = [
        '/health',
        '/api/system/status'
    ]
    
    # Monitoring
    ENABLE_METRICS = True
    METRICS_ENDPOINT = '/metrics'
    ENABLE_PROFILING = False
    
    @classmethod
    def init_app(cls, app):
        """Initialize application with production configuration"""
        
        # Configure logging
        logging.basicConfig(
            level=cls.LOG_LEVEL,
            format=cls.LOG_FORMAT
        )
        
        # Ensure directories exist
        for directory in [cls.DATA_DIRECTORY, cls.BACKUP_DIRECTORY, cls.LOG_DIRECTORY]:
            os.makedirs(directory, exist_ok=True)
        
        # Configure security headers
        @app.after_request
        def add_security_headers(response):
            for header, value in cls.SECURITY_HEADERS.items():
                response.headers[header] = value
            return response
        
        # Configure error handling
        @app.errorhandler(404)
        def not_found_error(error):
            return {'error': 'Resource not found'}, 404
        
        @app.errorhandler(500)
        def internal_error(error):
            return {'error': 'Internal server error'}, 500
        
        @app.errorhandler(429)
        def ratelimit_handler(e):
            return {'error': 'Rate limit exceeded'}, 429
        
        # Health check endpoint
        @app.route('/health')
        def health_check():
            return {
                'status': 'healthy',
                'version': '1.0.0',
                'timestamp': time.time()
            }

class DevelopmentConfig:
    """Development configuration settings"""
    
    DEBUG = True
    TESTING = False
    SECRET_KEY = 'dev-secret-key'
    SESSION_COOKIE_SECURE = False
    LOG_LEVEL = logging.DEBUG

class TestingConfig:
    """Testing configuration settings"""
    
    DEBUG = False
    TESTING = True
    SECRET_KEY = 'test-secret-key'
    WTF_CSRF_ENABLED = False

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': ProductionConfig
}