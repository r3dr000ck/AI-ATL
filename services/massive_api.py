"""
Massive.com (formerly Polygon.io) API Client
Provides real-time and historical stock market data
"""
import os
import aiohttp
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Massive API base URL
# Note: Massive.com was formerly Polygon.io, API structure may use polygon.io domain
# Check https://massive.com/docs for latest API endpoints
MASSIVE_API_BASE = "https://api.polygon.io/v2"


class MassiveAPIClient:
    """Client for Massive.com API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Massive API client
        
        Args:
            api_key: Massive.com API key. If not provided, will try to get from MASSIVE_API_KEY env var
        """
        self.api_key = api_key or os.getenv("MASSIVE_API_KEY")
        if not self.api_key:
            logger.warning("MASSIVE_API_KEY not found. API calls will fail. Set it as an environment variable.")
        
        self.base_url = MASSIVE_API_BASE
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            # Create SSL context that doesn't verify certificates
            # Note: This is less secure but necessary on some systems with SSL issues
            import ssl
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            self.session = aiohttp.ClientSession(connector=connector)
        return self.session
    
    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def _request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a request to the Massive API
        
        Args:
            endpoint: API endpoint (without base URL)
            params: Query parameters
            
        Returns:
            JSON response as dictionary
            
        Raises:
            Exception: If API request fails
        """
        if not self.api_key:
            raise ValueError("MASSIVE_API_KEY is not set")
        
        url = f"{self.base_url}{endpoint}"
        if params is None:
            params = {}
        params["apiKey"] = self.api_key
        
        session = await self._get_session()
        
        try:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 429:
                    error_text = await response.text()
                    logger.error(f"Rate limit exceeded: {error_text}")
                    raise Exception("Rate limit exceeded. Please try again later.")
                elif response.status == 401:
                    error_text = await response.text()
                    logger.error(f"Unauthorized: {error_text}")
                    raise Exception("Invalid API key. Please check your MASSIVE_API_KEY.")
                else:
                    error_text = await response.text()
                    logger.error(f"API request failed: {response.status} - {error_text}")
                    raise Exception(f"API request failed: {response.status}")
        except aiohttp.ClientError as e:
            logger.error(f"Network error: {e}")
            raise Exception(f"Network error: {str(e)}")
    
    async def get_ticker_details(self, ticker: str) -> Dict[str, Any]:
        """
        Get ticker details (company name, etc.)
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Ticker details dictionary
        """
        endpoint = f"/reference/tickers/{ticker}"
        return await self._request(endpoint)
    
    async def get_daily_open_close(self, ticker: str, date: str) -> Dict[str, Any]:
        """
        Get daily open/close data for a ticker
        
        Args:
            ticker: Stock ticker symbol
            date: Date in YYYY-MM-DD format
            
        Returns:
            Daily open/close data
        """
        endpoint = f"/aggs/ticker/{ticker}/range/1/day/{date}/{date}"
        return await self._request(endpoint)
    
    async def get_grouped_daily(self, date: str) -> Dict[str, Any]:
        """
        Get grouped daily bars for all stocks on a given date
        
        Args:
            date: Date in YYYY-MM-DD format
            
        Returns:
            Grouped daily bars for all stocks
        """
        endpoint = f"/aggs/grouped/locale/us/market/stocks/{date}"
        return await self._request(endpoint)
    
    async def get_snapshot_all_tickers(self) -> Dict[str, Any]:
        """
        Get snapshot of all tickers
        
        Returns:
            Snapshot data for all tickers
        """
        endpoint = "/snapshot/locale/us/markets/stocks/tickers"
        return await self._request(endpoint)
    
    async def get_snapshot_ticker(self, ticker: str) -> Dict[str, Any]:
        """
        Get snapshot for a specific ticker
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Snapshot data for the ticker
        """
        endpoint = f"/snapshot/locale/us/markets/stocks/tickers/{ticker}"
        return await self._request(endpoint)
    
    async def get_prev_close(self, ticker: str) -> Dict[str, Any]:
        """
        Get previous day's close data
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Previous close data
        """
        endpoint = f"/aggs/ticker/{ticker}/prev"
        return await self._request(endpoint)
    
    async def get_gainers_losers(self) -> Dict[str, Any]:
        """
        Get top gainers and losers (if available)
        Note: This endpoint may vary - using snapshot approach as fallback
        
        Returns:
            Dictionary with gainers and losers
        """
        # Get today's date
        today = datetime.now().strftime("%Y-%m-%d")
        
        try:
            # Try to get grouped daily data
            grouped_data = await self.get_grouped_daily(today)
            
            if "results" in grouped_data:
                results = grouped_data["results"]
                
                # Calculate percentage changes
                for result in results:
                    if result.get("c") and result.get("o"):  # close and open
                        result["change_pct"] = ((result["c"] - result["o"]) / result["o"]) * 100
                        result["change"] = result["c"] - result["o"]
                
                # Sort by percentage change
                sorted_results = sorted(results, key=lambda x: x.get("change_pct", 0), reverse=True)
                
                gainers = [r for r in sorted_results if r.get("change_pct", 0) > 0][:20]
                losers = [r for r in sorted_results if r.get("change_pct", 0) < 0][:20]
                
                return {
                    "gainers": gainers,
                    "losers": losers,
                    "status": "OK"
                }
        except Exception as e:
            logger.error(f"Error getting gainers/losers: {e}")
            raise
        
        return {"gainers": [], "losers": [], "status": "ERROR"}


# Global client instance
_client_instance: Optional[MassiveAPIClient] = None


def get_massive_client() -> MassiveAPIClient:
    """Get or create global Massive API client instance"""
    global _client_instance
    if _client_instance is None:
        _client_instance = MassiveAPIClient()
    return _client_instance


async def close_massive_client():
    """Close the global Massive API client"""
    global _client_instance
    if _client_instance:
        await _client_instance.close()
        _client_instance = None

