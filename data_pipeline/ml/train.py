"""
ML Model Training for CS2 Predictions
"""
import os
import sys
import argparse
import pickle
from datetime import datetime
from pathlib import Path

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier

sys.path.append('..')
from database import Database
from features import FeatureEngineer


# Model directory
MODELS_DIR = Path(__file__).parent / "models"
MODELS_DIR.mkdir(exist_ok=True)


class PlayerKillsModel:
    """
    Predict if a player will go over/under a kills line
    """
    
    def __init__(self):
        self.model = XGBClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            objective='binary:logistic',
            random_state=42
        )
        self.scaler = StandardScaler()
        self.feature_columns = [
            'last5_avg_kills', 'last10_avg_kills',
            'kills_std', 'kills_trend', 'kd_ratio',
            'line', 'line_vs_avg', 'matches_count'
        ]
        self.version = f"kills_v{datetime.now().strftime('%Y%m%d')}"
    
    def prepare_features(self, df: pd.DataFrame) -> np.ndarray:
        """Extract and scale features"""
        X = df[self.feature_columns].fillna(0)
        return self.scaler.fit_transform(X)
    
    def train(self, X: np.ndarray, y: np.ndarray):
        """Train the model"""
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        self.model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = self.model.predict(X_test)
        y_proba = self.model.predict_proba(X_test)[:, 1]
        
        metrics = {
            "accuracy": accuracy_score(y_test, y_pred),
            "precision": precision_score(y_test, y_pred),
            "recall": recall_score(y_test, y_pred),
            "roc_auc": roc_auc_score(y_test, y_proba),
        }
        
        print(f"Model Performance:")
        for metric, value in metrics.items():
            print(f"  {metric}: {value:.4f}")
        
        # Cross-validation
        cv_scores = cross_val_score(self.model, X, y, cv=5, scoring='roc_auc')
        print(f"  CV ROC-AUC: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")
        
        return metrics
    
    def predict(self, X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Return predictions and probabilities"""
        preds = self.model.predict(X)
        probas = self.model.predict_proba(X)[:, 1]
        return preds, probas
    
    def save(self, path: Path = None):
        """Save model to disk"""
        if path is None:
            path = MODELS_DIR / f"{self.version}.pkl"
        
        with open(path, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'scaler': self.scaler,
                'feature_columns': self.feature_columns,
                'version': self.version
            }, f)
        
        print(f"Model saved to {path}")
    
    @classmethod
    def load(cls, path: Path = None):
        """Load model from disk"""
        if path is None:
            # Load latest model
            models = list(MODELS_DIR.glob("kills_v*.pkl"))
            if not models:
                raise FileNotFoundError("No trained models found")
            path = max(models, key=lambda p: p.stem)
        
        with open(path, 'rb') as f:
            data = pickle.load(f)
        
        instance = cls()
        instance.model = data['model']
        instance.scaler = data['scaler']
        instance.feature_columns = data['feature_columns']
        instance.version = data['version']
        
        return instance


class MatchWinnerModel:
    """
    Predict match winner probabilities
    """
    
    def __init__(self):
        self.model = LGBMClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            objective='binary',
            random_state=42
        )
        self.scaler = StandardScaler()
        self.version = f"match_v{datetime.now().strftime('%Y%m%d')}"
    
    # Similar structure to PlayerKillsModel...
    # Would include team-level features


def build_training_dataset(db: Database, feature_eng: FeatureEngineer) -> pd.DataFrame:
    """
    Build training dataset from historical data
    """
    print("Building training dataset...")
    
    # Get completed matches with player stats
    # This would need to:
    # 1. Query historical matches
    # 2. Get player stats for each match
    # 3. Get the betting lines that were available
    # 4. Create labels (did they go over/under?)
    
    # Placeholder - in production, this queries real data
    # For now, return empty DataFrame with expected columns
    
    columns = [
        'player_id', 'match_id', 'line',
        'last5_avg_kills', 'last10_avg_kills',
        'kills_std', 'kills_trend', 'kd_ratio',
        'line_vs_avg', 'matches_count',
        'actual_kills', 'went_over'  # Labels
    ]
    
    return pd.DataFrame(columns=columns)


def main():
    parser = argparse.ArgumentParser(description="Train CS2 ML Models")
    parser.add_argument("--save-model", action="store_true", help="Save trained model")
    parser.add_argument("--model", choices=["kills", "match", "all"], default="all")
    args = parser.parse_args()
    
    print(f"Starting model training at {datetime.now().isoformat()}")
    
    db = Database()
    feature_eng = FeatureEngineer(db)
    
    # Build training data
    df = build_training_dataset(db, feature_eng)
    
    if len(df) < 100:
        print("Insufficient training data. Need at least 100 samples.")
        print("Make sure to run the data pipeline first to collect historical data.")
        return
    
    if args.model in ["kills", "all"]:
        print("\n=== Training Player Kills Model ===")
        model = PlayerKillsModel()
        
        X = model.prepare_features(df)
        y = df['went_over'].values
        
        metrics = model.train(X, y)
        
        if args.save_model:
            model.save()
    
    if args.model in ["match", "all"]:
        print("\n=== Training Match Winner Model ===")
        # Similar training for match model
        pass
    
    print(f"\nTraining completed at {datetime.now().isoformat()}")


if __name__ == "__main__":
    main()
