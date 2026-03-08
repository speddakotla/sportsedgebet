"""
Main data pipeline orchestrator for MLB
Run this script to fetch data from all sources and sync to database
"""
import sys
import argparse
from datetime import datetime, timedelta

from database import Database
from fetchers import MLBStatsFetcher, OddsAPIFetcher
from fetchers.base import FetchResult


def fetch_mlb_stats(db: Database, full_sync: bool = False):
    """Fetch data from MLB Stats API"""
    print("\n=== MLB Stats API Sync ===")
    fetcher = MLBStatsFetcher()
    result = FetchResult()
    
    try:
        # Fetch teams
        print("Fetching teams...")
        teams = fetcher.fetch_teams()
        result.records_fetched += len(teams)
        inserted, updated = db.upsert_teams(teams)
        result.records_inserted += inserted
        result.records_updated += updated
        print(f"  Teams: {inserted} inserted, {updated} updated")
        
        # Fetch players (from all teams)
        print("Fetching players...")
        players = fetcher.fetch_players()  # Fetches from all teams
        result.records_fetched += len(players)
        inserted, updated = db.upsert_players(players)
        result.records_inserted += inserted
        result.records_updated += updated
        print(f"  Players: {inserted} inserted, {updated} updated")
        
        # Fetch upcoming games
        print("Fetching upcoming games...")
        games = fetcher.fetch_upcoming_games(days_ahead=7)
        result.records_fetched += len(games)
        inserted, updated = db.upsert_games(games)
        result.records_inserted += inserted
        result.records_updated += updated
        print(f"  Upcoming games: {inserted} inserted, {updated} updated")
        
        # Fetch live games
        print("Fetching live games...")
        live_games = fetcher.fetch_live_games()
        result.records_fetched += len(live_games)
        inserted, updated = db.upsert_games(live_games)
        result.records_inserted += inserted
        result.records_updated += updated
        print(f"  Live games: {inserted} inserted, {updated} updated")
        
        # Full sync: also fetch historical data
        if full_sync:
            print("Fetching historical games (full sync)...")
            # Fetch last 30 days of completed games
            end_date = datetime.now() - timedelta(days=1)
            start_date = end_date - timedelta(days=30)
            
            past_games = fetcher.fetch_past_games(
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d")
            )
            result.records_fetched += len(past_games)
            inserted, updated = db.upsert_games(past_games)
            result.records_inserted += inserted
            result.records_updated += updated
            print(f"  Historical games: {inserted} inserted, {updated} updated")
        
        db.log_fetch(result.to_log_dict("mlb_stats", "full_sync" if full_sync else "regular"))
        
    except Exception as e:
        result.status = "error"
        result.error_message = str(e)
        db.log_fetch(result.to_log_dict("mlb_stats", "error"))
        print(f"  ERROR: {e}")
    
    finally:
        fetcher.close()
    
    return result


def fetch_odds(db: Database):
    """Fetch odds data from The Odds API"""
    print("\n=== Odds API Sync ===")
    fetcher = OddsAPIFetcher()
    result = FetchResult()
    
    try:
        # Fetch MLB odds (moneyline, spreads, totals)
        print("Fetching MLB odds...")
        odds = fetcher.fetch_mlb_odds(regions=["us"], markets=["h2h", "spreads", "totals"])
        result.records_fetched += len(odds)
        inserted = db.insert_odds(odds)
        result.records_inserted += inserted
        print(f"  Odds: {inserted} inserted")
        
        # Try to fetch player props (may require premium subscription)
        print("Fetching player props...")
        try:
            props = fetcher.fetch_player_props()
            # Note: Player props would need additional processing to match with players
            print(f"  Player props fetched: {len(props)} (may require premium API)")
        except Exception as e:
            print(f"  Player props not available: {e}")
        
        db.log_fetch(result.to_log_dict("odds_api", "regular"))
        
    except Exception as e:
        result.status = "error"
        result.error_message = str(e)
        db.log_fetch(result.to_log_dict("odds_api", "error"))
        print(f"  ERROR: {e}")
    
    finally:
        fetcher.close()
    
    return result


def main():
    parser = argparse.ArgumentParser(description="MLB Data Pipeline")
    parser.add_argument("--full-sync", action="store_true", help="Perform full historical sync")
    parser.add_argument("--source", choices=["all", "mlb_stats", "odds"], default="all")
    args = parser.parse_args()
    
    print(f"Starting MLB data pipeline at {datetime.now().isoformat()}")
    print(f"Mode: {'Full Sync' if args.full_sync else 'Regular Sync'}")
    
    db = Database()
    
    if args.source in ["all", "mlb_stats"]:
        fetch_mlb_stats(db, full_sync=args.full_sync)
    
    if args.source in ["all", "odds"]:
        fetch_odds(db)
    
    print(f"\nPipeline completed at {datetime.now().isoformat()}")


if __name__ == "__main__":
    main()
