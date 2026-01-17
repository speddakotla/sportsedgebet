"""
Main data pipeline orchestrator
Run this script to fetch data from all sources and sync to database
"""
import sys
import argparse
from datetime import datetime

from database import Database
from fetchers import PandaScoreFetcher, AbiosFetcher, OddsPapiFetcher
from fetchers.base import FetchResult


def fetch_pandascore(db: Database, full_sync: bool = False):
    """Fetch data from PandaScore"""
    print("\n=== PandaScore Sync ===")
    fetcher = PandaScoreFetcher()
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
        
        # Fetch players
        print("Fetching players...")
        players = fetcher.fetch_players()
        result.records_fetched += len(players)
        inserted, updated = db.upsert_players(players)
        result.records_inserted += inserted
        result.records_updated += updated
        print(f"  Players: {inserted} inserted, {updated} updated")
        
        # Fetch upcoming matches
        print("Fetching upcoming matches...")
        matches = fetcher.fetch_upcoming_matches()
        result.records_fetched += len(matches)
        inserted, updated = db.upsert_matches(matches)
        result.records_inserted += inserted
        result.records_updated += updated
        print(f"  Upcoming matches: {inserted} inserted, {updated} updated")
        
        # Fetch live matches
        print("Fetching live matches...")
        live_matches = fetcher.fetch_running_matches()
        result.records_fetched += len(live_matches)
        inserted, updated = db.upsert_matches(live_matches)
        result.records_inserted += inserted
        result.records_updated += updated
        print(f"  Live matches: {inserted} inserted, {updated} updated")
        
        # Full sync: also fetch historical data
        if full_sync:
            print("Fetching historical matches (full sync)...")
            for page in range(1, 6):  # Fetch 5 pages of history
                past_matches = fetcher.fetch_past_matches(page=page)
                if not past_matches:
                    break
                result.records_fetched += len(past_matches)
                inserted, updated = db.upsert_matches(past_matches)
                result.records_inserted += inserted
                result.records_updated += updated
                print(f"    Page {page}: {inserted} inserted, {updated} updated")
        
        db.log_fetch(result.to_log_dict("pandascore", "full_sync" if full_sync else "regular"))
        
    except Exception as e:
        result.status = "error"
        result.error_message = str(e)
        db.log_fetch(result.to_log_dict("pandascore", "error"))
        print(f"  ERROR: {e}")
    
    finally:
        fetcher.close()
    
    return result


def fetch_abios(db: Database, full_sync: bool = False):
    """Fetch data from Abios"""
    print("\n=== Abios Sync ===")
    fetcher = AbiosFetcher()
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
        
        # Fetch players
        print("Fetching players...")
        players = fetcher.fetch_players()
        result.records_fetched += len(players)
        inserted, updated = db.upsert_players(players)
        result.records_inserted += inserted
        result.records_updated += updated
        print(f"  Players: {inserted} inserted, {updated} updated")
        
        # Fetch upcoming matches
        print("Fetching upcoming matches...")
        matches = fetcher.fetch_matches(status="upcoming")
        result.records_fetched += len(matches)
        inserted, updated = db.upsert_matches(matches)
        result.records_inserted += inserted
        result.records_updated += updated
        print(f"  Upcoming: {inserted} inserted, {updated} updated")
        
        # Fetch live matches
        print("Fetching live matches...")
        live = fetcher.fetch_matches(status="live")
        result.records_fetched += len(live)
        inserted, updated = db.upsert_matches(live)
        result.records_inserted += inserted
        result.records_updated += updated
        print(f"  Live: {inserted} inserted, {updated} updated")
        
        db.log_fetch(result.to_log_dict("abios", "full_sync" if full_sync else "regular"))
        
    except Exception as e:
        result.status = "error"
        result.error_message = str(e)
        db.log_fetch(result.to_log_dict("abios", "error"))
        print(f"  ERROR: {e}")
    
    finally:
        fetcher.close()
    
    return result


def fetch_odds(db: Database):
    """Fetch odds data"""
    print("\n=== OddsPapi Sync ===")
    fetcher = OddsPapiFetcher()
    result = FetchResult()
    
    try:
        # Fetch upcoming odds
        print("Fetching odds...")
        odds = fetcher.fetch_cs2_odds("upcoming")
        result.records_fetched += len(odds)
        inserted = db.insert_odds(odds)
        result.records_inserted += inserted
        print(f"  Odds: {inserted} inserted")
        
        # Fetch Pinnacle sharp lines
        print("Fetching Pinnacle lines...")
        pinnacle = fetcher.fetch_pinnacle_odds()
        result.records_fetched += len(pinnacle)
        inserted = db.insert_odds(pinnacle)
        result.records_inserted += inserted
        print(f"  Pinnacle: {inserted} inserted")
        
        db.log_fetch(result.to_log_dict("oddspapi", "regular"))
        
    except Exception as e:
        result.status = "error"
        result.error_message = str(e)
        db.log_fetch(result.to_log_dict("oddspapi", "error"))
        print(f"  ERROR: {e}")
    
    finally:
        fetcher.close()
    
    return result


def main():
    parser = argparse.ArgumentParser(description="CS2 Data Pipeline")
    parser.add_argument("--full-sync", action="store_true", help="Perform full historical sync")
    parser.add_argument("--source", choices=["all", "pandascore", "abios", "odds"], default="all")
    args = parser.parse_args()
    
    print(f"Starting data pipeline at {datetime.now().isoformat()}")
    print(f"Mode: {'Full Sync' if args.full_sync else 'Regular Sync'}")
    
    db = Database()
    
    if args.source in ["all", "pandascore"]:
        fetch_pandascore(db, full_sync=args.full_sync)
    
    if args.source in ["all", "abios"]:
        fetch_abios(db, full_sync=args.full_sync)
    
    if args.source in ["all", "odds"]:
        fetch_odds(db)
    
    print(f"\nPipeline completed at {datetime.now().isoformat()}")


if __name__ == "__main__":
    main()
