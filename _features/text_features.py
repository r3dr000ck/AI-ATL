# python/valuecell_trader/features/text_features.py
"""
Text feature extraction from news/filings
"""
from typing import List, Dict, Any
from datetime import datetime, timedelta
import numpy as np

from ..storage.schemas import TextEvent


class TextFeatureBuilder:
    """Build features from text events"""

    def __init__(self, decay_lambda: float = 0.1):
        """
        Args:
            decay_lambda: Exponential decay rate for time-weighting
        """
        self.decay_lambda = decay_lambda

    def build_features(
            self,
            ticker: str,
            current_ts: datetime,
            events: List[TextEvent],
            lookback_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Build text features from recent events

        Args:
            ticker: Ticker symbol
            current_ts: Current timestamp
            events: List of recent text events
            lookback_hours: How far back to look

        Returns:
            Dictionary of features
        """
        # Filter events for this ticker and time window
        cutoff_ts = current_ts - timedelta(hours=lookback_hours)
        ticker_events = [
            e for e in events
            if ticker in e.ticker and e.published_at <= current_ts and e.published_at >= cutoff_ts
        ]

        if not ticker_events:
            return self._get_default_features()

        # Calculate weighted sentiment
        sentiment_weighted = self._calculate_weighted_sentiment(ticker_events, current_ts)

        # Count events in last hour
        one_hour_ago = current_ts - timedelta(hours=1)
        event_count_1h = len([e for e in ticker_events if e.published_at >= one_hour_ago])

        # Calculate sentiment delta (change over time)
        six_hours_ago = current_ts - timedelta(hours=6)
        recent_events = [e for e in ticker_events if e.published_at >= six_hours_ago]
        older_events = [e for e in ticker_events if e.published_at < six_hours_ago]

        recent_sentiment = self._calculate_weighted_sentiment(recent_events, current_ts) if recent_events else 0
        older_sentiment = self._calculate_weighted_sentiment(older_events, six_hours_ago) if older_events else 0
        sentiment_delta = recent_sentiment - older_sentiment

        # Extract event tags
        event_tags = self._extract_event_tags(ticker_events)

        return {
            'sentiment_weighted': sentiment_weighted,
            'event_count_1h': event_count_1h,
            'sentiment_delta': sentiment_delta,
            'event_tags': event_tags
        }

    def _calculate_weighted_sentiment(self, events: List[TextEvent], reference_ts: datetime) -> float:
        """
        Calculate time-weighted sentiment score

        Formula: S(t) = Σ(w_i * s_i) / Σ(w_i)
        where w_i = conf_i * exp(-λ * Δt_i) * (1 + novelty_i)
        """
        if not events:
            return 0.0

        total_weighted_sentiment = 0.0
        total_weight = 0.0

        for event in events:
            # Time difference in hours
            delta_hours = (reference_ts - event.published_at).total_seconds() / 3600

            # Calculate weight
            time_decay = np.exp(-self.decay_lambda * delta_hours)
            novelty_factor = 1 + event.novelty
            weight = event.confidence * time_decay * novelty_factor

            total_weighted_sentiment += weight * event.sentiment_raw
            total_weight += weight

        return total_weighted_sentiment / total_weight if total_weight > 0 else 0.0

    def _extract_event_tags(self, events: List[TextEvent]) -> Dict[str, float]:
        """Extract and aggregate event type tags"""
        tags = {
            'earnings': 0,
            'guidance_up': 0,
            'guidance_down': 0,
            'capex_up': 0,
            'mna': 0,
            'lawsuit': 0,
            'exec_change': 0
        }

        for event in events:
            text = (event.headline + ' ' + event.body_excerpt).lower()

            if 'earnings' in text or 'quarter' in text:
                tags['earnings'] += 1
            if 'guidance' in text and any(w in text for w in ['raise', 'increase', 'upgrade']):
                tags['guidance_up'] += 1
            if 'guidance' in text and any(w in text for w in ['lower', 'decrease', 'downgrade']):
                tags['guidance_down'] += 1
            if any(w in text for w in ['capex', 'capital expenditure', 'investment']) and 'increase' in text:
                tags['capex_up'] += 1
            if any(w in text for w in ['acquisition', 'merger', 'm&a', 'buyout']):
                tags['mna'] += 1
            if any(w in text for w in ['lawsuit', 'litigation', 'legal action']):
                tags['lawsuit'] += 1
            if any(w in text for w in ['ceo', 'cfo', 'executive', 'resignation', 'appointment']):
                tags['exec_change'] += 1

        return tags

    def _get_default_features(self) -> Dict[str, Any]:
        """Return default features when no events available"""
        return {
            'sentiment_weighted': 0.0,
            'event_count_1h': 0,
            'sentiment_delta': 0.0,
            'event_tags': {
                'earnings': 0,
                'guidance_up': 0,
                'guidance_down': 0,
                'capex_up': 0,
                'mna': 0,
                'lawsuit': 0,
                'exec_change': 0
            }
        }