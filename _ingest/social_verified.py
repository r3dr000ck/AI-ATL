# python/valuecell_trader/ingest/social_verified.py
"""
Verified social media post ingestion
Monitors verified executive and CEO accounts for market-moving posts
"""
import requests
from typing import List, Optional, Set
from datetime import datetime, timezone
import hashlib
import time
import re

from ..storage.schemas import TextEvent


class SocialVerifiedConnector:
    """
    Connector for verified social media accounts
    Focuses on CEOs, CFOs, and official company accounts
    """

    # Verified executive accounts (example mapping)
    VERIFIED_EXECUTIVES = {
        'elonmusk': {'companies': ['TSLA'], 'name': 'Elon Musk', 'verified': True},
        'tim_cook': {'companies': ['AAPL'], 'name': 'Tim Cook', 'verified': True},
        'satyanadella': {'companies': ['MSFT'], 'name': 'Satya Nadella', 'verified': True},
        'nvidia': {'companies': ['NVDA'], 'name': 'NVIDIA Corp', 'verified': True},
        # Add more verified accounts
    }

    def __init__(self, api_key: Optional[str] = None):
        """
        Args:
            api_key: Twitter/X API key for premium access
        """
        self.api_key = api_key
        self.session = requests.Session()

    def fetch_events(
            self,
            since_ts: datetime,
            handles: Optional[List[str]] = None
    ) -> List[TextEvent]:
        """
        Fetch verified social posts

        Args:
            since_ts: Fetch posts after this time
            handles: Optional list of handles to monitor

        Returns:
            List of TextEvent objects
        """
        events = []

        target_handles = handles if handles else list(self.VERIFIED_EXECUTIVES.keys())

        for handle in target_handles:
            if handle not in self.VERIFIED_EXECUTIVES:
                continue

            exec_info = self.VERIFIED_EXECUTIVES[handle]

            try:
                # Fetch recent posts for this handle
                posts = self._fetch_posts(handle, since_ts)

                for post in posts:
                    try:
                        # Parse post
                        text = post.get('text', '')
                        post_id = post.get('id', '')
                        created_at = post.get('created_at')

                        # Parse timestamp
                        try:
                            post_dt = datetime.fromisoformat(created_at)
                        except:
                            continue

                        # Skip if before cutoff
                        if post_dt <= since_ts:
                            continue

                        # Check if market-relevant
                        if not self._is_market_relevant(text):
                            continue

                        # Analyze sentiment
                        sentiment = self._analyze_post_sentiment(text)

                        # Extract mentioned tickers (if any)
                        mentioned_tickers = self._extract_tickers(text)
                        tickers = list(set(exec_info['companies'] + mentioned_tickers))

                        # Create event
                        event = TextEvent(
                            event_id=f"sha256:{hashlib.sha256((handle + post_id).encode()).hexdigest()}",
                            ticker=tickers,
                            source="social_verified",
                            url=f"https://twitter.com/{handle}/status/{post_id}",
                            headline=f"{exec_info['name']}: {text[:100]}...",
                            published_at=post_dt,
                            first_seen_at=datetime.now(timezone.utc),
                            body_excerpt=text,
                            event_type="executive_post",
                            sentiment_raw=sentiment,
                            confidence=0.80,  # Verified accounts, high confidence
                            novelty=0.90  # Executive posts often novel
                        )

                        events.append(event)

                    except Exception as e:
                        print(f"Error parsing post from {handle}: {e}")
                        continue

                time.sleep(1)  # Rate limiting

            except Exception as e:
                print(f"Error fetching posts for {handle}: {e}")

        return events

    def _fetch_posts(self, handle: str, since_ts: datetime) -> List[dict]:
        """
        Fetch posts from API

        In production, calls Twitter/X API v2
        For demo, returns empty list
        """
        # TODO: Implement real API call
        """
        headers = {'Authorization': f'Bearer {self.api_key}'}
        response = requests.get(
            f'https://api.twitter.com/2/users/by/username/{handle}/tweets',
            params={
                'start_time': since_ts.isoformat(),
                'max_results': 100,
                'tweet.fields': 'created_at,text'
            },
            headers=headers
        )
        return response.json().get('data', [])
        """
        return []

    def _is_market_relevant(self, text: str) -> bool:
        """Check if post is market-relevant"""
        text_lower = text.lower()

        # Keywords indicating market relevance
        relevant_keywords = [
            'earnings', 'revenue', 'profit', 'sales', 'growth',
            'product', 'launch', 'announcement', 'acquisition',
            'partnership', 'expansion', 'guidance', 'forecast',
            'million', 'billion', 'quarter', 'quarter', 'year',
            'stock', 'share', 'market', 'investor'
        ]

        return any(keyword in text_lower for keyword in relevant_keywords)

    def _extract_tickers(self, text: str) -> List[str]:
        """Extract stock ticker mentions (e.g., $AAPL)"""
        ticker_pattern = r'\$([A-Z]{1,5})\b'
        matches = re.findall(ticker_pattern, text)
        return matches

    def _analyze_post_sentiment(self, text: str) -> float:
        """Analyze sentiment of social post"""
        text_lower = text.lower()

        sentiment = 0.0

        # Positive keywords
        positive = [
            'great', 'excited', 'amazing', 'record', 'growth',
            'success', 'proud', 'excellent', 'strong', 'best',
            'innovation', 'breakthrough', 'milestone'
        ]

        # Negative keywords
        negative = [
            'concern', 'challenge', 'difficult', 'unfortunately',
            'decline', 'loss', 'issue', 'problem', 'delay',
            'sorry', 'apologize'
        ]

        pos_count = sum(1 for word in positive if word in text_lower)
        neg_count = sum(1 for word in negative if word in text_lower)

        sentiment = (pos_count - neg_count) * 0.15

        return max(-1.0, min(1.0, sentiment))