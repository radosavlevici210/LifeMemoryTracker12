"""
The chat function is updated to use a supported model for an older OpenAI API to resolve the installation failure.
"""
"""
Optimized Netlify serverless function for AI Life Coach application
"""
import json
import os
import sys
from pathlib import Path

# Optimize imports and minimize startup time
try:
    # Add the parent directory to the path
    current_dir = Path(__file__).parent
    parent_dir = current_dir.parent.parent
    sys.path.insert(0, str(parent_dir))

    # Set environment variables for Netlify
    os.environ.setdefault('FLASK_ENV', 'production')
    os.environ.setdefault('DATABASE_URL', 'sqlite:///ai_coach.db')

    # Import only what's needed to reduce cold start time
    from flask import Flask
    from werkzeug.middleware.proxy_fix import ProxyFix

    # Create minimal Flask app for serverless
    app = Flask(__name__)
    app.secret_key = os.environ.get("SESSION_SECRET", "netlify-production-key")
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # Lazy load heavy dependencies
    _openai_client = None
    _memory_cache = {}

    def get_openai_client():
        global _openai_client
        if _openai_client is None:
            from openai import OpenAI
            _openai_client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        return _openai_client

    def load_memory_optimized():
        """Optimized memory loading with caching"""
        if 'memory' not in _memory_cache:
            _memory_cache['memory'] = {
                "life_events": [],
                "goals": [],
                "warnings": [],
                "mood_history": [],
                "achievements": [],
                "action_items": [],
                "habits": [],
                "reflections": [],
                "milestones": []
            }
        return _memory_cache['memory']

    @app.route('/')
    def index():
        return {
            "status": "healthy",
            "service": "AI Life Coach",
            "version": "1.0.0-netlify"
        }

    @app.route('/health')
    def health():
        return {
            "status": "healthy",
            "timestamp": "2025-06-16T19:01:10Z",
            "platform": "netlify"
        }

    @app.route('/chat', methods=['POST'])
    def chat():
        """Optimized chat endpoint"""
        from flask import request, jsonify
        import datetime

        try:
            data = request.get_json()
            if not data or "message" not in data:
                return jsonify({"error": "Invalid request"}), 400

            user_input = data.get("message", "").strip()
            if not user_input:
                return jsonify({"error": "Message cannot be empty"}), 400

            # Get OpenAI client lazily
            openai_client = get_openai_client()
            if not openai_client:
                return jsonify({"error": "AI service not available"}), 503

            # Load memory
            memory = load_memory_optimized()

            # Add user message to memory
            memory["life_events"].append({
                "date": datetime.date.today().isoformat(),
                "event": user_input,
                "timestamp": datetime.datetime.now().isoformat()
            })

            # Prepare minimal context for faster processing
            recent_events = memory["life_events"][-5:]  # Reduced for performance

            context = f"""You are an AI Life Coach. Recent events: {recent_events}

            Provide brief, supportive guidance."""

            # Generate response using optimized settings
            response = openai_client.ChatCompletion.create(
                model="gpt-3.5-turbo",  # Supported model for older API
                messages=[
                    {"role": "system", "content": context},
                    {"role": "user", "content": user_input}
                ],
                max_tokens=150,  # Reduced for faster response
                temperature=0.7
            )

            ai_response = response.choices[0].message.content.strip()

            # Add AI response to memory
            memory["life_events"].append({
                "date": datetime.date.today().isoformat(),
                "event": f"AI Coach: {ai_response}",
                "timestamp": datetime.datetime.now().isoformat()
            })

            return jsonify({
                "response": ai_response,
                "status": "success"
            })

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # Import the optimized serverless wrapper
    from serverless_wrapper import ServerlessWSGIHandler

    # Create the serverless handler with optimizations
    handler = ServerlessWSGIHandler(app, timeout=30)

except ImportError as e:
    # Fallback for missing dependencies
    def handler(event, context):
        return {
            'statusCode': 503,
            'body': json.dumps({'error': f'Service unavailable: {str(e)}'})
        }

# For local testing
if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)