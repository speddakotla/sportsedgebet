"""
PandaScore API Fetcher
Docs: https://developers.pandascore.co/
"""
from typing import List, Optional
from datetime import datetime, timedelta
from .base import BaseFetcher, FetchResult

import sys
sys.path.append('..')
from config import PANDASCORE_BASE_URL, PANDASCORE_API_KEY, CS2_GAME_IDS


class PandaScoreFetcher(BaseFetcher):
    """Fetcher for PandaScore CS2 data"""
    
    def __init__(self):
        super().__init__(
            base_url=PANDASCORE_BASE_URL,
            api_key=PANDASCORE_API_KEY,
            source_name="pandascore"
        )
        self.game = CS2_GAME_IDS["pandascore"]
    
    def _get_auth_headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}"}
    
    def fetch_teams(self, page: int = 1, per_page: int = 100) -> List[dict]:
        """Fetch CS2 teams"""
        endpoint = f"/{self.game}/teams"
        params = {"page": page, "per_page": per_page}
        
        data = self._make_request(endpoint, params=params)
        
        return [{
            "external_id": str(team["id"]),
            "name": team["name"],
            "slug": team.get("slug"),
            "acronym": team.get("acronym"),
            "logo_url": team.get("image_url"),
            "country": team.get("location"),
            "source": self.source_name
        } for team in data]
    
    def fetch_players(self, page: int = 1, per_page: int = 100) -> List[dict]:
        """Fetch CS2 players"""
        endpoint = f"/{self.game}/players"
        params = {"page": page, "per_page": per_page}
        
        data = self._make_request(endpoint, params=params)
        
        return [{
            "external_id": str(player["id"]),
            "name": player["name"],
            "real_name": f"{player.get('first_name', '')} {player.get('last_name', '')}".strip() or None,
            "team_external_id": str(player["current_team"]["id"]) if player.get("current_team") else None,
            "country": player.get("nationality"),
            "age": player.get("age"),
            "role": player.get("role"),
            "image_url": player.get("image_url"),
            "source": self.source_name
        } for player in data]
    
    def fetch_upcoming_matches(self, days_ahead: int = 7) -> List[dict]:
        """Fetch upcoming CS2 matches"""
        endpoint = f"/{self.game}/matches/upcoming"
        params = {"per_page": 100}
        
        data = self._make_request(endpoint, params=params)
        
        return [self._parse_match(match) for match in data]
    
    def fetch_running_matches(self) -> List[dict]:
        """Fetch currently live CS2 matches"""
        endpoint = f"/{self.game}/matches/running"
        
        data = self._make_request(endpoint)
        
        return [self._parse_match(match) for match in data]
    
    def fetch_past_matches(self, page: int = 1, per_page: int = 100) -> List[dict]:
        """Fetch completed CS2 matches for historical data"""
        endpoint = f"/{self.game}/matches/past"
        params = {"page": page, "per_page": per_page}
        
        data = self._make_request(endpoint, params=params)
        
        return [self._parse_match(match) for match in data]
    
    def fetch_match_stats(self, match_id: str) -> List[dict]:
        """Fetch player stats for a specific match"""
        endpoint = f"/matches/{match_id}"
        
        data = self._make_request(endpoint)
        
        stats = []
        for game in data.get("games", []):
            map_name = game.get("map", {}).get("name")
            
            for player_stats in game.get("players", []):
                stats.append({
                    "match_external_id": str(match_id),
                    "player_external_id": str(player_stats["player"]["id"]),
                    "map_name": map_name,
                    "kills": player_stats.get("kills", 0),
                    "deaths": player_stats.get("deaths", 0),
                    "assists": player_stats.get("assists", 0),
                    "headshots": player_stats.get("headshots", 0),
                    "adr": player_stats.get("adr"),
                    "first_kills": player_stats.get("first_kills_diff"),  # May differ by API
                    "source": self.source_name,
                    "raw_data": player_stats
                })
        
        return stats
    
    def _parse_match(self, match: dict) -> dict:
        """Parse match data into standard format"""
        opponents = match.get("opponents", [])
        team1 = opponents[0]["opponent"] if len(opponents) > 0 else None
        team2 = opponents[1]["opponent"] if len(opponents) > 1 else None
        
        results = match.get("results", [])
        team1_score = results[0]["score"] if len(results) > 0 else None
        team2_score = results[1]["score"] if len(results) > 1 else None
        
        winner = match.get("winner")
        
        return {
            "external_id": str(match["id"]),
            "tournament_name": match.get("league", {}).get("name"),
            "tournament_id": str(match.get("league", {}).get("id")),
            "team1_external_id": str(team1["id"]) if team1 else None,
            "team2_external_id": str(team2["id"]) if team2 else None,
            "winner_external_id": str(winner["id"]) if winner else None,
            "team1_score": team1_score,
            "team2_score": team2_score,
            "best_of": match.get("number_of_games"),
            "status": self._map_status(match.get("status")),
            "scheduled_at": match.get("scheduled_at"),
            "started_at": match.get("begin_at"),
            "ended_at": match.get("end_at"),
            "source": self.source_name,
            "raw_data": match
        }
    
    def _map_status(self, status: str) -> str:
        """Map PandaScore status to our standard status"""
        mapping = {
            "not_started": "upcoming",
            "running": "live",
            "finished": "finished",
            "canceled": "canceled"
        }
        return mapping.get(status, status)
