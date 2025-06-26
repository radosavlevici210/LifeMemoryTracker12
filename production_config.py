"""
Production Configuration and Optimization
"""
import os
import logging
from datetime import datetime

class ProductionConfig:
    """Production configuration settings"""
    
    # Security Settings
    SECRET_KEY = os.environ.get('SESSION_SECRET')
    DATABASE_URL = os.environ.get('DATABASE_URL')
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    
    # Performance Settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file upload
    SEND_FILE_MAX_AGE_DEFAULT = 31536000  # 1 year cache for static files
    
    # Database Settings
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 300,
        'pool_pre_ping': True,
        'pool_timeout': 30,
        'max_overflow': 20
    }
    
    # Rate Limiting
    RATELIMIT_STORAGE_URL = "memory://"
    RATELIMIT_DEFAULT = "100 per hour"
    
    # Logging Configuration
    LOG_LEVEL = logging.INFO
    LOG_FORMAT = '%(asctime)s %(levelname)s %(name)s %(message)s'
    
    # API Settings
    API_TIMEOUT = 30
    MAX_RETRIES = 3
    
    # Feature Flags
    ENABLE_ANALYTICS = True
    ENABLE_GAMIFICATION = True
    ENABLE_VOICE_INTERACTION = True
    ENABLE_RECOMMENDATIONS = True
    ENABLE_PERSONALITY_ENGINE = True
    
    # Health Check Settings
    HEALTH_CHECK_INTERVAL = 60  # seconds
    
    @staticmethod
    def configure_logging():
        """Configure production logging"""
        logging.basicConfig(
            level=ProductionConfig.LOG_LEVEL,
            format=ProductionConfig.LOG_FORMAT,
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('app.log')
            ]
        )
        
        # Reduce noise from external libraries
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('requests').setLevel(logging.WARNING)
        logging.getLogger('werkzeug').setLevel(logging.WARNING)
    
    @staticmethod
    def validate_environment():
        """Validate required environment variables"""
        required_vars = ['SESSION_SECRET', 'DATABASE_URL', 'OPENAI_API_KEY']
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        
        if missing_vars:
            raise EnvironmentError(f"Missing required environment variables: {missing_vars}")
        
        return True
    
    @staticmethod
    def get_version_info():
        """Get application version information"""
        return {
            "version": "2.0.0",
            "build_date": datetime.now().isoformat(),
            "environment": "production",
            "features": {
                "ai_chat": True,
                "gamification": ProductionConfig.ENABLE_GAMIFICATION,
                "recommendations": ProductionConfig.ENABLE_RECOMMENDATIONS,
                "voice_interaction": ProductionConfig.ENABLE_VOICE_INTERACTION,
                "personality_engine": ProductionConfig.ENABLE_PERSONALITY_ENGINE,
                "analytics": ProductionConfig.ENABLE_ANALYTICS
            }
        }