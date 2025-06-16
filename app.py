import os
import json
import datetime
import logging
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from openai import OpenAI
from security import rate_limiter, security_monitor, sanitize_input, log_security_event, system_health_check, auto_repair, backup_data, get_security_metrics
from auto_updater import auto_updater
from notification_system import notification_system, NotificationType, NotificationPriority
try:
    from advanced_analytics import advanced_analytics
except (ImportError, ModuleNotFoundError) as e:
    logging.error(f"Advanced analytics not available: {e}")
    advanced_analytics = None
except Exception as e:
    logging.error(f"Advanced analytics initialization failed: {e}")
    advanced_analytics = None
from collaboration_tools import collaboration_tools, ShareType, ShareVisibility

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
CORS(app)

# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "default_key")
openai_client = OpenAI(api_key=OPENAI_API_KEY)

MEMORY_FILE = "life_memory.json"

def load_memory():
    """Load user's life memory from JSON file"""
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r") as f:
                data = json.load(f)
                # Ensure all required fields exist
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
    return {
        "life_events": [], "goals": [], "warnings": [],
        "mood_history": [], "achievements": [], "action_items": [],
        "habits": [], "reflections": [], "milestones": []
    }

def save_memory(data):
    """Save user's life memory to JSON file"""
    try:
        with open(MEMORY_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except IOError as e:
        logging.error(f"Error saving memory file: {e}")

@app.route("/")
@rate_limiter(max_requests=100, window=60)
@security_monitor
def index():
    """Render the main chat interface"""
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
@rate_limiter(max_requests=30, window=60)
@security_monitor
def chat():
    """Handle chat messages and provide AI responses"""
    try:
        data = request.get_json()
        if not data or "message" not in data:
            return jsonify({"error": "Invalid request format"}), 400

        # Sanitize input
        data = sanitize_input(data)
        user_input = data.get("message", "").strip()

        if not user_input:
            return jsonify({"error": "Message cannot be empty"}), 400

        today = datetime.date.today().isoformat()

        # Load and update memory
        memory = load_memory()
        memory["life_events"].append({
            "date": today, 
            "entry": user_input,
            "timestamp": datetime.datetime.now().isoformat()
        })
        save_memory(memory)

        # Get recent life events for context (last 10 entries)
        recent_entries = memory["life_events"][-10:]
        memory_summary = "\n".join([f"{e['date']}: {e['entry']}" for e in recent_entries])

        # Create system prompt for life coaching
        system_prompt = f"""You are an advanced AI life coach and advisor with deep wisdom and insight. Today is {today}.

Your role is to:
- Provide thoughtful, personalized advice based on the user's life patterns
- Help them achieve their goals and avoid potential pitfalls
- Offer practical strategies for personal growth and success
- Be supportive yet honest about potential challenges
- Consider their emotional, financial, and personal well-being

Here are the user's recent life updates:
{memory_summary}

Analyze patterns in their behavior, emotions, and circumstances. Provide specific, actionable advice that helps them:
1. Make better decisions
2. Achieve their goals
3. Avoid potential problems
4. Build healthier habits
5. Improve relationships and career prospects

Be direct, wise, and encouraging. Focus on transformation and positive outcomes."""

        # Get AI response using GPT-4o
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            max_tokens=1000,
            temperature=0.7
        )

        ai_reply = response.choices[0].message.content

        return jsonify({
            "response": ai_reply,
            "timestamp": datetime.datetime.now().isoformat()
        })

    except Exception as e:
        logging.error(f"Error in chat endpoint: {e}")
        return jsonify({
            "error": "I'm having trouble processing your request right now. Please try again in a moment."
        }), 500

@app.route("/memory", methods=["GET"])
def get_memory():
    """Get user's life memory data"""
    try:
        memory = load_memory()
        return jsonify(memory)
    except Exception as e:
        logging.error(f"Error retrieving memory: {e}")
        return jsonify({"error": "Unable to retrieve memory data"}), 500

@app.route("/clear_memory", methods=["POST"])
def clear_memory():
    """Clear user's life memory (with confirmation)"""
    try:
        empty_memory = {
            "life_events": [], "goals": [], "warnings": [], "mood_history": [], 
            "achievements": [], "action_items": [], "habits": [], "reflections": [], "milestones": []
        }
        save_memory(empty_memory)
        return jsonify({"message": "Memory cleared successfully"})
    except Exception as e:
        logging.error(f"Error clearing memory: {e}")
        return jsonify({"error": "Unable to clear memory"}), 500

