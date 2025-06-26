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
app.secret_key = os.environ.get("SESSION_SECRET")
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
login_manager.login_view = 'login'  # type: ignore
login_manager.login_message = 'Please log in to access this page.'

# OpenAI configuration with connection pooling
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai_client = None

def get_openai_client():
    """Lazy load OpenAI client for better performance"""
    global openai_client
    if openai_client is None and OPENAI_API_KEY:
        openai_client = OpenAI(
            api_key=OPENAI_API_KEY,
            max_retries=2,
            timeout=30.0
        )
    return openai_client

MEMORY_FILE = "life_memory.json"

# Create database tables
with app.app_context():
    # Import models here to avoid circular imports
    import models
    db.create_all()
    
    # Import and register Replit Auth
    from replit_auth import make_replit_blueprint
    app.register_blueprint(make_replit_blueprint(), url_prefix="/auth")

@login_manager.user_loader
def load_user(user_id):
    import models
    return models.User.query.get(user_id)

def load_memory():
    """Load user's life memory from database or JSON file"""
    if current_user.is_authenticated:
        import models
        user_memory = models.UserMemory.query.filter_by(user_id=current_user.id).first()
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
        import models
        user_memory = models.UserMemory.query.filter_by(user_id=current_user.id).first()
        if not user_memory:
            user_memory = models.UserMemory()
            user_memory.user_id = current_user.id
            user_memory.memory_data = json.dumps(data)
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
        
        import models
        user = models.User.query.filter_by(username=username).first()
        
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
def index():
    """Main route with Replit Auth integration"""
    if current_user.is_authenticated:
        # Authenticated user - show main app
        memory = load_memory()
        user_info = {
            'authenticated': True,
            'name': current_user.first_name or current_user.email or 'User',
            'email': current_user.email,
            'profile_image': current_user.profile_image_url
        }
        return render_template("index.html", memory=memory, user_info=user_info)
    else:
        # Non-authenticated user - show landing page
        return render_template("landing.html")

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
        
        client = get_openai_client()
        if not client:
            # Provide helpful fallback response when OpenAI is not available
            fallback_response = """I'm your AI Life Coach, but I need a proper OpenAI API key to provide personalized guidance. 

While you're setting up the API connection, here are some things I can help you with once configured:
- Goal setting and tracking
- Habit formation strategies  
- Mood and wellbeing analysis
- Personal growth insights
- Action planning and motivation

Please provide a valid OpenAI API key to enable full AI coaching capabilities."""
            
            return jsonify({
                "response": fallback_response,
                "type": "system_message"
            })

        # Load memory first
        memory = load_memory()
        
        # Initialize advanced features
        try:
            from ai_personality_engine import AIPersonalityEngine
            personality_engine = AIPersonalityEngine()
            personality = personality_engine.adapt_personality(memory)
            system_prompt = personality_engine.generate_system_prompt(personality, memory)
        except ImportError:
            system_prompt = "You are an empathetic AI Life Coach focused on helping users achieve their goals."
        
        today = datetime.date.today().isoformat()
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
        
        # Get AI response with optimizations
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # Faster model
                messages=[
                    {"role": "system", "content": context},
                    {"role": "user", "content": user_input}
                ],
                max_tokens=400,  # Optimized token limit
                temperature=0.7,
                stream=False
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
            
            # Enhanced error handling with specific guidance
            if "401" in str(e) or "Unauthorized" in str(e):
                error_response = """Your OpenAI API key needs to be updated. The current key has insufficient permissions.

To fix this:
1. Visit platform.openai.com
2. Create a new API key with full permissions
3. Ensure your account has available credit
4. Update the key in your environment settings

Once updated, I'll be able to provide personalized AI life coaching."""
            elif "insufficient_quota" in str(e).lower() or "quota" in str(e).lower():
                error_response = "Your OpenAI account has reached its usage limit. Please check your billing settings at platform.openai.com"
            else:
                error_response = f"AI service temporarily unavailable: {str(e)}"
            
            return jsonify({
                "response": error_response,
                "type": "error_message"
            }), 200
    
    except Exception as e:
        logging.error(f"Chat error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/memory")
