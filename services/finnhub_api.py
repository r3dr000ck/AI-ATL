"""
Finnhub API Client
Provides market news and financial data
"""
import os
import finnhub
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Global client instance
_client_instance: Optional[finnhub.Client] = None


def get_finnhub_client() -> finnhub.Client:
    """Get or create global Finnhub API client instance"""
    global _client_instance
    if _client_instance is None:
        api_key = os.getenv("FINNHUB_API_KEY")
        if not api_key:
            logger.warning("FINNHUB_API_KEY not found. API calls will fail. Set it as an environment variable.")
            raise ValueError("Finnhub API key is not set.")
        
        _client_instance = finnhub.Client(api_key=api_key)
        logger.info("Finnhub API client initialized")
    
    return _client_instance


def close_finnhub_client():
    """Close the global Finnhub API client (no-op for finnhub-python as it's stateless)"""
    global _client_instance
    _client_instance = None


def get_general_news(category: str = "general", min_id: int = 0) -> List[Dict[str, Any]]:
    """
    Get general market news (synchronous - Finnhub client is synchronous)
    
    Args:
        category: News category (general, forex, crypto, merger)
        min_id: Minimum news ID (for pagination)
        
    Returns:
        List of news items
    """
    try:
        client = get_finnhub_client()
        news = client.general_news(category, min_id)
        return news if news else []
    except Exception as e:
        logger.error(f"Error fetching general news from Finnhub: {e}")
        raise


def get_company_news(symbol: str, _from: str, to: str) -> List[Dict[str, Any]]:
    """
    Get company-specific news (synchronous)
    
    Args:
        symbol: Stock symbol (e.g., 'AAPL')
        _from: Start date (YYYY-MM-DD)
        to: End date (YYYY-MM-DD)
        
    Returns:
        List of news items
    """
    try:
        client = get_finnhub_client()
        news = client.company_news(symbol, _from=_from, to=to)
        return news if news else []
    except Exception as e:
        logger.error(f"Error fetching company news from Finnhub: {e}")
        raise


def get_market_news(limit: int = 20, category: str = "general") -> Dict[str, Any]:
    """
    Get market news with formatting
    
    Args:
        limit: Maximum number of news items to return
        category: News category (general, forex, crypto, merger)
        
    Returns:
        Dictionary with formatted news items
    """
    try:
        # Get general market news (synchronous call)
        news_items = get_general_news(category=category, min_id=0)
        
        if not news_items:
            return {
                "news": [],
                "timestamp": datetime.now().isoformat(),
                "source": "finnhub"
            }
        
        # Format news items
        formatted_news = []
        for item in news_items[:limit]:
            # Convert timestamp to datetime if it's a Unix timestamp
            datetime_val = item.get("datetime", 0)
            if isinstance(datetime_val, (int, float)) and datetime_val > 0:
                dt = datetime.fromtimestamp(datetime_val)
            else:
                dt = datetime.now()
            
            formatted_news.append({
                "id": item.get("id", 0),
                "headline": item.get("headline", ""),
                "summary": item.get("summary", ""),
                "source": item.get("source", ""),
                "url": item.get("url", ""),
                "image": item.get("image", ""),
                "datetime": datetime_val,
                "datetime_formatted": dt.isoformat(),
                "category": item.get("category", category),
                "related": item.get("related", ""),
            })
        
        return {
            "news": formatted_news,
            "timestamp": datetime.now().isoformat(),
            "source": "finnhub"
        }
    except Exception as e:
        logger.error(f"Error in get_market_news: {e}")
        raise

