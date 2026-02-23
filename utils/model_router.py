# utils/model_router.py - Simplified version (Gemini only)

import os
import google.generativeai as genai
from .prompts import AYRA_SYSTEM_PROMPT

class ModelRouter:
    def __init__(self):
        # Gemini only
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')

    def route(self, user_input, context, memory_profile=None):
        # Always use Gemini
        return self.call_gemini(user_input, context, memory_profile), "Gemini (Ayra)"

    def call_gemini(self, user_input, context, memory_profile=None):
        prompt = AYRA_SYSTEM_PROMPT + "\n\n"
        if memory_profile:
            prompt += f"User profile: {memory_profile}\n"
        for msg in context[-6:]:
            prompt += f"{msg['role']}: {msg['content']}\n"
        prompt += f"user: {user_input}\nassistant:"
        
        try:
            response = self.gemini_model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Maaf, AYRA ada masalah teknikal: {str(e)}"