@app.route("/mood_check", methods=["POST"])
def mood_check():
    """Analyze user's mood and provide insights"""
    try:
        data = request.get_json()
        if not data or "message" not in data:
            return jsonify({"error": "Invalid request format"}), 400

        user_input = data["message"].strip()
        today = datetime.date.today().isoformat()

        # Analyze mood using AI
        mood_prompt = f"""You are a mood analysis expert. Analyze the following text and determine:
1. Primary emotion (happy, sad, anxious, angry, neutral, excited, frustrated, content, etc.)
2. Intensity level (1-10 scale)
3. Key factors contributing to this mood
4. Brief recommendation for improvement

Text to analyze: "{user_input}"

Respond in JSON format:
{{
    "emotion": "primary emotion",
    "intensity": number between 1-10,
    "factors": ["factor1", "factor2"],
    "recommendation": "brief advice"
}}"""

        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": mood_prompt}],
            response_format={"type": "json_object"},
            max_tokens=300
        )

        mood_data = json.loads(response.choices[0].message.content or "{}")

        # Save mood to memory
        memory = load_memory()
        if "mood_history" not in memory:
            memory["mood_history"] = []

        mood_entry = {
            "date": today,
            "timestamp": datetime.datetime.now().isoformat(),
            "emotion": mood_data.get("emotion", "neutral"),
            "intensity": mood_data.get("intensity", 5),
            "factors": mood_data.get("factors", []),
            "recommendation": mood_data.get("recommendation", ""),
            "original_text": user_input
        }

        memory["mood_history"].append(mood_entry)
        save_memory(memory)

        return jsonify(mood_data)

    except Exception as e:
        logging.error(f"Error in mood check: {e}")
        return jsonify({"error": "Unable to analyze mood"}), 500

@app.route("/goal_tracker", methods=["POST"])
def goal_tracker():
    """Add or update goals"""
    try:
        data = request.get_json()
        action = data.get("action", "add")  # add, update, complete, delete

        memory = load_memory()
        if "goals" not in memory:
            memory["goals"] = []
        if "achievements" not in memory:
            memory["achievements"] = []

        if action == "add":
            goal_text = data.get("goal", "").strip()
            if not goal_text:
                return jsonify({"error": "Goal text is required"}), 400

            goal = {
                "id": len(memory["goals"]) + 1,
                "text": goal_text,
                "created_date": datetime.date.today().isoformat(),
                "status": "active",
                "progress": 0,
                "target_date": data.get("target_date"),
                "category": data.get("category", "general")
            }
            memory["goals"].append(goal)

        elif action == "complete":
            goal_id = data.get("goal_id")
            for goal in memory["goals"]:
                if goal["id"] == goal_id:
                    goal["status"] = "completed"
                    goal["completed_date"] = datetime.date.today().isoformat()

                    # Add to achievements
                    achievement = {
                        "id": len(memory["achievements"]) + 1,
                        "title": goal["text"],
                        "date": datetime.date.today().isoformat(),
                        "category": goal.get("category", "general")
                    }
                    memory["achievements"].append(achievement)
                    break

        elif action == "update_progress":
            goal_id = data.get("goal_id")
            progress = data.get("progress", 0)
            for goal in memory["goals"]:
                if goal["id"] == goal_id:
                    goal["progress"] = min(100, max(0, progress))
                    break

        save_memory(memory)
        return jsonify({"message": "Goal updated successfully", "goals": memory["goals"]})

    except Exception as e:
        logging.error(f"Error in goal tracker: {e}")
        return jsonify({"error": "Unable to update goals"}), 500

@app.route("/action_items", methods=["POST"])
def action_items():
    """Generate action items from conversations"""
    try:
        memory = load_memory()
        recent_events = memory.get("life_events", [])[-5:]  # Last 5 conversations

        if not recent_events:
            return jsonify({"action_items": []})

        context = "\n".join([f"{e['date']}: {e['entry']}" for e in recent_events])

        action_prompt = f"""Based on these recent life updates, generate 3-5 specific, actionable items that would help this person improve their situation:

{context}

Respond with JSON format:
{{
    "action_items": [
        {{
            "title": "specific action",
            "description": "why this helps",
            "priority": "high/medium/low",
            "category": "health/career/relationships/personal/financial"
        }}
    ]
}}"""

        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": action_prompt}],
            response_format={"type": "json_object"},
            max_tokens=500
        )

        action_data = json.loads(response.choices[0].message.content or "{}")

        # Save action items to memory
        if "action_items" not in memory:
            memory["action_items"] = []

        for item in action_data.get("action_items", []):
            item["id"] = len(memory["action_items"]) + 1
            item["created_date"] = datetime.date.today().isoformat()
            item["status"] = "pending"
            memory["action_items"].append(item)

        save_memory(memory)
        return jsonify(action_data)

    except Exception as e:
        logging.error(f"Error generating action items: {e}")
        return jsonify({"error": "Unable to generate action items"}), 500

@app.route("/insights", methods=["GET"])
def get_insights():
    """Generate personalized insights from user data"""
    try:
        memory = load_memory()

        life_events = memory.get("life_events", [])
        mood_history = memory.get("mood_history", [])
        goals = memory.get("goals", [])

        if not life_events and not mood_history:
            return jsonify({"insights": []})

        # Prepare data for analysis
        analysis_data = {
            "total_conversations": len(life_events),
            "active_goals": len([g for g in goals if g.get("status") == "active"]),
            "completed_goals": len([g for g in goals if g.get("status") == "completed"]),
            "recent_moods": [m.get("emotion") for m in mood_history[-10:]],
            "recent_topics": [e.get("entry", "")[:100] for e in life_events[-5:]]
        }

        insight_prompt = f"""Analyze this user's life coaching data and provide 3-4 key insights about their patterns, growth, and areas for improvement:

Data: {json.dumps(analysis_data)}

Respond with JSON format:
{{
    "insights": [
        {{
            "title": "insight title",
            "description": "detailed insight",
            "type": "positive/growth/warning/opportunity",
            "actionable_tip": "specific tip"
        }}
    ]
}}"""

        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": insight_prompt}],
            response_format={"type": "json_object"},
            max_tokens=600
        )

        return jsonify(json.loads(response.choices[0].message.content or "{}"))

    except Exception as e:
        logging.error(f"Error generating insights: {e}")
        return jsonify({"error": "Unable to generate insights"}), 500

