"""
Unified Smart City Info Agent Server

This server provides:

1. MCP Tool Endpoints:
    • /tool/geocode_location
    • /tool/get_weather
    • /tool/search_places
    • /tool/translate_text

2. Frontend Web UI:
    • Serves index.html + static CSS
    • Accepts user queries at /ask

3. Client Agent Integration:
    • Calls LLM (Gemini) + MCP tools via client.py

This entire app runs inside Cloud Run as ONE service with ONE public URL.
"""

import os
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from client import client
import sys

# Make sure Python can import final/client/client.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "client")))

from client import run_agent

# Tool functions
from tools.geocode import geocode_location
from tools.get_weather import get_weather
from tools.search_places import search_places
from tools.translate_text import translate_text


# Flask App Setup
app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)


# MCP TOOL ENDPOINTS

@app.route("/tool/geocode_location", methods=["POST"])
def tool_geocode():
    return jsonify(geocode_location(request.json))


@app.route("/tool/get_weather", methods=["POST"])
def tool_weather():
    return jsonify(get_weather(request.json))


@app.route("/tool/search_places", methods=["POST"])
def tool_places():
    return jsonify(search_places(request.json))


@app.route("/tool/translate_text", methods=["POST"])
def tool_translate():
    return jsonify(translate_text(request.json))


# UI + AGENT ENDPOINT

@app.route("/")
def home():
    """Serve the Web UI."""
    return render_template("index.html")


@app.route("/ask", methods=["POST"])
def ask():
    """Frontend → Agent → Tools → LLM → Response pipeline"""
    try:
        question = request.json.get("question", "").strip()
        if not question:
            return jsonify({"error": "Question cannot be empty"}), 400

        print(f"[SERVER] User asked: {question}")

        answer = run_agent(question)
        return jsonify({"answer": answer})

    except Exception as e:
        print("ERROR in /ask:", e)
        return jsonify({"error": str(e)}), 500


# HEALTH CHECK
@app.route("/health")
def health():
    return {"status": "ok"}


# RUN LOCAL DEV SERVER
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
