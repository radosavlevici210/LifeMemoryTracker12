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
        empty_memory = {"life_events": [], "goals": [], "warnings": []}
        save_memory(empty_memory)
        return jsonify({"message": "Memory cleared successfully"})
    except Exception as e:
        logging.error(f"Error clearing memory: {e}")
        return jsonify({"error": "Unable to clear memory"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
