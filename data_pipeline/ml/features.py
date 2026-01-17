"""
Feature engineering for CS2 ML models
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime, timedelta


class FeatureEngineer:
    """Generate features for CS2 predictions"""
    
    def __init__(self, db):
        self.db = db
    
    def get_player_features(self, player_id: str, as_of_date: datetime = None) -> Dict:
        """
        Generate features for a player's predicted performance
        """
        stats = self.db.get_player_stats_for_ml(player_id, limit=30)
        
        if not stats:
            return None
        
        df = pd.DataFrame(stats)
        
        # Basic stats
        features = {
            "player_id": player_id,
            # Recent form (last 5 matches)
            "last5_avg_kills": df.head(5)["kills"].mean(),
            "last5_avg_deaths": df.head(5)["deaths"].mean(),
            "last5_avg_rating": df.head(5)["rating"].mean() if "rating" in df else None,
            "last5_avg_adr": df.head(5)["adr"].mean() if "adr" in df else None,
            
            # Medium term (last 10 matches)
            "last10_avg_kills": df.head(10)["kills"].mean(),
            "last10_avg_deaths": df.head(10)["deaths"].mean(),
            "last10_avg_rating": df.head(10)["rating"].mean() if "rating" in df else None,
            
            # Volatility (standard deviation)
            "kills_std": df.head(10)["kills"].std(),
            "rating_std": df.head(10)["rating"].std() if "rating" in df else None,
            
            # Trend (are they improving?)
            "kills_trend": self._calculate_trend(df.head(10)["kills"]),
            
            # Consistency
            "matches_count": len(df),
            
            # K/D ratio
            "kd_ratio": df.head(10)["kills"].sum() / max(df.head(10)["deaths"].sum(), 1),
        }
        
        # Headshot percentage if available
        if "headshot_percentage" in df.columns:
            features["avg_hs_pct"] = df.head(10)["headshot_percentage"].mean()
        
        return features
    
    def get_match_features(self, team1_id: str, team2_id: str, match_id: str = None) -> Dict:
        """
        Generate features for match prediction
        """
        # Get players for each team
        # This would need team roster info
        
        features = {
            "match_id": match_id,
            "team1_id": team1_id,
            "team2_id": team2_id,
            # Team-level features would go here
            # - Team win rate
            # - Head-to-head record
            # - Recent form
            # - Map pool strength
        }
        
        return features
    
    def get_player_prop_features(
        self, 
        player_id: str, 
        prop_type: str,  # 'kills', 'deaths', 'assists'
        line: float,
        opponent_team_id: str = None
    ) -> Dict:
        """
        Generate features for player prop predictions (over/under)
        """
        base_features = self.get_player_features(player_id)
        
        if not base_features:
            return None
        
        # Add prop-specific features
        features = {
            **base_features,
            "prop_type": prop_type,
            "line": line,
            "line_vs_avg": line - base_features.get(f"last10_avg_{prop_type}", line),
        }
        
        # Calculate historical over/under rate
        stats = self.db.get_player_stats_for_ml(player_id, limit=20)
        if stats and prop_type in pd.DataFrame(stats).columns:
            df = pd.DataFrame(stats)
            features["historical_over_rate"] = (df[prop_type] > line).mean()
        
        return features
    
    def _calculate_trend(self, series: pd.Series) -> float:
        """
        Calculate linear trend coefficient
        Positive = improving, Negative = declining
        """
        if len(series) < 3:
            return 0
        
        x = np.arange(len(series))
        # Reverse so recent games have higher x
        y = series.values[::-1]
        
        try:
            slope, _ = np.polyfit(x, y, 1)
            return slope
        except:
            return 0
    
    def prepare_training_data(self, prop_type: str = "kills") -> pd.DataFrame:
        """
        Prepare training dataset from historical data
        """
        # This would query historical matches and their outcomes
        # to create labeled training data
        
        # Placeholder structure:
        # - Features: player stats before each match
        # - Labels: actual result (over/under the line)
        
        pass


class FeatureStore:
    """
    Cache computed features for efficiency
    """
    
    def __init__(self):
        self.cache = {}
    
    def get(self, key: str) -> Optional[Dict]:
        """Get cached features"""
        return self.cache.get(key)
    
    def set(self, key: str, features: Dict, ttl_minutes: int = 30):
        """Cache features with TTL"""
        self.cache[key] = {
            "features": features,
            "expires_at": datetime.now() + timedelta(minutes=ttl_minutes)
        }
    
    def clear_expired(self):
        """Remove expired cache entries"""
        now = datetime.now()
        self.cache = {
            k: v for k, v in self.cache.items() 
            if v["expires_at"] > now
        }