@app.route("/export_data", methods=["GET"])
def export_data():
    """Export user's life coaching data"""
    try:
        memory = load_memory()

        # Create comprehensive export
        export_data = {
            "export_date": datetime.datetime.now().isoformat(),
            "summary": {
                "total_conversations": len(memory.get("life_events", [])),
                "total_goals": len(memory.get("goals", [])),
                "completed_goals": len([g for g in memory.get("goals", []) if g.get("status") == "completed"]),
                "mood_entries": len(memory.get("mood_history", [])),
                "achievements": len(memory.get("achievements", [])),
                "habits_tracked": len(memory.get("habits", [])),
                "reflections": len(memory.get("reflections", [])),
                "milestones": len(memory.get("milestones", []))
            },
            "data": memory
        }

        return jsonify(export_data)

    except Exception as e:
        logging.error(f"Error exporting data: {e}")
        return jsonify({"error": "Unable to export data"}), 500

@app.route("/habit_tracker", methods=["POST"])
def habit_tracker():
    """Track daily habits and build streaks"""
    try:
        data = request.get_json()
        action = data.get("action", "add")  # add, update, check_in, delete

        memory = load_memory()
        if "habits" not in memory:
            memory["habits"] = []

        today = datetime.date.today().isoformat()

        if action == "add":
            habit_name = data.get("habit", "").strip()
            if not habit_name:
                return jsonify({"error": "Habit name is required"}), 400

            habit = {
                "id": len(memory["habits"]) + 1,
                "name": habit_name,
                "created_date": today,
                "frequency": data.get("frequency", "daily"),  # daily, weekly, custom
                "target_count": data.get("target_count", 1),
                "current_streak": 0,
                "longest_streak": 0,
                "total_completions": 0,
                "check_ins": [],
                "status": "active"
            }
            memory["habits"].append(habit)

        elif action == "check_in":
            habit_id = data.get("habit_id")
            for habit in memory["habits"]:
                if habit["id"] == habit_id:
                    # Check if already checked in today
                    today_check_ins = [c for c in habit["check_ins"] if c["date"] == today]
                    if today_check_ins:
                        return jsonify({"error": "Already checked in today"}), 400

                    # Add check-in
                    habit["check_ins"].append({
                        "date": today,
                        "timestamp": datetime.datetime.now().isoformat(),
                        "count": data.get("count", 1)
                    })

                    # Update streak
                    habit["total_completions"] += 1
                    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
                    yesterday_check_ins = [c for c in habit["check_ins"] if c["date"] == yesterday]

                    if yesterday_check_ins or habit["current_streak"] == 0:
                        habit["current_streak"] += 1
                    else:
                        habit["current_streak"] = 1

                    if habit["current_streak"] > habit["longest_streak"]:
                        habit["longest_streak"] = habit["current_streak"]

                    break

        save_memory(memory)
        return jsonify({"message": "Habit updated successfully", "habits": memory["habits"]})

    except Exception as e:
        logging.error(f"Error in habit tracker: {e}")
        return jsonify({"error": "Unable to update habits"}), 500

@app.route("/reflection", methods=["POST"])
def add_reflection():
    """Add daily/weekly reflections"""
    try:
        data = request.get_json()
        reflection_text = data.get("reflection", "").strip()
        reflection_type = data.get("type", "daily")  # daily, weekly, monthly

        if not reflection_text:
            return jsonify({"error": "Reflection text is required"}), 400

        memory = load_memory()
        if "reflections" not in memory:
            memory["reflections"] = []

        reflection = {
            "id": len(memory["reflections"]) + 1,
            "text": reflection_text,
            "type": reflection_type,
            "date": datetime.date.today().isoformat(),
            "timestamp": datetime.datetime.now().isoformat(),
            "tags": data.get("tags", [])
        }

        memory["reflections"].append(reflection)
        save_memory(memory)

        return jsonify({"message": "Reflection added successfully", "reflection": reflection})

    except Exception as e:
        logging.error(f"Error adding reflection: {e}")
        return jsonify({"error": "Unable to add reflection"}), 500

@app.route("/milestones", methods=["POST"])
def milestone_tracker():
    """Track important life milestones and celebrations"""
    try:
        data = request.get_json()
        action = data.get("action", "add")  # add, celebrate, update

        memory = load_memory()
        if "milestones" not in memory:
            memory["milestones"] = []

        if action == "add":
            milestone_text = data.get("milestone", "").strip()
            if not milestone_text:
                return jsonify({"error": "Milestone description is required"}), 400

            milestone = {
                "id": len(memory["milestones"]) + 1,
                "title": milestone_text,
                "description": data.get("description", ""),
                "category": data.get("category", "personal"),  # personal, career, health, relationships
                "date": datetime.date.today().isoformat(),
                "importance": data.get("importance", "medium"),  # low, medium, high
                "celebrated": False,
                "reflection": ""
            }
            memory["milestones"].append(milestone)

        elif action == "celebrate":
            milestone_id = data.get("milestone_id")
            celebration_note = data.get("celebration_note", "")

            for milestone in memory["milestones"]:
                if milestone["id"] == milestone_id:
                    milestone["celebrated"] = True
                    milestone["celebration_date"] = datetime.date.today().isoformat()
                    milestone["celebration_note"] = celebration_note
                    break

        save_memory(memory)
        return jsonify({"message": "Milestone updated successfully", "milestones": memory["milestones"]})

    except Exception as e:
        logging.error(f"Error in milestone tracker: {e}")
        return jsonify({"error": "Unable to update milestones"}), 500

