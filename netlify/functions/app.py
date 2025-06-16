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

# Import the Flask app
from app import app
from production_config import ProductionConfig

# Configure for Netlify
app.config.from_object(ProductionConfig)
ProductionConfig.init_app(app)

def handler(event, context):
    """
    Netlify function handler for Flask application
    """
    try:
        # Extract request details from Netlify event
        path = event.get('path', '/')
        method = event.get('httpMethod', 'GET')
        headers = event.get('headers', {})
        query_params = event.get('queryStringParameters') or {}
        body = event.get('body', '')
        
        # Create Flask test client
        with app.test_client() as client:
            # Prepare request data
            request_kwargs = {
                'method': method,
                'path': path,
                'headers': headers,
                'query_string': query_params
            }
            
            if body and method in ['POST', 'PUT', 'PATCH']:
                if headers.get('content-type', '').startswith('application/json'):
                    request_kwargs['json'] = json.loads(body)
                else:
                    request_kwargs['data'] = body
            
            # Make request to Flask app
            response = client.open(**request_kwargs)
            
            # Prepare Netlify response
            return {
                'statusCode': response.status_code,
                'headers': dict(response.headers),
                'body': response.get_data(as_text=True),
                'isBase64Encoded': False
            }
            
    except Exception as e:
        # Error handling
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            }),
            'isBase64Encoded': False
        }

# For local testing
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)