"""
client.py

Client-side LLM agent that communicates with the MCP server tools.

This agent:
  • Defines the tool schema for Gemini.
  • Sends user questions to Gemini.
  • Lets Gemini decide which tools to call.
  • Executes tool calls on the MCP server via HTTP.
  • Returns structured JSON results to the frontend.
  • Supports automatic multi-tool chaining (e.g., places → translations).

Used by:
  • CLI agent (when running this file directly)
  • Flask web UI (app.py)

Environment variables:
  GEMINI_API_KEY — required for Gemini tool-calling model
"""

import os
import json
import requests
from google import generativeai as genai

# Configure Gemini
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://127.0.0.1:8080")



# Tool calling helper

def call_tool(tool_name, arguments):
    """
    Call a tool on the MCP server.

    Args:
        tool_name (str): name of the tool route (e.g. "get_weather")
        arguments (dict): payload sent to the tool

    Returns:
        dict: JSON response from the tool OR { "error": ... }
    """
    try:
        url = f"{MCP_SERVER_URL}/tool/{tool_name}"
        response = requests.post(url, json=arguments)
        return response.json()
    except Exception as e:
        return {"error": str(e)}


# Main agent logic using Gemini tool-calling
def run_agent(user_query):
    """
    Main LLM agent entry point.

    Steps:
      1. Define tool schemas for Gemini.
      2. Ask Gemini to interpret user query.
      3. Gemini decides if tools are needed.
      4. Execute tool calls and collect outputs.
      5. Return structured JSON (used by UI).

    Args:
        user_query (str): natural language question from user

    Returns:
        str: JSON string OR natural-language fallback text
    """

    # Define the available tools for Gemini
    TOOLS = [
        {
            "function_declarations": [
                {
                    "name": "geocode_location",
                    "description": "Get coordinates for a place.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {"location": {"type": "string"}},
                        "required": ["location"]
                    }
                },
                {
                    "name": "get_weather",
                    "description": "Fetch weather for a location.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {"location": {"type": "string"}},
                        "required": ["location"]
                    }
                },
                {
                    "name": "search_places",
                    "description": "Search for businesses at a location.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "query": {"type": "string"},
                            "location": {"type": "string"}
                        },
                        "required": ["query", "location"]
                    }
                },
                {
                    "name": "translate_text",
                    "description": "Translate text into another language.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "text": {"type": "string"},
                            "target_lang": {"type": "string"}
                        },
                        "required": ["text", "target_lang"]
                    }
                }
            ]
        }
    ]

    # Instantiate Gemini with tool support
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        tools=TOOLS
    )

    # FIRST MODEL CALL — Gemini decides tool usage
    response = model.generate_content(user_query)
    parts = response.candidates[0].content.parts

    all_results = {}

    # PROCESS ANY TOOL CALLS
    for part in parts:
        if not hasattr(part, "function_call"):
            # If no tool call, skip
            continue

        fn = part.function_call
        tool_name = fn.name

        # Convert structured tool arguments to dict
        args = {k: v for k, v in dict(fn.args).items()}

        print(f"\nGemini is calling tool: {tool_name}")
        print("Arguments:", args)

        # Run tool on MCP server
        tool_output = call_tool(tool_name, args)
        print("Tool returned:", tool_output, "\n")

        if "error" in tool_output:
            return f"I am sorry, something went wrong → {tool_output['error']}"

        # Store structured results
        all_results[tool_name] = tool_output

    # AUTO-TRANSLATE PLACE NAMES WHEN USER REQUESTS TRANSLATIONS
    if "search_places" in all_results and "translate" in user_query.lower():

        places = all_results["search_places"].get("results", [])
        names_to_translate = [p["name"] for p in places[:3]]  # First 3 names

        # Detect "translate ... to Spanish/Hindi/etc."
        target_lang = None
        words = user_query.lower().split()
        if "to" in words:
            idx = words.index("to")
            if idx + 1 < len(words):
                target_lang = words[idx + 1].strip()

        if not target_lang:
            target_lang = "hindi"  # Safe default

        translations = []

        for name in names_to_translate:
            payload = {"text": name, "target_lang": target_lang}
            t_out = call_tool("translate_text", payload)
            translations.append({
                "original": name,
                "translated": t_out.get("translated_text", "[error]")
            })

        all_results["translations"] = translations

    # RETURN STRUCTURED TOOL RESULTS TO WEB FRONTEND
    if all_results:
        run_agent.last_tool_output = all_results  # for retry logic
        return json.dumps(all_results, indent=2)

    # FALLBACK: If Gemini didn't call tools, return plain text
    try:
        final_response = model.generate_content(user_query)
        return final_response.text
    except:
        return "Sorry — I could not summarize the results."


# CLI Testing
if __name__ == "__main__":
    print("\nSmart City Agent (Gemini) Ready!")
    while True:
        q = input("You: ")
        if q.lower() in ["quit", "exit"]:
            break
        print(run_agent(q), "\n")