@app.route("/progress_report", methods=["GET"])
def generate_progress_report():
    """Generate comprehensive progress report"""
    try:
        memory = load_memory()

        # Calculate date ranges
        today = datetime.date.today()
        week_ago = today - datetime.timedelta(days=7)
        month_ago = today - datetime.timedelta(days=30)

        # Analyze recent activity
        recent_events = [e for e in memory.get("life_events", []) 
                        if datetime.datetime.fromisoformat(e.get("timestamp", e.get("date"))).date() >= week_ago]

        recent_moods = [m for m in memory.get("mood_history", []) 
                       if datetime.datetime.fromisoformat(m.get("timestamp")).date() >= week_ago]

        active_goals = [g for g in memory.get("goals", []) if g.get("status") == "active"]
        completed_goals_month = [g for g in memory.get("goals", []) 
                               if g.get("status") == "completed" and 
                               datetime.datetime.fromisoformat(g.get("completed_date", today.isoformat())).date() >= month_ago]

        # Calculate habit streaks
        habit_summary = []
        for habit in memory.get("habits", []):
            if habit.get("status") == "active":
                habit_summary.append({
                    "name": habit["name"],
                    "current_streak": habit.get("current_streak", 0),
                    "longest_streak": habit.get("longest_streak", 0),
                    "completion_rate": len(habit.get("check_ins", [])) / max(1, 
                        (today - datetime.datetime.fromisoformat(habit["created_date"]).date()).days)
                })

        # Mood trend analysis
        mood_trends = {}
        for mood in recent_moods:
            emotion = mood.get("emotion", "neutral")
            if emotion not in mood_trends:
                mood_trends[emotion] = []
            mood_trends[emotion].append(mood.get("intensity", 5))

        # Calculate averages
        avg_moods = {emotion: sum(intensities) / len(intensities) 
                    for emotion, intensities in mood_trends.items()}

        report = {
            "generated_date": today.isoformat(),
            "period": "Last 7 days",
            "summary": {
                "conversations": len(recent_events),
                "mood_entries": len(recent_moods),
                "goals_completed_this_month": len(completed_goals_month),
                "active_goals": len(active_goals),
                "active_habits": len([h for h in memory.get("habits", []) if h.get("status") == "active"])
            },
            "mood_analysis": {
                "average_moods": avg_moods,
                "dominant_emotion": max(avg_moods.keys(), key=lambda k: avg_moods[k]) if avg_moods else "neutral",
                "mood_stability": len(set(m.get("emotion") for m in recent_moods))
            },
            "habit_performance": habit_summary,
            "recent_achievements": memory.get("achievements", [])[-5:],
            "upcoming_goals": active_goals[:3],
            "reflections": memory.get("reflections", [])[-3:]
        }

        return jsonify(report)

    except Exception as e:
        logging.error(f"Error generating progress report: {e}")
        return jsonify({"error": "Unable to generate progress report"}), 500

