"""
Configuration for CS2 Data Pipeline
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# API Keys
PANDASCORE_API_KEY = os.getenv("PANDASCORE_API_KEY")
ABIOS_CLIENT_ID = os.getenv("ABIOS_CLIENT_ID")
ABIOS_CLIENT_SECRET = os.getenv("ABIOS_CLIENT_SECRET")
ODDSPAPI_API_KEY = os.getenv("ODDSPAPI_API_KEY")

# API Endpoints
PANDASCORE_BASE_URL = "https://api.pandascore.co"
ABIOS_BASE_URL = "https://api.abiosgaming.com/v3"
ODDSPAPI_BASE_URL = "https://api.oddspapi.io/v1"

# Rate limiting
API_RATE_LIMIT_DELAY = float(os.getenv("API_RATE_LIMIT_DELAY", "1.0"))

# CS2 Game ID mappings (varies by API)
CS2_GAME_IDS = {
    "pandascore": "csgo",  # PandaScore uses 'csgo' for CS2
    "abios": 5,            # Abios game ID for CS2
}
