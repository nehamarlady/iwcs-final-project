"""
translate_text.py

Provides the MCP tool for text translation using Google's Gemini API.

This module performs:
  1. Input validation for text + target language.
  2. Sending a translation request to the Gemini model.
  3. Returning ONLY the translated text in a clean dictionary format.

Environment Variables Required:
  GEMINI_API_KEY  - API key for Gemini (never hard-coded)

This file is used by your MCP server and will run inside Cloud Run.
"""

import os
from google import generativeai as genai

# Configure Gemini via environment variable
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))


def translate_text(data):
    """
    Translate text into a target language using Gemini.

    Args:
        data (dict):
            Expected format:
                {
                    "text": "hello",
                    "target_lang": "es"
                }

    Returns:
        dict:
            {
                "translated_text": "hola"
            }

        OR on error:
            { "error": "message" }
    """

    # Validate input
    text = data.get("text")
    target = data.get("target_lang")

    if not text or not target:
        return {"error": "Both 'text' and 'target_lang' are required"}

    # Build translation prompt
    prompt = (
        f"Translate the following text into '{target}'. "
        f"Return ONLY the translated text. "
        f"Do NOT explain. Do NOT provide alternatives.\n\n"
        f"{text}"
    )

    # Gemini API call
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)

        translated = response.text.strip()
        return {"translated_text": translated}

    except Exception as e:
        return {"error": str(e)}