@app.route("/ai_coach_advice", methods=["POST"])
@rate_limiter(max_requests=10, window=60)
@security_monitor
def get_ai_coach_advice():
    """Get personalized AI coaching advice based on current situation"""
    try:
        data = request.get_json()
        data = sanitize_input(data)

        situation = data.get("situation", "").strip()
        advice_type = data.get("type", "general")  # general, crisis, motivation, planning

        memory = load_memory()

        # Build context from user's history
        recent_events = memory.get("life_events", [])[-10:]
        recent_moods = memory.get("mood_history", [])[-5:]
        active_goals = [g for g in memory.get("goals", []) if g.get("status") == "active"]
        recent_achievements = memory.get("achievements", [])[-3:]

        context_summary = {
            "recent_conversations": [e.get("entry", "") for e in recent_events],
            "recent_emotions": [f"{m.get('emotion', 'neutral')} ({m.get('intensity', 5)}/10)" for m in recent_moods],
            "active_goals": [g.get("text", "") for g in active_goals],
            "recent_wins": [a.get("title", "") for a in recent_achievements]
        }

        if advice_type == "crisis":
            system_prompt = f"""You are an empathetic crisis support AI coach. The user is going through a difficult time. 

Current situation: {situation}

User's context: {json.dumps(context_summary)}

Provide immediate, supportive, and practical advice. Focus on:
1. Emotional validation and support
2. Immediate actionable steps they can take
3. Resources or coping strategies
4. Encouraging perspective while acknowledging their pain
5. Building on their past achievements and strengths

Be compassionate, direct, and helpful. Avoid generic advice."""

        elif advice_type == "motivation":
            system_prompt = f"""You are an energizing motivational coach. The user needs encouragement and motivation.

Current situation: {situation}

User's context: {json.dumps(context_summary)}

Provide inspiring and practical motivation. Focus on:
1. Highlighting their past achievements and progress
2. Reframing challenges as opportunities
3. Specific action steps to build momentum
4. Connecting their current situation to their goals
5. Energizing language that builds confidence

Be uplifting, specific, and action-oriented."""

        elif advice_type == "planning":
            system_prompt = f"""You are a strategic life planning coach. The user needs help organizing and planning.

Current situation: {situation}

User's context: {json.dumps(context_summary)}

Provide structured planning advice. Focus on:
1. Breaking down the situation into manageable steps
2. Prioritizing actions based on their goals
3. Timeline recommendations
4. Potential obstacles and solutions
5. Connecting to their existing goals and habits

Be systematic, practical, and thorough."""

        else:  # general
            system_prompt = f"""You are a wise AI life coach providing personalized guidance.

Current situation: {situation}

User's context: {json.dumps(context_summary)}

Provide thoughtful, personalized advice considering their history and patterns. Focus on:
1. Understanding their unique situation and context
2. Practical, actionable guidance
3. Building on their strengths and past successes
4. Addressing potential challenges
5. Encouraging growth and positive change

Be insightful, supportive, and specific to their situation."""

        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": situation}
            ],
            max_tokens=800,
            temperature=0.7
        )

        advice = response.choices[0].message.content

        # Save this advice session to memory
        advice_entry = {
            "date": datetime.date.today().isoformat(),
            "timestamp": datetime.datetime.now().isoformat(),
            "situation": situation,
            "advice_type": advice_type,
            "advice": advice
        }

        memory["life_events"].append({
            "date": datetime.date.today().isoformat(),
            "timestamp": datetime.datetime.now().isoformat(),
            "entry": f"Sought {advice_type} advice about: {situation[:100]}..."
        })

        save_memory(memory)

        return jsonify({
            "advice": advice,
            "type": advice_type,
            "timestamp": datetime.datetime.now().isoformat()
        })

    except Exception as e:
        logging.error(f"Error getting AI coach advice: {e}")
        return jsonify({"error": "Unable to provide advice right now"}), 500

# Production-ready system monitoring and management endpoints
@app.route("/system/status", methods=["GET"])
@rate_limiter(max_requests=20, window=60)
@security_monitor
def system_status():
    """Get comprehensive system status"""
    try:
        health = system_health_check()
        security_metrics = get_security_metrics()
        updater_status = auto_updater.get_system_status()

        return jsonify({
            "status": "operational",
            "timestamp": datetime.datetime.now().isoformat(),
            "health": health,
            "security": security_metrics,
            "auto_updater": updater_status,
            "maintenance_mode": auto_updater.maintenance_mode
        })
    except Exception as e:
        logging.error(f"Error getting system status: {e}")
        return jsonify({"error": "Unable to retrieve system status"}), 500

