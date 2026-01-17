"""
Database operations for CS2 data pipeline
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
        existing = self.client.table("cs2_teams").select("external_id").in_("external_id", external_ids).execute()
        existing_ids = {r["external_id"] for r in existing.data}
        
        inserted = 0
        updated = 0
        
        for team in teams:
            if team["external_id"] in existing_ids:
                self.client.table("cs2_teams").update(team).eq("external_id", team["external_id"]).execute()
                updated += 1
            else:
                self.client.table("cs2_teams").insert(team).execute()
                inserted += 1
        
        return inserted, updated
    
    def get_team_id_mapping(self, external_ids: List[str]) -> Dict[str, str]:
        """Get mapping of external_id -> UUID for teams"""
        if not external_ids:
            return {}
        
        result = self.client.table("cs2_teams").select("id, external_id").in_("external_id", external_ids).execute()
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
        existing = self.client.table("cs2_players").select("external_id").in_("external_id", external_ids).execute()
        existing_ids = {r["external_id"] for r in existing.data}
        
        inserted = 0
        updated = 0
        
        for player in players:
            # Map team external ID to UUID
            team_ext_id = player.pop("team_external_id", None)
            if team_ext_id and team_ext_id in team_mapping:
                player["team_id"] = team_mapping[team_ext_id]
            
            if player["external_id"] in existing_ids:
                self.client.table("cs2_players").update(player).eq("external_id", player["external_id"]).execute()
                updated += 1
            else:
                self.client.table("cs2_players").insert(player).execute()
                inserted += 1
        
        return inserted, updated
    
    def get_player_id_mapping(self, external_ids: List[str]) -> Dict[str, str]:
        """Get mapping of external_id -> UUID for players"""
        if not external_ids:
            return {}
        
        result = self.client.table("cs2_players").select("id, external_id").in_("external_id", external_ids).execute()
        return {r["external_id"]: r["id"] for r in result.data}
    
    # ==================== MATCHES ====================
    def upsert_matches(self, matches: List[dict]) -> tuple[int, int]:
        """Insert or update matches"""
        if not matches:
            return 0, 0
        
        # Resolve team external IDs
        team_ext_ids = []
        for m in matches:
            if m.get("team1_external_id"):
                team_ext_ids.append(m["team1_external_id"])
            if m.get("team2_external_id"):
                team_ext_ids.append(m["team2_external_id"])
            if m.get("winner_external_id"):
                team_ext_ids.append(m["winner_external_id"])
        
        team_mapping = self.get_team_id_mapping(list(set(team_ext_ids)))
        
        # Get existing matches
        external_ids = [m["external_id"] for m in matches]
        existing = self.client.table("cs2_matches").select("external_id").in_("external_id", external_ids).execute()
        existing_ids = {r["external_id"] for r in existing.data}
        
        inserted = 0
        updated = 0
        
        for match in matches:
            # Map team external IDs to UUIDs
            t1_ext = match.pop("team1_external_id", None)
            t2_ext = match.pop("team2_external_id", None)
            w_ext = match.pop("winner_external_id", None)
            
            if t1_ext and t1_ext in team_mapping:
                match["team1_id"] = team_mapping[t1_ext]
            if t2_ext and t2_ext in team_mapping:
                match["team2_id"] = team_mapping[t2_ext]
            if w_ext and w_ext in team_mapping:
                match["winner_id"] = team_mapping[w_ext]
            
            if match["external_id"] in existing_ids:
                self.client.table("cs2_matches").update(match).eq("external_id", match["external_id"]).execute()
                updated += 1
            else:
                self.client.table("cs2_matches").insert(match).execute()
                inserted += 1
        
        return inserted, updated
    
    def get_match_id_mapping(self, external_ids: List[str]) -> Dict[str, str]:
        """Get mapping of external_id -> UUID for matches"""
        if not external_ids:
            return {}
        
        result = self.client.table("cs2_matches").select("id, external_id").in_("external_id", external_ids).execute()
        return {r["external_id"]: r["id"] for r in result.data}
    
    # ==================== PLAYER STATS ====================
    def insert_player_stats(self, stats: List[dict]) -> int:
        """Insert player match stats (with conflict handling)"""
        if not stats:
            return 0
        
        # Resolve external IDs
        match_ext_ids = list(set(s["match_external_id"] for s in stats))
        player_ext_ids = list(set(s["player_external_id"] for s in stats))
        
        match_mapping = self.get_match_id_mapping(match_ext_ids)
        player_mapping = self.get_player_id_mapping(player_ext_ids)
        
        inserted = 0
        for stat in stats:
            match_ext = stat.pop("match_external_id")
            player_ext = stat.pop("player_external_id")
            
            if match_ext not in match_mapping or player_ext not in player_mapping:
                continue
            
            stat["match_id"] = match_mapping[match_ext]
            stat["player_id"] = player_mapping[player_ext]
            
            try:
                self.client.table("cs2_player_stats").upsert(
                    stat, 
                    on_conflict="player_id,match_id,map_name"
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
        
        # Resolve match IDs
        match_ext_ids = list(set(o.get("match_external_id") for o in odds if o.get("match_external_id")))
        match_mapping = self.get_match_id_mapping(match_ext_ids)
        
        inserted = 0
        for odd in odds:
            match_ext = odd.pop("match_external_id", None)
            
            if match_ext and match_ext in match_mapping:
                odd["match_id"] = match_mapping[match_ext]
            else:
                # Skip odds without matching match
                continue
            
            # Remove non-column fields
            odd.pop("team1_name", None)
            odd.pop("team2_name", None)
            odd.pop("scheduled_at", None)
            
            try:
                self.client.table("cs2_odds").insert(odd).execute()
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
        
        self.client.table("cs2_player_aggregates").upsert(
            data,
            on_conflict="player_id,time_period"
        ).execute()
    
    # ==================== ML PREDICTIONS ====================
    def insert_prediction(self, prediction: dict) -> str:
        """Insert an ML prediction and return its ID"""
        result = self.client.table("cs2_predictions").insert(prediction).execute()
        return result.data[0]["id"] if result.data else None
    
    def get_player_stats_for_ml(self, player_id: str, limit: int = 20) -> List[dict]:
        """Get recent player stats for ML feature generation"""
        result = self.client.table("cs2_player_stats").select("*").eq(
            "player_id", player_id
        ).order("created_at", desc=True).limit(limit).execute()
        
        return result.data
    
    def get_upcoming_matches(self) -> List[dict]:
        """Get upcoming matches for predictions"""
        result = self.client.table("cs2_matches").select(
            "*, team1:cs2_teams!team1_id(*), team2:cs2_teams!team2_id(*)"
        ).eq("status", "upcoming").execute()
        
        return result.data
