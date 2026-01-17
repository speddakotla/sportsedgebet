"""
Generate predictions for upcoming matches
"""
import sys
from datetime import datetime
from typing import List, Dict

import numpy as np
import pandas as pd

sys.path.append('..')
from database import Database
from features import FeatureEngineer
from train import PlayerKillsModel, MODELS_DIR


class Predictor:
    """Generate and store predictions"""
    
    def __init__(self):
        self.db = Database()
        self.feature_eng = FeatureEngineer(self.db)
        self.kills_model = None
    
    def load_models(self):
        """Load trained models"""
        try:
            self.kills_model = PlayerKillsModel.load()
            print(f"Loaded kills model: {self.kills_model.version}")
        except FileNotFoundError:
            print("No kills model found - predictions unavailable")
    
    def predict_player_props(self, match_id: str = None) -> List[Dict]:
        """
        Generate predictions for player prop bets
        """
        if not self.kills_model:
            self.load_models()
            if not self.kills_model:
                return []
        
        # Get upcoming props from database
        props = self._get_upcoming_props(match_id)
        
        if not props:
            print("No upcoming props found")
            return []
        
        predictions = []
        
        for prop in props:
            # Generate features
            features = self.feature_eng.get_player_prop_features(
                player_id=prop['player_id'],
                prop_type=prop['prop_type'],
                line=prop['line']
            )
            
            if not features:
                continue
            
            # Convert to DataFrame for model
            df = pd.DataFrame([features])
            X = self.kills_model.scaler.transform(
                df[self.kills_model.feature_columns].fillna(0)
            )
            
            # Get prediction
            pred, proba = self.kills_model.predict(X)
            
            prediction = {
                "match_id": prop.get('match_id'),
                "player_id": prop['player_id'],
                "prediction_type": f"player_{prop['prop_type']}_over",
                "predicted_value": float(proba[0]),  # Probability of over
                "confidence": self._calculate_confidence(proba[0]),
                "model_version": self.kills_model.version,
                "features_used": features
            }
            
            predictions.append(prediction)
            
            # Store prediction in database
            self.db.insert_prediction(prediction)
        
        return predictions
    
    def predict_match_winners(self) -> List[Dict]:
        """
        Generate predictions for match outcomes
        """
        # Get upcoming matches
        matches = self.db.get_upcoming_matches()
        
        predictions = []
        for match in matches:
            # Would use match winner model here
            # Placeholder for now
            pass
        
        return predictions
    
    def _get_upcoming_props(self, match_id: str = None) -> List[Dict]:
        """Get player props to predict"""
        # Query props from database
        query = self.db.client.table("cs2_player_props").select(
            "*, player:cs2_players(*), match:cs2_matches(*)"
        )
        
        if match_id:
            query = query.eq("match_id", match_id)
        
        # Only get props for upcoming matches
        result = query.execute()
        
        return result.data
    
    def _calculate_confidence(self, probability: float) -> float:
        """
        Calculate confidence based on probability distance from 0.5
        Higher distance = higher confidence
        """
        distance = abs(probability - 0.5)
        # Scale to 0-1 range (0.5 distance maps to 1.0 confidence)
        return min(distance * 2, 1.0)
    
    def get_value_bets(self, min_edge: float = 0.05) -> List[Dict]:
        """
        Find bets where our model probability differs from market odds
        """
        predictions = self.predict_player_props()
        
        value_bets = []
        for pred in predictions:
            # Get corresponding odds from market
            odds = self._get_market_odds(pred)
            
            if not odds:
                continue
            
            # Calculate implied probability from market
            market_prob = 1 / odds['over_odds']
            our_prob = pred['predicted_value']
            
            # Calculate edge
            edge = our_prob - market_prob
            
            if edge >= min_edge:
                value_bets.append({
                    **pred,
                    "market_odds": odds['over_odds'],
                    "market_implied_prob": market_prob,
                    "our_probability": our_prob,
                    "edge": edge,
                    "expected_value": (our_prob * odds['over_odds']) - 1
                })
        
        # Sort by edge
        value_bets.sort(key=lambda x: x['edge'], reverse=True)
        
        return value_bets
    
    def _get_market_odds(self, prediction: Dict) -> Dict:
        """Get current market odds for a prediction"""
        result = self.db.client.table("cs2_player_props").select("*").eq(
            "player_id", prediction['player_id']
        ).eq(
            "match_id", prediction['match_id']
        ).order("fetched_at", desc=True).limit(1).execute()
        
        return result.data[0] if result.data else None


def main():
    print(f"Generating predictions at {datetime.now().isoformat()}")
    
    predictor = Predictor()
    predictor.load_models()
    
    # Generate prop predictions
    props = predictor.predict_player_props()
    print(f"Generated {len(props)} prop predictions")
    
    # Find value bets
    value_bets = predictor.get_value_bets(min_edge=0.05)
    print(f"Found {len(value_bets)} potential value bets")
    
    for bet in value_bets[:5]:  # Show top 5
        print(f"\n  Player: {bet.get('player_id')}")
        print(f"  Our Prob: {bet['our_probability']:.2%}")
        print(f"  Market: {bet['market_implied_prob']:.2%}")
        print(f"  Edge: {bet['edge']:.2%}")
        print(f"  EV: {bet['expected_value']:.2%}")


if __name__ == "__main__":
    main()
