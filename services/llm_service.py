import os
import json
import google.generativeai as genai
import groq

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import GEMINI_API_KEY, GROQ_API_KEY

# Configure Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Initialize Groq
groq_client = groq.Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

def generate_json_response(prompt, system_prompt="You are a helpful AI assistant."):
    """
    Tries Gemini first. If rate limited or fails, falls back to Groq (Llama 3).
    Returns a parsed JSON dictionary.
    """
    # 1. Try Gemini
    if GEMINI_API_KEY:
        try:
            model = genai.GenerativeModel(
                model_name="gemini-3.6-flash",
                system_instruction=system_prompt
            )
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                )
            )
            return json.loads(response.text)
        except Exception as e:
            print(f"Gemini failed (possibly rate limit). Error: {e}")
            print("Falling back to Groq...")
    
    # 2. Fallback to Groq GPT-OSS
    if groq_client:
        try:
            messages = [
                {"role": "system", "content": system_prompt + "\nIMPORTANT: Return ONLY a valid JSON object. No markdown formatting."},
                {"role": "user", "content": prompt}
            ]
            response = groq_client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=messages,
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"Groq failed. Error: {e}")
    
    if not GEMINI_API_KEY and not GROQ_API_KEY:
        print("Error: Neither GEMINI_API_KEY nor GROQ_API_KEY are configured in .env")
        
    return None
