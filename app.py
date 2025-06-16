import os
import json
import datetime
import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET") or "dev-secret-key-for-migration"
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# OpenAI configuration
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

MEMORY_FILE = "life_memory.json"

# Import models after db initialization
from models import User, UserMemory

# Create database tables
with app.app_context():
    db.create_all()
    
    # Create default user if not exists
    default_user = User.query.filter_by(username='Ervin').first()
    if not default_user:
        default_user = User(username='Ervin')
        default_user.set_password('Quantum210')
        db.session.add(default_user)
        db.session.commit()
        logging.info("Default user created successfully")

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def load_memory():
    """Load user's life memory from database or JSON file"""
    if current_user.is_authenticated:
        user_memory = UserMemory.query.filter_by(user_id=current_user.id).first()
        if user_memory:
            try:
                return json.loads(user_memory.memory_data)
            except json.JSONDecodeError:
                pass
    
    # Fallback to file-based storage
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r") as f:
                data = json.load(f)
                default_structure = {
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
                for key, default_value in default_structure.items():
                    if key not in data:
                        data[key] = default_value
                return data
        except (json.JSONDecodeError, IOError) as e:
            logging.error(f"Error loading memory file: {e}")
    
    return {
        "life_events": [], "goals": [], "warnings": [],
        "mood_history": [], "achievements": [], "action_items": [],
        "habits": [], "reflections": [], "milestones": []
    }

def save_memory(data):
    """Save user's life memory to database or JSON file"""
    if current_user.is_authenticated:
        user_memory = UserMemory.query.filter_by(user_id=current_user.id).first()
        if not user_memory:
            user_memory = UserMemory(user_id=current_user.id, memory_data=json.dumps(data))
            db.session.add(user_memory)
        else:
            user_memory.memory_data = json.dumps(data)
            user_memory.updated_at = datetime.datetime.utcnow()
        db.session.commit()
    else:
        # Fallback to file-based storage
        try:
            with open(MEMORY_FILE, "w") as f:
                json.dump(data, f, indent=2)
        except IOError as e:
            logging.error(f"Error saving memory file: {e}")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Handle user login"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        if not username or not password:
            flash("Please enter both username and password")
            return render_template("login.html")
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            user.last_login = datetime.datetime.utcnow()
            db.session.commit()
            return redirect(url_for("index"))
        else:
            flash("Invalid username or password")
    
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    """Handle user logout"""
    logout_user()
    return redirect(url_for("login"))

@app.route("/")
@login_required
def index():
    """Render the main chat interface"""
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
@login_required
def chat():
    """Handle chat messages and provide AI responses"""
    try:
        data = request.get_json()
        if not data or "message" not in data:
            return jsonify({"error": "Invalid request format"}), 400
        
        user_input = data.get("message", "").strip()
        
        if not user_input:
            return jsonify({"error": "Message cannot be empty"}), 400
        
        if not openai_client:
            return jsonify({"error": "OpenAI API not configured. Please set OPENAI_API_KEY."}), 500
        
        today = datetime.date.today().isoformat()
        
        # Load and update memory
        memory = load_memory()
        memory["life_events"].append({
            "date": today,
            "event": user_input,
            "timestamp": datetime.datetime.now().isoformat()
        })
        
        # Prepare context for AI
        recent_events = memory["life_events"][-10:] if memory["life_events"] else []
        recent_goals = memory["goals"][-5:] if memory["goals"] else []
        recent_mood = memory["mood_history"][-3:] if memory["mood_history"] else []
        
        context = f"""You are an AI Life Coach. Here's what you know about the user:

Recent life events: {recent_events}
Current goals: {recent_goals}
Recent mood: {recent_mood}

Provide supportive, actionable guidance. Be empathetic and helpful."""
        
        # Get AI response
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": context},
                    {"role": "user", "content": user_input}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content
            
            # Add AI response to memory
            memory["life_events"].append({
                "date": today,
                "event": f"AI Coach: {ai_response}",
                "timestamp": datetime.datetime.now().isoformat()
            })
            
            save_memory(memory)
            
            return jsonify({
                "response": ai_response,
                "status": "success"
            })
            
        except Exception as e:
            logging.error(f"OpenAI API error: {e}")
            return jsonify({"error": "Failed to get AI response"}), 500
    
    except Exception as e:
        logging.error(f"Chat error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/memory")
@login_required
def get_memory():
    """Get user's life memory data"""
    try:
        memory = load_memory()
        return jsonify(memory)
    except Exception as e:
        logging.error(f"Memory retrieval error: {e}")
        return jsonify({"error": "Failed to retrieve memory"}), 500

@app.route("/clear_memory", methods=["POST"])
@login_required
def clear_memory():
    """Clear user's life memory"""
    try:
        empty_memory = {
            "life_events": [], "goals": [], "warnings": [],
            "mood_history": [], "achievements": [], "action_items": [],
            "habits": [], "reflections": [], "milestones": []
        }
        save_memory(empty_memory)
        return jsonify({"message": "Memory cleared successfully"})
    except Exception as e:
        logging.error(f"Memory clear error: {e}")
        return jsonify({"error": "Failed to clear memory"}), 500

@app.route("/health")
def health_check():
    """Simple health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.datetime.now().isoformat(),
        "database": "connected" if db.engine else "disconnected",
        "openai": "configured" if openai_client else "not configured"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)