def get_memory():
    """Get user's life memory data"""
    try:
        memory = load_memory()
        return jsonify(memory)
    except Exception as e:
        logging.error(f"Memory retrieval error: {e}")
        return jsonify({"error": "Failed to retrieve memory"}), 500

@app.route("/clear_memory", methods=["POST"])
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

@app.route("/status")
def basic_status():
    """Basic status endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.datetime.now().isoformat(),
        "database": "connected" if db.engine else "disconnected",
        "openai": "configured" if get_openai_client() else "not configured"
    })

# Register admin dashboard blueprint
try:
    from admin_dashboard import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')
    logging.info("Admin dashboard registered successfully")
except ImportError as e:
    logging.warning(f"Admin dashboard not available: {e}")

# Register additional features
try:
    from advanced_analytics import AdvancedAnalytics
    analytics = AdvancedAnalytics()
    
    @app.route("/analytics", methods=["GET"])
    def get_analytics():
        """Get advanced analytics report"""
        memory = load_memory()
        report = analytics.generate_comprehensive_report(memory)
        return jsonify(report)
    
    logging.info("Advanced analytics registered successfully")
except ImportError as e:
    logging.warning(f"Advanced analytics not available: {e}")

# Register notification system
try:
    from notification_system import NotificationSystem
    notifications = NotificationSystem()
    
    @app.route("/notifications", methods=["GET"])
    def get_notifications():
        """Get user notifications"""
        user_notifications = notifications.get_user_notifications(
            user_id=str(current_user.id) if current_user.is_authenticated else "default"
        )
        return jsonify(user_notifications)
    
    logging.info("Notification system registered successfully")
except ImportError as e:
    logging.warning(f"Notification system not available: {e}")

# Register collaboration tools
try:
    from collaboration_tools import CollaborationTools
    collaboration = CollaborationTools()
    
    @app.route("/share", methods=["POST"])
    def share_content():
        """Share user content"""
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid request"}), 400
        
        share_id = collaboration.create_share(
            user_id=str(current_user.id),
            share_type=data.get("type"),
            title=data.get("title"),
            content=data.get("content"),
            visibility=data.get("visibility", "private")
        )
        return jsonify({"share_id": share_id})
    
    @app.route("/feed", methods=["GET"])
    def get_feed():
        """Get user feed"""
        feed = collaboration.get_feed(user_id=str(current_user.id))
        return jsonify(feed)
    
    logging.info("Collaboration tools registered successfully")
except ImportError as e:
    logging.warning(f"Collaboration tools not available: {e}")

# Register advanced features
try:
    from smart_recommendations import SmartRecommendationsEngine
    recommendations_engine = SmartRecommendationsEngine()
    
    @app.route("/recommendations", methods=["GET"])
    def get_recommendations():
        """Get personalized recommendations"""
        memory = load_memory()
        recommendations = recommendations_engine.get_recommendation_summary(memory)
        return jsonify(recommendations)
    
    logging.info("Smart recommendations registered successfully")
except ImportError as e:
    logging.warning(f"Smart recommendations not available: {e}")

try:
    from voice_interaction import VoiceInteractionEngine
    voice_engine = VoiceInteractionEngine()
    
    @app.route("/voice/command", methods=["POST"])
    def process_voice_command():
        """Process voice commands"""
        data = request.get_json()
        command = data.get("command", "")
        confidence = data.get("confidence", 0.8)
        
        result = voice_engine.process_voice_command(command, confidence)
        return jsonify(result)
    
    @app.route("/voice/settings", methods=["GET", "POST"])
    def voice_settings():
        """Get or update voice settings"""
        if request.method == "POST":
            data = request.get_json()
            if data.get("enabled"):
                result = voice_engine.enable_voice_interaction()
            else:
                result = voice_engine.disable_voice_interaction()
            return jsonify(result)
        
        return jsonify(voice_engine.get_voice_settings())
    
    logging.info("Voice interaction registered successfully")
except ImportError as e:
    logging.warning(f"Voice interaction not available: {e}")

try:
    from gamification_engine import GamificationEngine
    gamification = GamificationEngine()
    
    @app.route("/gamification/dashboard", methods=["GET"])
    def get_gamification_dashboard():
        """Get gamification dashboard"""
        memory = load_memory()
        dashboard = gamification.get_gamification_dashboard(memory)
        return jsonify(dashboard)
    
    @app.route("/gamification/achievements", methods=["GET"])
    def check_achievements():
        """Check for new achievements"""
        memory = load_memory()
        new_achievements = gamification.check_new_achievements(memory)
        
        # Add new achievements to memory
        if new_achievements:
            if "achievements" not in memory:
                memory["achievements"] = []
            
            for achievement in new_achievements:
                memory["achievements"].append({
                    "id": achievement.id,
                    "title": achievement.title,
                    "description": achievement.description,
                    "points": achievement.points,
                    "achieved_date": achievement.achieved_date.isoformat() if achievement.achieved_date else None
                })
            
            save_memory(memory)
        
        return jsonify({
            "new_achievements": [
                {
                    "id": ach.id,
                    "title": ach.title,
                    "description": ach.description,
                    "badge_icon": ach.badge_icon,
                    "points": ach.points
                }
                for ach in new_achievements
            ]
        })
    
    @app.route("/gamification/challenges", methods=["GET"])
    def get_daily_challenges():
        """Get daily challenges"""
        memory = load_memory()
        stats = gamification.calculate_user_stats(memory)
        challenges = gamification.generate_daily_challenges(memory, stats)
        return jsonify({"challenges": challenges})
    
    logging.info("Gamification engine registered successfully")
except ImportError as e:
    logging.warning(f"Gamification engine not available: {e}")

try:
    from ai_personality_engine import AIPersonalityEngine
    personality_engine = AIPersonalityEngine()
    
    @app.route("/personality/profile", methods=["GET"])
    def get_personality_profile():
        """Get current AI personality profile"""
        memory = load_memory()
        personality = personality_engine.adapt_personality(memory)
        return jsonify(personality_engine.get_personality_summary())
    
    @app.route("/personality/adapt", methods=["POST"])
    def adapt_personality():
        """Manually trigger personality adaptation"""
        memory = load_memory()
        personality = personality_engine.adapt_personality(memory)
        personality_engine.save_personality_profile()
        return jsonify({
            "message": "Personality adapted successfully",
            "profile": personality_engine.get_personality_summary()
        })
    
    logging.info("AI personality engine registered successfully")
except ImportError as e:
    logging.warning(f"AI personality engine not available: {e}")

# Enhanced goal management
@app.route("/goals", methods=["GET", "POST"])
def manage_goals():
    """Enhanced goal management"""
    memory = load_memory()
    
    if request.method == "POST":
        data = request.get_json()
        goal = {
            "id": len(memory.get("goals", [])) + 1,
            "text": data.get("text", ""),
            "category": data.get("category", "personal"),
            "priority": data.get("priority", "medium"),
            "target_date": data.get("target_date", ""),
            "progress": 0,
            "status": "active",
            "created_date": datetime.datetime.now().isoformat(),
            "milestones": data.get("milestones", [])
        }
        
        if "goals" not in memory:
            memory["goals"] = []
        memory["goals"].append(goal)
        save_memory(memory)
        
        return jsonify({"message": "Goal added successfully", "goal": goal})
    
    return jsonify(memory.get("goals", []))

@app.route("/goals/<int:goal_id>/progress", methods=["POST"])
def update_goal_progress(goal_id):
    """Update goal progress"""
    memory = load_memory()
    data = request.get_json()
    progress = data.get("progress", 0)
    
    goals = memory.get("goals", [])
    for goal in goals:
        if goal.get("id") == goal_id:
            goal["progress"] = min(max(progress, 0), 100)
            if goal["progress"] >= 100:
                goal["status"] = "completed"
                goal["completed_date"] = datetime.datetime.now().isoformat()
            break
    
    save_memory(memory)
    return jsonify({"message": "Goal progress updated"})

# Enhanced habit tracking
@app.route("/habits", methods=["GET", "POST"])
def manage_habits():
    """Enhanced habit management"""
    memory = load_memory()
    
    if request.method == "POST":
        data = request.get_json()
        habit = {
            "id": len(memory.get("habits", [])) + 1,
            "text": data.get("text", ""),
            "frequency": data.get("frequency", 7),  # times per week
            "category": data.get("category", "health"),
            "current_streak": 0,
            "best_streak": 0,
            "status": "active",
            "created_date": datetime.datetime.now().isoformat(),
            "last_completed": None
        }
        
        if "habits" not in memory:
            memory["habits"] = []
        memory["habits"].append(habit)
        save_memory(memory)
        
        return jsonify({"message": "Habit added successfully", "habit": habit})
    
    return jsonify(memory.get("habits", []))

@app.route("/habits/<int:habit_id>/complete", methods=["POST"])
def complete_habit(habit_id):
    """Mark habit as completed for today"""
    memory = load_memory()
    today = datetime.date.today().isoformat()
    
    habits = memory.get("habits", [])
    for habit in habits:
        if habit.get("id") == habit_id:
            habit["last_completed"] = today
            habit["current_streak"] = habit.get("current_streak", 0) + 1
            habit["best_streak"] = max(habit.get("best_streak", 0), habit["current_streak"])
            break
    
    save_memory(memory)
    return jsonify({"message": "Habit completed for today"})

# Mood tracking with insights
@app.route("/mood", methods=["GET", "POST"])
def track_mood():
    """Enhanced mood tracking"""
    memory = load_memory()
    
    if request.method == "POST":
        data = request.get_json()
        mood_entry = {
            "date": datetime.date.today().isoformat(),
            "timestamp": datetime.datetime.now().isoformat(),
            "mood": data.get("mood", 5),
            "energy": data.get("energy", 5),
            "stress": data.get("stress", 5),
            "notes": data.get("notes", ""),
            "tags": data.get("tags", [])
        }
        
        if "mood_history" not in memory:
            memory["mood_history"] = []
        memory["mood_history"].append(mood_entry)
        save_memory(memory)
        
        return jsonify({"message": "Mood tracked successfully", "mood": mood_entry})
    
    return jsonify(memory.get("mood_history", []))

# Production health endpoints
@app.route("/health", methods=["GET"])
def production_health():
    """Comprehensive health check endpoint"""
    try:
        from production_monitoring import monitor
        health_data = monitor.get_system_health()
        return jsonify(health_data)
    except ImportError:
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.datetime.now().isoformat(),
            "version": "2.0.0",
            "features": {
                "ai_chat": bool(get_openai_client()),
                "database": True,
                "gamification": True,
                "recommendations": True,
                "voice_interaction": True,
                "personality_engine": True
            }
        })

@app.route("/health/detailed", methods=["GET"])
def detailed_health_check():
    """Detailed health and performance metrics"""
    try:
        from production_monitoring import monitor
        return jsonify(monitor.get_performance_summary())
    except ImportError:
        return jsonify({
            "status": "basic_monitoring",
            "message": "Advanced monitoring not available"
        })

@app.route("/version", methods=["GET"])
def version_info():
    """Get application version and feature information"""
    try:
        from production_config import ProductionConfig
        return jsonify(ProductionConfig.get_version_info())
    except ImportError:
        return jsonify({
            "version": "2.0.0",
            "environment": "production",
            "build_date": datetime.datetime.now().isoformat(),
            "features": {
                "ai_chat": True,
                "gamification": True,
                "recommendations": True,
                "voice_interaction": True,
                "personality_engine": True,
                "analytics": True
            }
        })

# Error handling
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Resource not found",
        "status": 404,
        "timestamp": datetime.datetime.now().isoformat()
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "error": "Internal server error",
        "status": 500,
        "timestamp": datetime.datetime.now().isoformat(),
        "support": "Please try again or contact support if the issue persists"
    }), 500

@app.errorhandler(429)
def rate_limit_exceeded(error):
    return jsonify({
        "error": "Rate limit exceeded",
        "status": 429,
        "timestamp": datetime.datetime.now().isoformat(),
        "message": "Please wait before making more requests"
    }), 429

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