@app.route("/system/health", methods=["GET"])
@rate_limiter(max_requests=100, window=60)
def health_check():
    """Simple health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.datetime.now().isoformat(),
        "version": auto_updater.app_version
    })

@app.route("/system/repair", methods=["POST"])
@rate_limiter(max_requests=5, window=300)  # 5 repairs per 5 minutes
@security_monitor
def trigger_repair():
    """Trigger system auto-repair"""
    try:
        repairs = auto_repair()
        log_security_event("manual_repair_triggered", {"repairs": repairs})

        return jsonify({
            "status": "completed",
            "repairs_performed": repairs,
            "timestamp": datetime.datetime.now().isoformat()
        })
    except Exception as e:
        logging.error(f"Error during manual repair: {e}")
        return jsonify({"error": "Repair operation failed"}), 500

@app.route("/system/backup", methods=["POST"])
@rate_limiter(max_requests=10, window=3600)  # 10 backups per hour
@security_monitor
def create_backup():
    """Create manual backup"""
    try:
        backup_filename = backup_data()

        if backup_filename:
            return jsonify({
                "status": "success",
                "backup_file": backup_filename,
                "timestamp": datetime.datetime.now().isoformat()
            })
        else:
            return jsonify({"error": "Backup creation failed"}), 500

    except Exception as e:
        logging.error(f"Error creating backup: {e}")
        return jsonify({"error": "Backup operation failed"}), 500

@app.route("/system/updates", methods=["GET"])
@rate_limiter(max_requests=10, window=300)
@security_monitor
def check_updates():
    """Check for system updates"""
    try:
        update_status = auto_updater.check_for_updates()
        return jsonify(update_status)
    except Exception as e:
        logging.error(f"Error checking updates: {e}")
        return jsonify({"error": "Update check failed"}), 500

@app.route("/system/updates", methods=["POST"])
@rate_limiter(max_requests=3, window=3600)  # 3 update attempts per hour
@security_monitor
def apply_updates():
    """Apply system updates"""
    try:
        data = request.get_json() or {}
        update_ids = data.get("update_ids", [])

        if not update_ids:
            # Apply all pending updates
            updates_to_apply = auto_updater.pending_updates
        else:
            # Apply specific updates
            updates_to_apply = [
                update for update in auto_updater.pending_updates
                if update["id"] in update_ids
            ]

        if not updates_to_apply:
            return jsonify({"error": "No updates to apply"}), 400

        result = auto_updater.apply_updates(updates_to_apply)
        return jsonify(result)

    except Exception as e:
        logging.error(f"Error applying updates: {e}")
        return jsonify({"error": "Update application failed"}), 500

@app.route("/system/optimize", methods=["POST"])
@rate_limiter(max_requests=5, window=1800)  # 5 optimizations per 30 minutes
@security_monitor
def optimize_system():
    """Optimize system performance"""
    try:
        result = auto_updater.optimize_performance()
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error optimizing system: {e}")
        return jsonify({"error": "Optimization failed"}), 500

@app.route("/notifications", methods=["GET"])
@rate_limiter(max_requests=50, window=60)
@security_monitor
def get_notifications():
    """Get user notifications"""
    try:
        limit = request.args.get("limit", 20, type=int)
        unread_only = request.args.get("unread", False, type=bool)

        notifications = notification_system.get_user_notifications(
            limit=limit, 
            unread_only=unread_only
        )

        return jsonify({
            "notifications": notifications,
            "total": len(notifications)
        })

    except Exception as e:
        logging.error(f"Error getting notifications: {e}")
        return jsonify({"error": "Unable to retrieve notifications"}), 500

@app.route("/notifications/<notification_id>/read", methods=["POST"])
@rate_limiter(max_requests=100, window=60)
@security_monitor
def mark_notification_read(notification_id):
    """Mark notification as read"""
    try:
        success = notification_system.mark_notification_read(notification_id)

        if success:
            return jsonify({"message": "Notification marked as read"})
        else:
            return jsonify({"error": "Notification not found"}), 404

    except Exception as e:
        logging.error(f"Error marking notification as read: {e}")
        return jsonify({"error": "Unable to update notification"}), 500

@app.route("/notifications/preferences", methods=["GET", "POST"])
@rate_limiter(max_requests=20, window=60)
@security_monitor
def notification_preferences():
    """Get or update notification preferences"""
    try:
        if request.method == "GET":
            return jsonify(notification_system.notification_preferences)

        elif request.method == "POST":
            data = request.get_json()
            if not data:
                return jsonify({"error": "Invalid request format"}), 400

            notification_system.update_preferences(data)
            return jsonify({
                "message": "Preferences updated successfully",
                "preferences": notification_system.notification_preferences
            })

    except Exception as e:
        logging.error(f"Error handling notification preferences: {e}")
        return jsonify({"error": "Unable to handle preferences"}), 500

@app.route("/analytics/comprehensive", methods=["GET"])
@rate_limiter(max_requests=10, window=300)
@security_monitor
def get_comprehensive_analytics():
    """Get comprehensive analytics report"""
    try:
        if advanced_analytics is None:
            return jsonify({"error": "Analytics module not available"}), 503
            
        memory = load_memory()
        analytics_report = advanced_analytics.generate_comprehensive_report(memory)

        return jsonify(analytics_report)

    except Exception as e:
        logging.error(f"Error generating comprehensive analytics: {e}")
        return jsonify({"error": "Unable to generate analytics"}), 500

@app.route("/analytics/predictions", methods=["GET"])
@rate_limiter(max_requests=20, window=300)
@security_monitor
def get_predictive_analytics():
    """Get predictive analytics and insights"""
    try:
        if advanced_analytics is None:
            return jsonify({"error": "Analytics module not available"}), 503
            
        memory = load_memory()

        # Generate predictions
        from advanced_analytics import AdvancedAnalytics
        analytics = AdvancedAnalytics()

        predictions = {
            "goal_completion": analytics._predict_goal_completion(memory.get("goals", [])),
            "mood_forecast": analytics._predict_mood_trend(memory.get("mood_history", [])),
            "habit_sustainability": analytics._predict_habit_sustainability(memory.get("habits", [])),
            "engagement_forecast": analytics._predict_engagement(memory.get("life_events", [])),
            "achievement_timeline": analytics._predict_next_achievement(memory)
        }

        return jsonify({
            "predictions": predictions,
            "generated_at": datetime.datetime.now().isoformat(),
            "confidence_note": "Predictions are based on historical patterns and may vary"
        })

    except Exception as e:
        logging.error(f"Error generating predictions: {e}")
        return jsonify({"error": "Unable to generate predictions"}), 500

@app.route("/analytics/behavioral", methods=["GET"])
@rate_limiter(max_requests=15, window=300)
@security_monitor
def get_behavioral_analytics():
    """Get behavioral pattern analysis"""
    try:
        if advanced_analytics is None:
            return jsonify({"error": "Analytics module not available"}), 503
            
        memory = load_memory()

        from advanced_analytics import AdvancedAnalytics
        analytics = AdvancedAnalytics()

        patterns = analytics._analyze_patterns(memory)
        recommendations = analytics._generate_recommendations(memory)

        return jsonify({
            "behavioral_patterns": patterns,
            "personalized_recommendations": recommendations,
            "analysis_date": datetime.datetime.now().isoformat()
        })

    except Exception as e:
        logging.error(f"Error generating behavioral analytics: {e}")
        return jsonify({"error": "Unable to generate behavioral analysis"}), 500

@app.route("/smart_notifications/trigger", methods=["POST"])
@rate_limiter(max_requests=5, window=300)
@security_monitor
def trigger_smart_notifications():
    """Manually trigger smart notification generation"""
    try:
        # Generate smart notifications based on current user state
        memory = load_memory()

        # Create contextual notifications
        active_goals = [g for g in memory.get("goals", []) if g.get("status") == "active"]

        if len(active_goals) > 0:
            # Check for stale goals
            stale_goals = []
            for goal in active_goals:
                created_date = datetime.datetime.fromisoformat(goal.get("created_date", datetime.datetime.now().isoformat()))
                days_since_created = (datetime.datetime.now() - created_date).days

                if days_since_created > 7 and goal.get("progress", 0) < 10:
                    stale_goals.append(goal)

            if stale_goals:
                notification_system.create_notification(
                    NotificationType.GOAL_REMINDER,
                    f"Goals Need Attention",
                    f"You have {len(stale_goals)} goals that could use some progress. Let's work on them!",
                    priority=NotificationPriority.MEDIUM
                )

        # Check for habit streaks
        habits = memory.get("habits", [])
        for habit in habits:
            if habit.get("status") == "active":
                streak = habit.get("current_streak", 0)
                if streak > 0 and streak % 5 == 0:  # Every 5 days
                    notification_system.create_notification(
                        NotificationType.HABIT_STREAK,
                        "Habit Streak Achievement!",
                        f"Congratulations! You've maintained '{habit['name']}' for {streak} days!",
                        priority=NotificationPriority.HIGH
                    )

        return jsonify({
            "message": "Smart notifications generated successfully",
            "timestamp": datetime.datetime.now().isoformat()
        })

    except Exception as e:
        logging.error(f"Error generating smart notifications: {e}")
        return jsonify({"error": "Unable to generate smart notifications"}), 500

@app.route("/share/achievement", methods=["POST"])
@rate_limiter(max_requests=20, window=300)
@security_monitor
def share_achievement():
    """Share an achievement"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid request format"}), 400

        achievement_id = data.get("achievement_id")
        visibility = data.get("visibility", "friends")

        memory = load_memory()
        achievements = memory.get("achievements", [])

        achievement = next((a for a in achievements if a.get("id") == achievement_id), None)
        if not achievement:
            return jsonify({"error": "Achievement not found"}), 404

        visibility_enum = ShareVisibility.FRIENDS
        if visibility == "public":
            visibility_enum = ShareVisibility.PUBLIC
        elif visibility == "private":
            visibility_enum = ShareVisibility.PRIVATE

        share_id = collaboration_tools.share_achievement("default", achievement, visibility_enum)

        if share_id:
            return jsonify({
                "message": "Achievement shared successfully",
                "share_id": share_id
            })
        else:
            return jsonify({"error": "Failed to share achievement"}), 500

    except Exception as e:
        logging.error(f"Error sharing achievement: {e}")
        return jsonify({"error": "Unable to share achievement"}), 500

