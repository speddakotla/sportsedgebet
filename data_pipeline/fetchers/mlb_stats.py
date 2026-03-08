"""
MLB Stats API Fetcher
Official MLB Stats API - Free, no API key required
Docs: https://statsapi.mlb.com/api/docs
"""
from typing import List, Optional
from datetime import datetime, timedelta
from .base import BaseFetcher, FetchResult

import sys
sys.path.append('..')
from config import MLB_STATS_BASE_URL, MLB_SEASON


class MLBStatsFetcher(BaseFetcher):
    """Fetcher for MLB Stats API data"""
    
    def __init__(self):
        super().__init__(
            base_url=MLB_STATS_BASE_URL,
            api_key=None,  # MLB Stats API is free, no key needed
            source_name="mlb_stats"
        )
        self.season = MLB_SEASON
    
    def _get_auth_headers(self) -> dict:
        return {}
    
    def fetch_teams(self) -> List[dict]:
        """Fetch all MLB teams"""
        endpoint = "/teams"
        params = {
            "sportId": 1,  # MLB
            "season": self.season
        }
        
        data = self._make_request(endpoint, params=params)
        
        teams = []
        for team_data in data.get("teams", []):
            venue = team_data.get("venue", {})
            division = team_data.get("division", {})
            league = team_data.get("league", {})
            
            teams.append({
                "external_id": str(team_data["id"]),
                "name": team_data["name"],
                "abbreviation": team_data.get("abbreviation"),
                "city": team_data.get("locationName"),
                "venue_name": venue.get("name"),
                "venue_city": venue.get("city"),
                "division": division.get("name"),
                "league": league.get("name"),
                "logo_url": None,  # Would need to construct from team ID
                "source": self.source_name
            })
        
        return teams
    
    def fetch_players(self, team_id: Optional[int] = None) -> List[dict]:
        """Fetch MLB players (optionally filtered by team)"""
        if team_id:
            endpoint = f"/teams/{team_id}/roster"
        else:
            # Fetch all players by getting rosters for all teams
            teams = self.fetch_teams()
            all_players = []
            for team in teams[:30]:  # Limit to avoid too many requests
                try:
                    players = self.fetch_players(int(team["external_id"]))
                    all_players.extend(players)
                except Exception as e:
                    print(f"Error fetching players for team {team['name']}: {e}")
                    continue
            return all_players
        
        params = {"rosterType": "active"}
        data = self._make_request(endpoint, params=params)
        
        players = []
        for player_data in data.get("roster", []):
            person = player_data.get("person", {})
            position = player_data.get("position", {})
            
            players.append({
                "external_id": str(person["id"]),
                "first_name": person.get("firstName", ""),
                "last_name": person.get("lastName", ""),
                "full_name": person.get("fullName", ""),
                "team_external_id": str(team_id) if team_id else None,
                "position": position.get("abbreviation"),
                "jersey_number": person.get("primaryNumber"),
                "birth_date": person.get("birthDate"),
                "bats": person.get("batSide", {}).get("code"),
                "throws": person.get("pitchHand", {}).get("code"),
                "image_url": None,  # Would need to construct from player ID
                "source": self.source_name
            })
        
        return players
    
    def fetch_upcoming_games(self, days_ahead: int = 7) -> List[dict]:
        """Fetch upcoming MLB games"""
        start_date = datetime.now().strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
        
        endpoint = "/schedule"
        params = {
            "sportId": 1,
            "startDate": start_date,
            "endDate": end_date,
            "hydrate": "team,linescore,venue"
        }
        
        data = self._make_request(endpoint, params=params)
        
        games = []
        for date_data in data.get("dates", []):
            for game_data in date_data.get("games", []):
                if game_data.get("status", {}).get("abstractGameState") == "Preview":
                    games.append(self._parse_game(game_data))
        
        return games
    
    def fetch_live_games(self) -> List[dict]:
        """Fetch currently live MLB games"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        endpoint = "/schedule"
        params = {
            "sportId": 1,
            "date": today,
            "hydrate": "team,linescore,venue"
        }
        
        data = self._make_request(endpoint, params=params)
        
        games = []
        for date_data in data.get("dates", []):
            for game_data in date_data.get("games", []):
                status = game_data.get("status", {})
                if status.get("abstractGameState") == "Live":
                    games.append(self._parse_game(game_data))
        
        return games
    
    def fetch_past_games(self, start_date: str, end_date: str) -> List[dict]:
        """Fetch completed MLB games for historical data"""
        endpoint = "/schedule"
        params = {
            "sportId": 1,
            "startDate": start_date,
            "endDate": end_date,
            "hydrate": "team,linescore,venue"
        }
        
        data = self._make_request(endpoint, params=params)
        
        games = []
        for date_data in data.get("dates", []):
            for game_data in date_data.get("games", []):
                status = game_data.get("status", {})
                if status.get("abstractGameState") == "Final":
                    games.append(self._parse_game(game_data))
        
        return games
    
    def fetch_game_stats(self, game_id: int) -> List[dict]:
        """Fetch player stats for a specific game"""
        endpoint = f"/game/{game_id}/boxscore"
        
        try:
            data = self._make_request(endpoint)
        except Exception as e:
            print(f"Error fetching game stats: {e}")
            return []
        
        stats = []
        
        # Process home team stats
        home_team_id = data.get("teams", {}).get("home", {}).get("team", {}).get("id")
        home_players = data.get("teams", {}).get("home", {}).get("players", {})
        
        # Process away team stats
        away_team_id = data.get("teams", {}).get("away", {}).get("team", {}).get("id")
        away_players = data.get("teams", {}).get("away", {}).get("players", {})
        
        # Combine and process all players
        all_players = {**home_players, **away_players}
        
        for player_id, player_data in all_players.items():
            if not player_id.startswith("ID"):  # Skip non-player entries
                continue
            
            person = player_data.get("person", {})
            stats_data = player_data.get("stats", {})
            batting = stats_data.get("batting", {})
            pitching = stats_data.get("pitching", {})
            
            # Determine team
            team_id = home_team_id if player_id in home_players else away_team_id
            
            stat_entry = {
                "game_external_id": str(game_id),
                "player_external_id": str(person.get("id")),
                "team_external_id": str(team_id) if team_id else None,
            }
            
            # Add batting stats if available
            if batting:
                stat_entry.update({
                    "at_bats": batting.get("atBats", 0),
                    "hits": batting.get("hits", 0),
                    "runs": batting.get("runs", 0),
                    "rbis": batting.get("rbi", 0),
                    "home_runs": batting.get("homeRuns", 0),
                    "doubles": batting.get("doubles", 0),
                    "triples": batting.get("triples", 0),
                    "walks": batting.get("baseOnBalls", 0),
                    "strikeouts": batting.get("strikeOuts", 0),
                    "stolen_bases": batting.get("stolenBases", 0),
                    "batting_average": batting.get("avg"),
                    "on_base_pct": batting.get("obp"),
                    "slugging_pct": batting.get("slg"),
                })
            
            # Add pitching stats if available
            if pitching:
                stat_entry.update({
                    "innings_pitched": pitching.get("inningsPitched"),
                    "earned_runs": pitching.get("earnedRuns", 0),
                    "hits_allowed": pitching.get("hits", 0),
                    "walks_allowed": pitching.get("baseOnBalls", 0),
                    "strikeouts_thrown": pitching.get("strikeOuts", 0),
                    "home_runs_allowed": pitching.get("homeRuns", 0),
                    "era": pitching.get("era"),
                    "whip": pitching.get("whip"),
                })
            
            if batting or pitching:  # Only add if there are stats
                stat_entry["source"] = self.source_name
                stat_entry["raw_data"] = player_data
                stats.append(stat_entry)
        
        return stats
    
    def _parse_game(self, game_data: dict) -> dict:
        """Parse game data into standard format"""
        teams = game_data.get("teams", {})
        home_team = teams.get("home", {}).get("team", {})
        away_team = teams.get("away", {}).get("team", {})
        
        linescore = game_data.get("linescore", {})
        home_score = linescore.get("home", {}).get("runs")
        away_score = linescore.get("away", {}).get("runs")
        
        status = game_data.get("status", {})
        detailed_state = status.get("detailedState")
        abstract_state = status.get("abstractGameState")
        
        # Map abstract state to our status
        status_mapping = {
            "Preview": "scheduled",
            "Live": "live",
            "Final": "final",
            "Delayed": "postponed",
            "Cancelled": "canceled"
        }
        
        game_status = status_mapping.get(abstract_state, "scheduled")
        
        # Determine winner
        winner_id = None
        if abstract_state == "Final" and home_score is not None and away_score is not None:
            if home_score > away_score:
                winner_id = str(home_team.get("id"))
            elif away_score > home_score:
                winner_id = str(away_team.get("id"))
        
        venue = game_data.get("venue", {})
        
        return {
            "external_id": str(game_data["gamePk"]),
            "game_date": game_data.get("gameDate", "").split("T")[0],
            "game_type": game_data.get("gameType"),
            "home_team_external_id": str(home_team.get("id")),
            "away_team_external_id": str(away_team.get("id")),
            "winner_external_id": winner_id,
            "home_score": home_score,
            "away_score": away_score,
            "status": game_status,
            "detailed_state": detailed_state,
            "scheduled_at": game_data.get("gameDate"),
            "venue": venue.get("name"),
            "source": self.source_name,
            "raw_data": game_data
        }
