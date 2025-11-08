# python/valuecell_trader/api/scoring_service.py
"""
Scoring service API - Calculate investment scores
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from ..models.__init__ import PUpModel
from ..models.d_ext import DExtModel
from ..models.model_trainer import PDropModel
from ..models.ensemble import EnsembleScorer
from ..features.text_features import TextFeatureBuilder
from ..features.market_features import MarketFeatureBuilder
from ..storage.schemas import TextEvent, PriceBar

logger = logging.getLogger(__name__)


class ScoreRequest(BaseModel):
    """Score calculation request"""

    ticker: str = Field(..., description="Ticker symbol")
    text: Optional[str] = Field(
        None, description="Text to analyze (news, filing, post)"
    )
    headline: Optional[str] = Field(None, description="Headline")
    source: str = Field("manual", description="Source of information")
    sentiment: Optional[float] = Field(
        None, ge=-1, le=1, description="Pre-calculated sentiment"
    )
    market_data: Optional[Dict[str, Any]] = Field(
        None, description="Current market data"
    )


class ScoreResponse(BaseModel):
    """Score calculation response"""

    ticker: str
    s_final: float = Field(..., description="Final investment score [0,1]")
    p_up: float = Field(..., description="Upward probability")
    p_drop: float = Field(..., description="Downward probability")
    d_ext: float = Field(..., description="Extension dampener")
    expected_move: Optional[float] = Field(None, description="Expected percentage move")
    action: str = Field(..., description="Recommended action: BUY, SELL, HOLD")
    confidence: float = Field(..., description="Confidence in score")
    explanation: str = Field(..., description="Human-readable explanation")
    timestamp: datetime


class ScoringService:
    """Service for calculating investment scores"""

    def __init__(self):
        self.text_features = TextFeatureBuilder()
        self.market_features = MarketFeatureBuilder()
        self.p_up_model = PUpModel()
        self.d_ext_model = DExtModel()
        self.p_drop_model = PDropModel()
        self.ensemble = EnsembleScorer()

        self.app = FastAPI(title="ValueCell Trader - Scoring Service")
        self._setup_routes()

    def _setup_routes(self):
        """Setup FastAPI routes"""

        @self.app.post("/score", response_model=ScoreResponse)
        async def calculate_score(request: ScoreRequest):
            """
            Calculate investment score for a ticker

            Example:
            ```
            POST /score
            {
                "ticker": "AAPL",
                "headline": "Apple announces record earnings",
                "text": "Apple Inc. reported quarterly earnings...",
                "source": "company_ir_rss"
            }
            ```
            """
            try:
                return await self._calculate_score(request)
            except Exception as e:
                logger.error(f"Score calculation failed: {e}", exc_info=True)
                raise HTTPException(500, f"Scoring failed: {str(e)}")

        @self.app.post("/batch_score")
        async def batch_score(requests: List[ScoreRequest]):
            """Calculate scores for multiple tickers"""
            results = []
            for req in requests:
                try:
                    score = await self._calculate_score(req)
                    results.append(score)
                except Exception as e:
                    logger.error(f"Score failed for {req.ticker}: {e}")
                    results.append({"ticker": req.ticker, "error": str(e)})
            return {"scores": results}

    async def _calculate_score(self, request: ScoreRequest) -> ScoreResponse:
        """Calculate investment score"""

        # Build text features
        text_features = {}
        if request.text or request.headline:
            # Create synthetic event
            event = TextEvent(
                event_id=f"manual_{datetime.now().timestamp()}",
                ticker=[request.ticker],
                source=request.source,
                url="",
                headline=request.headline or "Manual input",
                published_at=datetime.now(),
                first_seen_at=datetime.now(),
                body_excerpt=request.text or "",
                event_type="manual",
                sentiment_raw=request.sentiment or 0.0,
                confidence=0.7,
                novelty=0.8,
            )

            text_features = self.text_features.build_features(
                request.ticker, datetime.now(), [event]
            )
        else:
            text_features = self.text_features.build_features(
                request.ticker, datetime.now(), []
            )

        # Build market features
        market_features = {}
        if request.market_data:
            # Use provided market data
            market_features = {
                "return_zscore": request.market_data.get("return_zscore", 0),
                "rsi": request.market_data.get("rsi", 50),
                "atr": request.market_data.get("atr", 0),
                "volume_ratio": request.market_data.get("volume_ratio", 1),
                "spread_bps": request.market_data.get("spread_bps", 5),
            }
        else:
            # Use defaults
            market_features = {
                "return_zscore": 0,
                "rsi": 50,
                "atr": 0,
                "volume_ratio": 1,
                "spread_bps": 5,
            }

        # Combine features
        features = {**text_features, **market_features}

        # Calculate scores
        p_up = self.p_up_model.predict(features)
        d_ext = self.d_ext_model.compute(features)
        p_drop = self.p_drop_model.predict(features)

        # Get ensemble score
        ensemble_result = self.ensemble.calculate_final_score(p_up, d_ext, p_drop)

        s_final = ensemble_result["s_final"]

        # Determine action
        if s_final >= 0.65:
            action = "BUY"
        elif s_final <= 0.35:
            action = "SELL"
        else:
            action = "HOLD"

        # Generate explanation
        explanation = self._generate_explanation(s_final, p_up, d_ext, p_drop, features)

        return ScoreResponse(
            ticker=request.ticker,
            s_final=s_final,
            p_up=p_up,
            p_drop=p_drop,
            d_ext=d_ext,
            expected_move=ensemble_result.get("expected_move"),
            action=action,
            confidence=max(p_up, p_drop),
            explanation=explanation,
            timestamp=datetime.now(),
        )

    def _generate_explanation(
        self,
        s_final: float,
        p_up: float,
        d_ext: float,
        p_drop: float,
        features: Dict[str, Any],
    ) -> str:
        """Generate human-readable explanation"""

        parts = []

        # Overall score
        if s_final >= 0.7:
            parts.append("Strong buy signal.")
        elif s_final >= 0.6:
            parts.append("Moderate buy signal.")
        elif s_final <= 0.4:
            parts.append("Negative signal.")
        else:
            parts.append("Neutral signal.")

        # Conviction
        if p_up > 0.7:
            parts.append(f"High conviction (P_up={p_up:.2f}).")
        elif p_up < 0.4:
            parts.append(f"Low conviction (P_up={p_up:.2f}).")

        # Extension
        if d_ext < 0.7:
            parts.append(f"Market appears extended (D_ext={d_ext:.2f}).")

        # Downside risk
        if p_drop > 0.5:
            parts.append(f"Elevated downside risk (P_drop={p_drop:.2f}).")

        # Sentiment
        sentiment = features.get("sentiment_weighted", 0)
        if abs(sentiment) > 0.2:
            direction = "positive" if sentiment > 0 else "negative"
            parts.append(f"Sentiment is {direction} ({sentiment:+.2f}).")

        # Technical
        rsi = features.get("rsi", 50)
        if rsi > 70:
            parts.append(f"Overbought (RSI={rsi:.0f}).")
        elif rsi < 30:
            parts.append(f"Oversold (RSI={rsi:.0f}).")

        return " ".join(parts)
