"""
Base class for API fetchers with common functionality
"""
import time
import httpx
from typing import Any, Optional
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential

import sys
sys.path.append('..')
from config import API_RATE_LIMIT_DELAY


class BaseFetcher:
    """Base class for all API fetchers"""
    
    def __init__(self, base_url: str, api_key: str, source_name: str):
        self.base_url = base_url
        self.api_key = api_key
        self.source_name = source_name
        self.last_request_time = 0
        self.client = httpx.Client(timeout=30.0)
    
    def _rate_limit(self):
        """Enforce rate limiting between requests"""
        elapsed = time.time() - self.last_request_time
        if elapsed < API_RATE_LIMIT_DELAY:
            time.sleep(API_RATE_LIMIT_DELAY - elapsed)
        self.last_request_time = time.time()
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def _make_request(
        self, 
        endpoint: str, 
        method: str = "GET",
        params: Optional[dict] = None,
        headers: Optional[dict] = None
    ) -> dict:
        """Make HTTP request with retry logic"""
        self._rate_limit()
        
        url = f"{self.base_url}{endpoint}"
        default_headers = self._get_auth_headers()
        if headers:
            default_headers.update(headers)
        
        response = self.client.request(
            method=method,
            url=url,
            params=params,
            headers=default_headers
        )
        response.raise_for_status()
        return response.json()
    
    def _get_auth_headers(self) -> dict:
        """Override in subclass to provide auth headers"""
        return {}
    
    def close(self):
        """Close HTTP client"""
        self.client.close()


class FetchResult:
    """Standard result object for fetch operations"""
    
    def __init__(self):
        self.status = "success"
        self.records_fetched = 0
        self.records_inserted = 0
        self.records_updated = 0
        self.error_message = None
        self.start_time = datetime.now()
    
    def to_log_dict(self, source: str, endpoint: str) -> dict:
        """Convert to dict for logging to database"""
        duration = (datetime.now() - self.start_time).total_seconds() * 1000
        return {
            "source": source,
            "endpoint": endpoint,
            "status": self.status,
            "records_fetched": self.records_fetched,
            "records_inserted": self.records_inserted,
            "records_updated": self.records_updated,
            "error_message": self.error_message,
            "duration_ms": int(duration)
        }
