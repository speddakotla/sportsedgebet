"""
Configuration for MLB Data Pipeline
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# API Keys
MLB_STATS_API_KEY = os.getenv("MLB_STATS_API_KEY", "")  # Optional, MLB Stats API is free
ODDS_API_KEY = os.getenv("ODDS_API_KEY")  # The Odds API key
ESPN_API_KEY = os.getenv("ESPN_API_KEY", "")  # Optional backup

# API Endpoints
MLB_STATS_BASE_URL = "https://statsapi.mlb.com/api/v1"
ODDS_API_BASE_URL = "https://api.the-odds-api.com/v4"

# Rate limiting
API_RATE_LIMIT_DELAY = float(os.getenv("API_RATE_LIMIT_DELAY", "0.5"))  # MLB Stats API is more lenient

# MLB Configuration
MLB_SEASON = int(os.getenv("MLB_SEASON", "2024"))  # Current season year
MLB_SPORT_KEY = "baseball_mlb"  # For The Odds API
