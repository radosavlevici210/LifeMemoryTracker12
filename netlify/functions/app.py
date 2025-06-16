"""
Netlify serverless function for AI Life Coach application
"""
import json
import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import our app
current_dir = Path(__file__).parent
parent_dir = current_dir.parent.parent
sys.path.insert(0, str(parent_dir))

# Set environment variables for Netlify
os.environ.setdefault('FLASK_ENV', 'production')
os.environ.setdefault('DATABASE_URL', 'sqlite:///ai_coach.db')

# Import the Flask app
from app import app
from production_config import ProductionConfig

# Configure for Netlify
app.config.from_object(ProductionConfig)
ProductionConfig.init_app(app)

# Optimize for serverless
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
    'connect_args': {'check_same_thread': False}
}

# Import the optimized serverless wrapper
from serverless_wrapper import ServerlessWSGIHandler

# Create the serverless handler
handler = ServerlessWSGIHandler(app)

# For local testing
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)