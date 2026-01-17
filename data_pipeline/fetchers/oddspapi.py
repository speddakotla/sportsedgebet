"""
OddsPapi.io API Fetcher
Focused on esports odds including CS2 sharp lines
"""
from typing import List, Optional
from datetime import datetime
from .base import BaseFetcher, FetchResult

import sys
sys.path.append('..')
from config import ODDSPAPI_BASE_URL, ODDSPAPI_API_KEY


class OddsPapiFetcher(BaseFetcher):
    """Fetcher for OddsPapi.io odds data"""
    
    def __init__(self):
        super().__init__(
            base_url=ODDSPAPI_BASE_URL,
            api_key=ODDSPAPI_API_KEY,
            source_name="oddspapi"
        )
    
    def _get_auth_headers(self) -> dict:
        return {"X-Api-Key": self.api_key}
    
    def fetch_cs2_odds(self, event_type: str = "upcoming") -> List[dict]:
        """
        Fetch CS2 match odds
        event_type: 'upcoming', 'live'
        """
        endpoint = "/odds/esports/cs2"
        params = {"status": event_type}
        
        try:
            data = self._make_request(endpoint, params=params)
        except Exception as e:
            # API might have different structure, handle gracefully
            print(f"OddsPapi fetch error: {e}")
            return []
        
        odds_list = []
        for event in data.get("data", []):
            match_info = {
                "match_external_id": event.get("event_id"),
                "team1_name": event.get("home_team"),
                "team2_name": event.get("away_team"),
                "scheduled_at": event.get("commence_time"),
            }
            
            # Process each bookmaker's odds
            for bookmaker in event.get("bookmakers", []):
                for market in bookmaker.get("markets", []):
                    for outcome in market.get("outcomes", []):
                        odds_list.append({
                            **match_info,
                            "bookmaker": bookmaker.get("key"),
                            "market_type": market.get("key"),
                            "selection": outcome.get("name"),
                            "odds_decimal": outcome.get("price"),
                            "is_live": event_type == "live",
                            "source": self.source_name,
                            "fetched_at": datetime.utcnow().isoformat()
                        })
        
        return odds_list
    
    def fetch_pinnacle_odds(self) -> List[dict]:
        """
        Fetch Pinnacle sharp lines specifically (for reference odds)
        Pinnacle is known for sharp, unbiased odds
        """
        endpoint = "/odds/esports/cs2"
        params = {"bookmakers": "pinnacle"}
        
        try:
            data = self._make_request(endpoint, params=params)
        except Exception as e:
            print(f"Pinnacle odds fetch error: {e}")
            return []
        
        return self._parse_odds(data, bookmaker_filter="pinnacle")
    
    def _parse_odds(self, data: dict, bookmaker_filter: str = None) -> List[dict]:
        """Parse odds data into standard format"""
        odds_list = []
        
        for event in data.get("data", []):
            for bookmaker in event.get("bookmakers", []):
                if bookmaker_filter and bookmaker.get("key") != bookmaker_filter:
                    continue
                    
                for market in bookmaker.get("markets", []):
                    for outcome in market.get("outcomes", []):
                        odds_list.append({
                            "match_external_id": event.get("event_id"),
                            "bookmaker": bookmaker.get("key"),
                            "market_type": market.get("key"),
                            "selection": outcome.get("name"),
                            "odds_decimal": outcome.get("price"),
                            "line": outcome.get("point"),  # For handicaps/totals
                            "is_live": False,
                            "source": self.source_name,
                            "fetched_at": datetime.utcnow().isoformat()
                        })
        
        return odds_list
    
    def calculate_implied_probability(self, odds_decimal: float) -> float:
        """Convert decimal odds to implied probability"""
        if odds_decimal <= 0:
            return 0
        return 1 / odds_decimal
    
    def calculate_vig(self, odds1: float, odds2: float) -> float:
        """Calculate bookmaker vig/margin from two-way odds"""
        prob1 = self.calculate_implied_probability(odds1)
        prob2 = self.calculate_implied_probability(odds2)
        return (prob1 + prob2 - 1) * 100  # Return as percentage
