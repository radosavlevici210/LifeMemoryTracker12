# ============================================
# Project: LifeMemoryTracker12
# Author: Ervin Remus Radosavlevici
# Copyright: © 2025 Ervin Remus Radosavlevici
# All rights reserved. Protected under digital trace monitoring.
# Unauthorized usage will trigger automated reports.
# ============================================

import datetime
import socket
import platform
import getpass

def log_access():
    log_info = {
        "timestamp": datetime.datetime.now().isoformat(),
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "user": getpass.getuser()
    }
    with open("access_log.txt", "a") as f:
        f.write(str(log_info) + "\n")

log_access()

from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import datetime

app = Flask(__name__)
CORS(app)

openai.api_key = "your-openai-api-key"  # Replace this with your OpenAI key

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json["message"]
    today = datetime.date.today().isoformat()

    system_prompt = f"You are a life advisor assistant. Today is {today}. The user is Ervin. Give helpful, safe, and positive advice only. Avoid dangerous or illegal suggestions. Help with daily problems."

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
    )
    return jsonify({"response": response.choices[0].message["content"]})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
