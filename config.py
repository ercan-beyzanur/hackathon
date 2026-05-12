import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
API_URL = os.getenv("API_URL", "http://localhost:8000")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY bulunamadı!")


