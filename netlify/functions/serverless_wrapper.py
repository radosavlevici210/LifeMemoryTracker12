
"""
Optimized serverless wrapper for Netlify functions
"""
import json
import logging
from werkzeug.wrappers import Response
from werkzeug.serving import WSGIRequestHandler

# Configure logging for serverless
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ServerlessWSGIHandler:
    """Custom WSGI handler optimized for serverless environments"""
    
    def __init__(self, app):
        self.app = app
    
    def __call__(self, event, context):
        """Handle Netlify function calls"""
        try:
            # Parse the request
            path = event.get('path', '/')
            method = event.get('httpMethod', 'GET')
            headers = event.get('headers', {})
            query_params = event.get('queryStringParameters') or {}
            body = event.get('body', '')
            
            # Create environ dict for WSGI
            environ = {
                'REQUEST_METHOD': method,
                'PATH_INFO': path,
                'QUERY_STRING': '&'.join([f'{k}={v}' for k, v in query_params.items()]),
                'CONTENT_TYPE': headers.get('content-type', ''),
                'CONTENT_LENGTH': str(len(body)) if body else '0',
                'SERVER_NAME': headers.get('host', 'localhost'),
                'SERVER_PORT': '443',
                'wsgi.version': (1, 0),
                'wsgi.url_scheme': 'https',
                'wsgi.input': None,
                'wsgi.errors': None,
                'wsgi.multithread': False,
                'wsgi.multiprocess': True,
                'wsgi.run_once': True,
            }
            
            # Add headers to environ
            for key, value in headers.items():
                key = key.upper().replace('-', '_')
                if key not in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
                    key = 'HTTP_' + key
                environ[key] = value
            
            # Handle body
            if body:
                environ['wsgi.input'] = body.encode('utf-8') if isinstance(body, str) else body
            
            # Collect response
            response_data = []
            status = None
            response_headers = []
            
            def start_response(status_code, headers):
                nonlocal status, response_headers
                status = status_code
                response_headers = headers
            
            # Call the WSGI application
            app_iter = self.app(environ, start_response)
            
            try:
                for data in app_iter:
                    if data:
                        response_data.append(data)
            finally:
                if hasattr(app_iter, 'close'):
                    app_iter.close()
            
            # Build response
            response_body = b''.join(response_data).decode('utf-8')
            status_code = int(status.split()[0])
            
            return {
                'statusCode': status_code,
                'headers': dict(response_headers),
                'body': response_body,
                'isBase64Encoded': False
            }
            
        except Exception as e:
            logger.error(f"Serverless function error: {str(e)}")
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': 'Internal server error',
                    'message': str(e)
                }),
                'isBase64Encoded': False
            }
