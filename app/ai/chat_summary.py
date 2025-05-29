from dotenv import load_dotenv
import os
import openai

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
print("✅ OpenAI Key Loaded:", bool(openai.api_key))
