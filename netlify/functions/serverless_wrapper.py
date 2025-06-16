
"""
Optimized serverless WSGI wrapper for Netlify functions
"""
import json
import base64
from urllib.parse import unquote_plus
from io import StringIO
import sys

class ServerlessWSGIHandler:
    """Optimized WSGI handler for serverless environments"""
    
    def __init__(self, app, timeout=30):
        self.app = app
        self.timeout = timeout
    
    def __call__(self, event, context):
        """Handle serverless function invocation"""
        try:
            # Parse the event
            method = event.get('httpMethod', 'GET')
            path = event.get('path', '/')
            query_string = event.get('queryStringParameters') or {}
            headers = event.get('headers') or {}
            body = event.get('body', '')
            is_base64 = event.get('isBase64Encoded', False)
            
            # Decode body if base64 encoded
            if is_base64 and body:
                body = base64.b64decode(body).decode('utf-8')
            
            # Build query string
            query_params = []
            for key, value in query_string.items():
                if value:
                    query_params.append(f"{key}={unquote_plus(str(value))}")
            query_string_formatted = '&'.join(query_params)
            
            # Build WSGI environ
            environ = {
                'REQUEST_METHOD': method,
                'SCRIPT_NAME': '',
                'PATH_INFO': path,
                'QUERY_STRING': query_string_formatted,
                'CONTENT_TYPE': headers.get('content-type', ''),
                'CONTENT_LENGTH': str(len(body)) if body else '0',
                'SERVER_NAME': headers.get('host', 'localhost').split(':')[0],
                'SERVER_PORT': '80',
                'SERVER_PROTOCOL': 'HTTP/1.1',
                'wsgi.version': (1, 0),
                'wsgi.url_scheme': 'https',
                'wsgi.input': StringIO(body),
                'wsgi.errors': sys.stderr,
                'wsgi.multithread': False,
                'wsgi.multiprocess': True,
                'wsgi.run_once': False,
            }
            
            # Add headers to environ
            for key, value in headers.items():
                key = key.upper().replace('-', '_')
                if key not in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
                    environ[f'HTTP_{key}'] = value
            
            # Capture response
            response = {'statusCode': 200, 'headers': {}, 'body': ''}
            
            def start_response(status, response_headers, exc_info=None):
                response['statusCode'] = int(status.split(' ', 1)[0])
                for header in response_headers:
                    response['headers'][header[0]] = header[1]
            
            # Call the WSGI app
            result = self.app(environ, start_response)
            
            # Build response body
            response_body = b''.join(result).decode('utf-8')
            response['body'] = response_body
            
            # Set default headers
            if 'Content-Type' not in response['headers']:
                response['headers']['Content-Type'] = 'application/json'
            
            # Add CORS headers for web compatibility
            response['headers']['Access-Control-Allow-Origin'] = '*'
            response['headers']['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
            response['headers']['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            
            return response
            
        except Exception as e:
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': f'Internal server error: {str(e)}'})
            }
