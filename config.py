import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Google Workspace / Gmail API paths
GMAIL_CREDENTIALS_PATH = os.path.join(os.path.dirname(__file__), "credentials.json")
GMAIL_TOKEN_PATH = os.path.join(os.path.dirname(__file__), "token.json")

# App Settings
DAILY_EMAIL_LIMIT = 40

if not GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY is missing. Please add it to your .env file.")
