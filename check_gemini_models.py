"""
Quick script to check available Gemini models
"""
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("GEMINI_API_KEY not set in .env file")
    exit(1)

genai.configure(api_key=api_key)

print("Available Gemini models:")
print("=" * 60)
for model in genai.list_models():
    if 'generateContent' in model.supported_generation_methods:
        print(f"  - {model.name}")
        print(f"    Display name: {model.display_name}")
        print(f"    Description: {model.description}")
        print()

