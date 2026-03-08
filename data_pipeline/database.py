"""
Database operations for MLB data pipeline
Uses Supabase client for PostgreSQL operations
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from supabase import create_client, Client

from config import SUPABASE_URL, SUPABASE_SERVICE_KEY


class Database:
    """Database operations handler"""
    
    def __init__(self):
        self.client: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    
    # ==================== TEAMS ====================
    def upsert_teams(self, teams: List[dict]) -> tuple[int, int]:
        """Insert or update teams, returns (inserted, updated)"""
        if not teams:
            return 0, 0
        
        # Get existing teams by external_id
        external_ids = [t["external_id"] for t in teams]
        existing = self.client.table("mlb_teams").select("external_id").in_("external_id", external_ids).execute()
        existing_ids = {r["external_id"] for r in existing.data}
        
        inserted = 0
        updated = 0
        
        for team in teams:
            if team["external_id"] in existing_ids:
                self.client.table("mlb_teams").update(team).eq("external_id", team["external_id"]).execute()
                updated += 1
            else:
                self.client.table("mlb_teams").insert(team).execute()
                inserted += 1
        
        return inserted, updated
    
    def get_team_id_mapping(self, external_ids: List[str]) -> Dict[str, str]:
        """Get mapping of external_id -> UUID for teams"""
        if not external_ids:
            return {}
        
        result = self.client.table("mlb_teams").select("id, external_id").in_("external_id", external_ids).execute()
        return {r["external_id"]: r["id"] for r in result.data}
    
    # ==================== PLAYERS ====================
    def upsert_players(self, players: List[dict]) -> tuple[int, int]:
        """Insert or update players"""
        if not players:
            return 0, 0
        
        # Resolve team external IDs to UUIDs
        team_external_ids = [p.get("team_external_id") for p in players if p.get("team_external_id")]
        team_mapping = self.get_team_id_mapping(team_external_ids)
        
        # Get existing players
        external_ids = [p["external_id"] for p in players]
        existing = self.client.table("mlb_players").select("external_id").in_("external_id", external_ids).execute()
        existing_ids = {r["external_id"] for r in existing.data}
        
        inserted = 0
        updated = 0
        
        for player in players:
            # Map team external ID to UUID
            team_ext_id = player.pop("team_external_id", None)
            if team_ext_id and team_ext_id in team_mapping:
                player["team_id"] = team_mapping[team_ext_id]
            
            if player["external_id"] in existing_ids:
                self.client.table("mlb_players").update(player).eq("external_id", player["external_id"]).execute()
                updated += 1
            else:
                self.client.table("mlb_players").insert(player).execute()
                inserted += 1
        
        return inserted, updated
    
    def get_player_id_mapping(self, external_ids: List[str]) -> Dict[str, str]:
        """Get mapping of external_id -> UUID for players"""
        if not external_ids:
            return {}
        
        result = self.client.table("mlb_players").select("id, external_id").in_("external_id", external_ids).execute()
        return {r["external_id"]: r["id"] for r in result.data}
    
    # ==================== GAMES ====================
    def upsert_games(self, games: List[dict]) -> tuple[int, int]:
        """Insert or update games"""
        if not games:
            return 0, 0
        
        # Resolve team external IDs
        team_ext_ids = []
        for g in games:
            if g.get("home_team_external_id"):
                team_ext_ids.append(g["home_team_external_id"])
            if g.get("away_team_external_id"):
                team_ext_ids.append(g["away_team_external_id"])
            if g.get("winner_external_id"):
                team_ext_ids.append(g["winner_external_id"])
        
        team_mapping = self.get_team_id_mapping(list(set(team_ext_ids)))
        
        # Get existing games
        external_ids = [g["external_id"] for g in games]
        existing = self.client.table("mlb_games").select("external_id").in_("external_id", external_ids).execute()
        existing_ids = {r["external_id"] for r in existing.data}
        
        inserted = 0
        updated = 0
        
        for game in games:
            # Map team external IDs to UUIDs
            home_ext = game.pop("home_team_external_id", None)
            away_ext = game.pop("away_team_external_id", None)
            w_ext = game.pop("winner_external_id", None)
            
            if home_ext and home_ext in team_mapping:
                game["home_team_id"] = team_mapping[home_ext]
            if away_ext and away_ext in team_mapping:
                game["away_team_id"] = team_mapping[away_ext]
            if w_ext and w_ext in team_mapping:
                game["winner_id"] = team_mapping[w_ext]
            
            if game["external_id"] in existing_ids:
                self.client.table("mlb_games").update(game).eq("external_id", game["external_id"]).execute()
                updated += 1
            else:
                self.client.table("mlb_games").insert(game).execute()
                inserted += 1
        
        return inserted, updated
    
    def get_game_id_mapping(self, external_ids: List[str]) -> Dict[str, str]:
        """Get mapping of external_id -> UUID for games"""
        if not external_ids:
            return {}
        
        result = self.client.table("mlb_games").select("id, external_id").in_("external_id", external_ids).execute()
        return {r["external_id"]: r["id"] for r in result.data}
    
    # ==================== PLAYER STATS ====================
    def insert_player_stats(self, stats: List[dict]) -> int:
        """Insert player game stats (with conflict handling)"""
        if not stats:
            return 0
        
        # Resolve external IDs
        game_ext_ids = list(set(s["game_external_id"] for s in stats))
        player_ext_ids = list(set(s["player_external_id"] for s in stats))
        team_ext_ids = list(set(s.get("team_external_id") for s in stats if s.get("team_external_id")))
        
        game_mapping = self.get_game_id_mapping(game_ext_ids)
        player_mapping = self.get_player_id_mapping(player_ext_ids)
        team_mapping = self.get_team_id_mapping(team_ext_ids) if team_ext_ids else {}
        
        inserted = 0
        for stat in stats:
            game_ext = stat.pop("game_external_id")
            player_ext = stat.pop("player_external_id")
            team_ext = stat.pop("team_external_id", None)
            
            if game_ext not in game_mapping or player_ext not in player_mapping:
                continue
            
            stat["game_id"] = game_mapping[game_ext]
            stat["player_id"] = player_mapping[player_ext]
            if team_ext and team_ext in team_mapping:
                stat["team_id"] = team_mapping[team_ext]
            
            try:
                self.client.table("mlb_player_stats").upsert(
                    stat, 
                    on_conflict="player_id,game_id"
                ).execute()
                inserted += 1
            except Exception as e:
                print(f"Error inserting stat: {e}")
        
        return inserted
    
    # ==================== ODDS ====================
    def insert_odds(self, odds: List[dict]) -> int:
        """Insert odds data"""
        if not odds:
            return 0
        
        # Resolve game IDs
        game_ext_ids = list(set(o.get("game_external_id") for o in odds if o.get("game_external_id")))
        game_mapping = self.get_game_id_mapping(game_ext_ids)
        
        inserted = 0
        for odd in odds:
            game_ext = odd.pop("game_external_id", None)
            
            if game_ext and game_ext in game_mapping:
                odd["game_id"] = game_mapping[game_ext]
            else:
                # Skip odds without matching game
                continue
            
            try:
                self.client.table("mlb_odds").insert(odd).execute()
                inserted += 1
            except Exception as e:
                print(f"Error inserting odds: {e}")
        
        return inserted
    
    # ==================== LOGGING ====================
    def log_fetch(self, log_data: dict):
        """Log a fetch operation"""
        self.client.table("data_fetch_log").insert(log_data).execute()
    
    # ==================== AGGREGATES ====================
    def update_player_aggregates(self, player_id: str, time_period: str, stats: dict):
        """Update or insert player aggregates"""
        data = {
            "player_id": player_id,
            "time_period": time_period,
            **stats,
            "calculated_at": datetime.utcnow().isoformat()
        }
        
        self.client.table("mlb_player_aggregates").upsert(
            data,
            on_conflict="player_id,time_period"
        ).execute()
    
    # ==================== ML PREDICTIONS ====================
    def insert_prediction(self, prediction: dict) -> str:
        """Insert an ML prediction and return its ID"""
        result = self.client.table("mlb_predictions").insert(prediction).execute()
        return result.data[0]["id"] if result.data else None
    
    def get_player_stats_for_ml(self, player_id: str, limit: int = 20) -> List[dict]:
        """Get recent player stats for ML feature generation"""
        result = self.client.table("mlb_player_stats").select("*").eq(
            "player_id", player_id
        ).order("created_at", desc=True).limit(limit).execute()
        
        return result.data
    
    def get_upcoming_games(self) -> List[dict]:
        """Get upcoming games for predictions"""
        result = self.client.table("mlb_games").select(
            "*, home_team:mlb_teams!home_team_id(*), away_team:mlb_teams!away_team_id(*)"
        ).eq("status", "scheduled").execute()
        
        return result.data
