"""
Abios Gaming API Fetcher
Docs: https://docs.abiosgaming.com/
"""
from typing import List, Optional
from datetime import datetime
from .base import BaseFetcher, FetchResult

import sys
sys.path.append('..')
from config import ABIOS_BASE_URL, ABIOS_CLIENT_ID, ABIOS_CLIENT_SECRET, CS2_GAME_IDS


class AbiosFetcher(BaseFetcher):
    """Fetcher for Abios Gaming CS2 data"""
    
    def __init__(self):
        super().__init__(
            base_url=ABIOS_BASE_URL,
            api_key=None,  # Uses OAuth
            source_name="abios"
        )
        self.game_id = CS2_GAME_IDS["abios"]
        self.access_token = None
        self._authenticate()
    
    def _authenticate(self):
        """Get OAuth access token"""
        import httpx
        
        auth_url = "https://api.abiosgaming.com/v3/oauth/access_token"
        response = httpx.post(auth_url, data={
            "grant_type": "client_credentials",
            "client_id": ABIOS_CLIENT_ID,
            "client_secret": ABIOS_CLIENT_SECRET
        })
        response.raise_for_status()
        self.access_token = response.json()["access_token"]
    
    def _get_auth_headers(self) -> dict:
        return {"Authorization": f"Bearer {self.access_token}"}
    
    def fetch_teams(self, page: int = 1) -> List[dict]:
        """Fetch CS2 teams"""
        endpoint = "/teams"
        params = {
            "filter[game_id]": self.game_id,
            "page": page,
            "per_page": 50
        }
        
        data = self._make_request(endpoint, params=params)
        
        return [{
            "external_id": f"abios_{team['id']}",
            "name": team["name"],
            "slug": team.get("short_name"),
            "logo_url": team.get("images", {}).get("default"),
            "country": team.get("country", {}).get("name"),
            "source": self.source_name
        } for team in data.get("data", [])]
    
    def fetch_players(self, page: int = 1) -> List[dict]:
        """Fetch CS2 players"""
        endpoint = "/players"
        params = {
            "filter[game_id]": self.game_id,
            "page": page,
            "per_page": 50
        }
        
        data = self._make_request(endpoint, params=params)
        
        return [{
            "external_id": f"abios_{player['id']}",
            "name": player["nick_name"],
            "real_name": f"{player.get('first_name', '')} {player.get('last_name', '')}".strip() or None,
            "team_external_id": f"abios_{player['team']['id']}" if player.get("team") else None,
            "country": player.get("country", {}).get("name"),
            "image_url": player.get("images", {}).get("default"),
            "source": self.source_name
        } for player in data.get("data", [])]
    
    def fetch_matches(self, status: str = "upcoming", page: int = 1) -> List[dict]:
        """
        Fetch CS2 matches
        status: 'upcoming', 'live', 'recent'
        """
        endpoint = "/series"
        params = {
            "filter[game_id]": self.game_id,
            "page": page,
            "per_page": 50
        }
        
        # Add status filter
        if status == "upcoming":
            params["filter[lifecycle]"] = "upcoming"
        elif status == "live":
            params["filter[lifecycle]"] = "live"
        elif status == "recent":
            params["filter[lifecycle]"] = "over"
        
        data = self._make_request(endpoint, params=params)
        
        return [self._parse_series(series) for series in data.get("data", [])]
    
    def fetch_player_stats(self, series_id: int) -> List[dict]:
        """Fetch detailed player stats for a series/match"""
        endpoint = f"/series/{series_id}/players/stats"
        
        try:
            data = self._make_request(endpoint)
        except Exception:
            return []
        
        stats = []
        for player_stat in data.get("data", []):
            stats.append({
                "match_external_id": f"abios_{series_id}",
                "player_external_id": f"abios_{player_stat['player']['id']}",
                "kills": player_stat.get("kills"),
                "deaths": player_stat.get("deaths"),
                "assists": player_stat.get("assists"),
                "headshots": player_stat.get("headshots"),
                "adr": player_stat.get("adr"),
                "rating": player_stat.get("rating"),
                "source": self.source_name,
                "raw_data": player_stat
            })
        
        return stats
    
    def _parse_series(self, series: dict) -> dict:
        """Parse series/match data into standard format"""
        rosters = series.get("rosters", [])
        team1 = rosters[0].get("team") if len(rosters) > 0 else None
        team2 = rosters[1].get("team") if len(rosters) > 1 else None
        
        scores = series.get("scores", {})
        
        # Determine winner
        winner_id = None
        if series.get("lifecycle") == "over" and scores:
            if scores.get(str(team1["id"]), 0) > scores.get(str(team2["id"]), 0):
                winner_id = team1["id"]
            elif scores.get(str(team2["id"]), 0) > scores.get(str(team1["id"]), 0):
                winner_id = team2["id"]
        
        return {
            "external_id": f"abios_{series['id']}",
            "tournament_name": series.get("tournament", {}).get("title"),
            "tournament_id": str(series.get("tournament", {}).get("id")),
            "team1_external_id": f"abios_{team1['id']}" if team1 else None,
            "team2_external_id": f"abios_{team2['id']}" if team2 else None,
            "winner_external_id": f"abios_{winner_id}" if winner_id else None,
            "team1_score": scores.get(str(team1["id"])) if team1 else None,
            "team2_score": scores.get(str(team2["id"])) if team2 else None,
            "best_of": series.get("format", {}).get("best_of"),
            "status": self._map_status(series.get("lifecycle")),
            "scheduled_at": series.get("start"),
            "ended_at": series.get("end"),
            "source": self.source_name,
            "raw_data": series
        }
    
    def _map_status(self, lifecycle: str) -> str:
        """Map Abios lifecycle to our standard status"""
        mapping = {
            "upcoming": "upcoming",
            "live": "live",
            "over": "finished",
            "deleted": "canceled"
        }
        return mapping.get(lifecycle, lifecycle)