@app.route("/share/milestone", methods=["POST"])
@rate_limiter(max_requests=20, window=300)
@security_monitor
def share_milestone():
    """Share a milestone"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid request format"}), 400

        milestone_id = data.get("milestone_id")
        visibility = data.get("visibility", "friends")

        memory = load_memory()
        milestones = memory.get("milestones", [])

        milestone = next((m for m in milestones if m.get("id") == milestone_id), None)
        if not milestone:
            return jsonify({"error": "Milestone not found"}), 404

        visibility_enum = ShareVisibility.FRIENDS
        if visibility == "public":
            visibility_enum = ShareVisibility.PUBLIC
        elif visibility == "private":
            visibility_enum = ShareVisibility.PRIVATE

        share_id = collaboration_tools.share_milestone("default", milestone, visibility_enum)

        if share_id:
            return jsonify({
                "message": "Milestone shared successfully",
                "share_id": share_id
            })
        else:
            return jsonify({"error": "Failed to share milestone"}), 500

    except Exception as e:
        logging.error(f"Error sharing milestone: {e}")
        return jsonify({"error": "Unable to share milestone"}), 500

@app.route("/share/progress", methods=["POST"])
@rate_limiter(max_requests=10, window=300)
@security_monitor
def share_progress_report():
    """Share a progress report"""
    try:
        data = request.get_json()
        visibility = data.get("visibility", "friends") if data else "friends"

        # Generate fresh progress report
        memory = load_memory()
        from app import generate_progress_report

        # Create a mock request object for the progress report
        class MockRequest:
            def get_json(self):
                return {}

        mock_request = MockRequest()

        # Get progress report data
        with app.test_request_context():
            report_response = generate_progress_report()
            if hasattr(report_response, 'get_json'):
                report = report_response.get_json()
            else:
                report = report_response

        visibility_enum = ShareVisibility.FRIENDS
        if visibility == "public":
            visibility_enum = ShareVisibility.PUBLIC
        elif visibility == "private":
            visibility_enum = ShareVisibility.PRIVATE

        share_id = collaboration_tools.share_progress_report("default", report, visibility_enum)

        if share_id:
            return jsonify({
                "message": "Progress report shared successfully",
                "share_id": share_id
            })
        else:
            return jsonify({"error": "Failed to share progress report"}), 500

    except Exception as e:
        logging.error(f"Error sharing progress report: {e}")
        return jsonify({"error": "Unable to share progress report"}), 500

@app.route("/share/insight", methods=["POST"])
@rate_limiter(max_requests=30, window=300)
@security_monitor
def share_insight():
    """Share a personal insight"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid request format"}), 400

        insight = {
            "title": data.get("title", "Personal Insight"),
            "text": data.get("text", ""),
            "category": data.get("category", "general"),
            "tags": data.get("tags", []),
            "date": datetime.date.today().isoformat(),
            "mood": data.get("mood", "neutral")
        }

        visibility = data.get("visibility", "friends")
        visibility_enum = ShareVisibility.FRIENDS
        if visibility == "public":
            visibility_enum = ShareVisibility.PUBLIC
        elif visibility == "private":
            visibility_enum = ShareVisibility.PRIVATE

        share_id = collaboration_tools.share_insight("default", insight, visibility_enum)

        if share_id:
            return jsonify({
                "message": "Insight shared successfully",
                "share_id": share_id
            })
        else:
            return jsonify({"error": "Failed to share insight"}), 500

    except Exception as e:
        logging.error(f"Error sharing insight: {e}")
        return jsonify({"error": "Unable to share insight"}), 500

