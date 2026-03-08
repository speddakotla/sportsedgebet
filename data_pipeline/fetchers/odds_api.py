"""
The Odds API Fetcher for MLB
Docs: https://the-odds-api.com/liveapi/guides/v4/
"""
from typing import List, Optional
from datetime import datetime
from .base import BaseFetcher, FetchResult

import sys
sys.path.append('..')
from config import ODDS_API_BASE_URL, ODDS_API_KEY, MLB_SPORT_KEY


class OddsAPIFetcher(BaseFetcher):
    """Fetcher for The Odds API MLB odds data"""
    
    def __init__(self):
        super().__init__(
            base_url=ODDS_API_BASE_URL,
            api_key=ODDS_API_KEY,
            source_name="odds_api"
        )
        self.sport_key = MLB_SPORT_KEY
    
    def _get_auth_headers(self) -> dict:
        return {}
    
    def fetch_mlb_odds(self, regions: List[str] = ["us"], markets: List[str] = ["h2h", "spreads", "totals"]) -> List[dict]:
        """
        Fetch MLB game odds
        regions: ['us', 'uk', 'au'] - betting regions
        markets: ['h2h', 'spreads', 'totals', 'player_props'] - market types
        """
        endpoint = f"/sports/{self.sport_key}/odds"
        params = {
            "apiKey": self.api_key,
            "regions": ",".join(regions),
            "markets": ",".join(markets),
            "oddsFormat": "decimal"
        }
        
        try:
            data = self._make_request(endpoint, params=params)
        except Exception as e:
            print(f"Odds API fetch error: {e}")
            return []
        
        odds_list = []
        for event in data:
            game_external_id = event.get("id")
            commence_time = event.get("commenceTime")
            home_team = event.get("homeTeam")
            away_team = event.get("awayTeam")
            
            # Process each bookmaker's odds
            for bookmaker in event.get("bookmakers", []):
                bookmaker_key = bookmaker.get("key")
                
                for market in bookmaker.get("markets", []):
                    market_key = market.get("key")
                    
                    if market_key == "h2h":  # Moneyline
                        for outcome in market.get("outcomes", []):
                            odds_list.append({
                                "game_external_id": game_external_id,
                                "bookmaker": bookmaker_key,
                                "market_type": "moneyline",
                                "selection": outcome.get("name"),
                                "odds_decimal": outcome.get("price"),
                                "is_live": False,
                                "source": self.source_name,
                                "fetched_at": datetime.utcnow().isoformat()
                            })
                    
                    elif market_key == "spreads":  # Run line
                        for outcome in market.get("outcomes", []):
                            odds_list.append({
                                "game_external_id": game_external_id,
                                "bookmaker": bookmaker_key,
                                "market_type": "spread",
                                "selection": outcome.get("name"),
                                "odds_decimal": outcome.get("price"),
                                "line": outcome.get("point"),
                                "is_live": False,
                                "source": self.source_name,
                                "fetched_at": datetime.utcnow().isoformat()
                            })
                    
                    elif market_key == "totals":  # Over/Under total runs
                        for outcome in market.get("outcomes", []):
                            odds_list.append({
                                "game_external_id": game_external_id,
                                "bookmaker": bookmaker_key,
                                "market_type": "total",
                                "selection": outcome.get("name"),  # "over" or "under"
                                "odds_decimal": outcome.get("price"),
                                "line": market.get("point"),  # Total runs line
                                "is_live": False,
                                "source": self.source_name,
                                "fetched_at": datetime.utcnow().isoformat()
                            })
        
        return odds_list
    
    def fetch_player_props(self, game_id: Optional[str] = None) -> List[dict]:
        """
        Fetch player prop bets (if available)
        Note: Player props may require a premium Odds API subscription
        """
        endpoint = f"/sports/{self.sport_key}/odds"
        params = {
            "apiKey": self.api_key,
            "regions": "us",
            "markets": "player_props",
            "oddsFormat": "decimal"
        }
        
        if game_id:
            params["eventIds"] = game_id
        
        try:
            data = self._make_request(endpoint, params=params)
        except Exception as e:
            print(f"Player props fetch error (may require premium): {e}")
            return []
        
        props = []
        for event in data:
            game_external_id = event.get("id")
            
            for bookmaker in event.get("bookmakers", []):
                for market in bookmaker.get("markets", []):
                    if market.get("key") == "player_props":
                        for outcome in market.get("outcomes", []):
                            # Parse player name and prop type from outcome name
                            # Format: "Player Name - Prop Type"
                            outcome_name = outcome.get("name", "")
                            
                            props.append({
                                "game_external_id": game_external_id,
                                "player_name": outcome_name,  # Would need to parse/match to player
                                "bookmaker": bookmaker.get("key"),
                                "prop_type": market.get("description", "").lower(),
                                "line": outcome.get("point"),
                                "over_odds": outcome.get("price") if "over" in outcome_name.lower() else None,
                                "under_odds": outcome.get("price") if "under" in outcome_name.lower() else None,
                                "is_live": False,
                                "source": self.source_name,
                                "fetched_at": datetime.utcnow().isoformat()
                            })
        
        return props
    
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
