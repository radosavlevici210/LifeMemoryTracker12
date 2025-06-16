import os
import json
import datetime
import logging
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from openai import OpenAI

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
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logging.error(f"Error loading memory file: {e}")
            return {"life_events": [], "goals": [], "warnings": []}
    return {"life_events": [], "goals": [], "warnings": []}

def save_memory(data):
    """Save user's life memory to JSON file"""
    try:
        with open(MEMORY_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except IOError as e:
        logging.error(f"Error saving memory file: {e}")

@app.route("/")
def index():
    """Render the main chat interface"""
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    """Handle chat messages and provide AI responses"""
    try:
        data = request.get_json()
        if not data or "message" not in data:
            return jsonify({"error": "Invalid request format"}), 400
        
        user_input = data["message"].strip()
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
        empty_memory = {"life_events": [], "goals": [], "warnings": [], "mood_history": [], "achievements": [], "action_items": []}
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
                "achievements": len(memory.get("achievements", []))
            },
            "data": memory
        }
        
        return jsonify(export_data)
        
    except Exception as e:
        logging.error(f"Error exporting data: {e}")
        return jsonify({"error": "Unable to export data"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