@app.route("/shares", methods=["GET"])
@rate_limiter(max_requests=50, window=60)
@security_monitor
def get_shares():
    """Get shared items"""
    try:
        user_id = request.args.get("user_id", "default")
        share_type = request.args.get("type")
        limit = request.args.get("limit", 20, type=int)

        share_type_enum = None
        if share_type:
            try:
                share_type_enum = ShareType(share_type)
            except ValueError:
                return jsonify({"error": "Invalid share type"}), 400

        shares = collaboration_tools.get_shared_items(user_id, share_type_enum, limit)

        return jsonify({
            "shares": shares,
            "total": len(shares)
        })

    except Exception as e:
        logging.error(f"Error getting shares: {e}")
        return jsonify({"error": "Unable to retrieve shares"}), 500

@app.route("/shares/<share_id>", methods=["GET"])
@rate_limiter(max_requests=100, window=60)
@security_monitor
def view_share(share_id):
    """View a specific shared item"""
    try:
        share = collaboration_tools.view_share(share_id)

        if share:
            return jsonify(share)
        else:
            return jsonify({"error": "Share not found"}), 404

    except Exception as e:
        logging.error(f"Error viewing share: {e}")
        return jsonify({"error": "Unable to view share"}), 500

@app.route("/shares/<share_id>/like", methods=["POST"])
@rate_limiter(max_requests=100, window=60)
@security_monitor
def like_share(share_id):
    """Like a shared item"""
    try:
        success = collaboration_tools.like_share(share_id, "default")

        if success:
            return jsonify({"message": "Share liked successfully"})
        else:
            return jsonify({"error": "Unable to like share"}), 400

    except Exception as e:
        logging.error(f"Error liking share: {e}")
        return jsonify({"error": "Unable to like share"}), 500

@app.route("/shares/<share_id>/comment", methods=["POST"])
@rate_limiter(max_requests=50, window=300)
@security_monitor
def add_comment(share_id):
    """Add a comment to a shared item"""
    try:
        data = request.get_json()
        if not data or "text" not in data:
            return jsonify({"error": "Comment text is required"}), 400

        comment_text = sanitize_input(data["text"])
        success = collaboration_tools.add_comment(share_id, "default", comment_text)

        if success:
            return jsonify({"message": "Comment added successfully"})
        else:
            return jsonify({"error": "Unable to add comment"}), 400

    except Exception as e:
        logging.error(f"Error adding comment: {e}")
        return jsonify({"error": "Unable to add comment"}), 500

@app.route("/feed", methods=["GET"])
@rate_limiter(max_requests=30, window=60)
@security_monitor
def get_feed():
    """Get personalized feed"""
    try:
        limit = request.args.get("limit", 20, type=int)
        feed_items = collaboration_tools.get_feed("default", limit)

        return jsonify({
            "feed": feed_items,
            "total": len(feed_items)
        })

    except Exception as e:
        logging.error(f"Error getting feed: {e}")
        return jsonify({"error": "Unable to retrieve feed"}), 500

@app.route("/trending", methods=["GET"])
@rate_limiter(max_requests=20, window=300)
@security_monitor
def get_trending():
    """Get trending shared items"""
    try:
        limit = request.args.get("limit", 10, type=int)
        trending_items = collaboration_tools.get_trending_items(limit)

        return jsonify({
            "trending": trending_items,
            "total": len(trending_items)
        })

    except Exception as e:
        logging.error(f"Error getting trending items: {e}")
        return jsonify({"error": "Unable to retrieve trending items"}), 500

@app.route("/share/settings", methods=["GET", "POST"])
@rate_limiter(max_requests=20, window=300)
@security_monitor
def share_settings():
    """Get or update sharing settings"""
    try:
        if request.method == "GET":
            settings = collaboration_tools.get_share_settings()
            return jsonify(settings)

        elif request.method == "POST":
            data = request.get_json()
            if not data:
                return jsonify({"error": "Invalid request format"}), 400

            collaboration_tools.update_share_settings(data)
            return jsonify({
                "message": "Share settings updated successfully",
                "settings": collaboration_tools.get_share_settings()
            })

    except Exception as e:
        logging.error(f"Error handling share settings: {e}")
        return jsonify({"error": "Unable to handle share settings"}), 500

# Register admin blueprint
from admin_dashboard import admin_bp
app.register_blueprint(admin_bp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)