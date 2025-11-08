# python/valuecell_trader/app.py
"""
Main application runner for ValueCell AI Trader
Integrates all services and runs in real-time or backtest mode
"""
import asyncio
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pathlib import Path
from datetime import datetime, timedelta
import logging
from typing import Optional

from .config.schema import TraderConfig
from .execution.broker_paper import PaperBroker
from .api.execution_service import ExecutionService
from .api.scoring_service import ScoringService
from .api.monitor_service import MonitorService
from .ingest.edgar import EDGARConnector
from .ingest.ir_rss import IRRSSConnector
from .ingest.govwatch import GovWatchConnector
from .ingest.social_verified import SocialVerifiedConnector
from .ingest.macrofeeds import MacroFeedsConnector
from .storage.schemas import TextEvent, PriceBar

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ValueCellTrader:
    """
    Main application class for ValueCell AI Trader
    """

    def __init__(self, config_path: Path):
        """
        Initialize the trader application

        Args:
            config_path: Path to configuration YAML
        """
        # Load configuration
        logger.info(f"Loading configuration from {config_path}")
        self.config = TraderConfig.from_yaml(config_path)

        # Initialize broker
        logger.info("Initializing paper broker...")
        self.broker = PaperBroker(initial_capital=1000.0)

        # Initialize data connectors
        logger.info("Initializing data connectors...")
        self.connectors = {
            "edgar": EDGARConnector(),
            "ir_rss": IRRSSConnector(),
            "govwatch": GovWatchConnector(),
            "social": SocialVerifiedConnector(),
            "macro": MacroFeedsConnector(),
        }

        # Initialize services
        logger.info("Initializing API services...")
        self.execution_service = ExecutionService(self.config, self.broker)
        self.scoring_service = ScoringService()
        self.monitor_service = MonitorService(self.broker)

        # Event cache
        self.event_cache: list[TextEvent] = []
        self.last_fetch_time: Optional[datetime] = None

        # Running flag
        self.is_running = False

    async def start_realtime_mode(self):
        """
        Start real-time trading mode
        Continuously fetches data and evaluates positions
        """
        logger.info("Starting real-time mode...")
        self.is_running = True

        # Start data ingestion loop
        ingestion_task = asyncio.create_task(self._data_ingestion_loop())

        # Start position evaluation loop
        evaluation_task = asyncio.create_task(self._evaluation_loop())

        # Start API server
        api_task = asyncio.create_task(self._run_api_server())

        # Wait for all tasks
        await asyncio.gather(ingestion_task, evaluation_task, api_task)

    async def _data_ingestion_loop(self):
        """
        Continuously fetch new events from all sources
        Runs every 5 minutes
        """
        while self.is_running:
            try:
                logger.info("Fetching new events from sources...")

                # Determine fetch window
                if self.last_fetch_time:
                    since_ts = self.last_fetch_time
                else:
                    since_ts = datetime.now() - timedelta(hours=24)

                # Fetch from all sources
                all_events = []

                # EDGAR filings
                try:
                    edgar_events = self.connectors["edgar"].fetch_events(
                        since_ts, self.config.universe.tickers
                    )
                    all_events.extend(edgar_events)
                    logger.info(f"Fetched {len(edgar_events)} EDGAR events")
                except Exception as e:
                    logger.error(f"EDGAR fetch failed: {e}")

                # IR RSS
                try:
                    ir_events = self.connectors["ir_rss"].fetch_events(
                        since_ts, self.config.universe.tickers
                    )
                    all_events.extend(ir_events)
                    logger.info(f"Fetched {len(ir_events)} IR events")
                except Exception as e:
                    logger.error(f"IR RSS fetch failed: {e}")

                # Government trades
                try:
                    gov_events = self.connectors["govwatch"].fetch_events(since_ts)
                    all_events.extend(gov_events)
                    logger.info(f"Fetched {len(gov_events)} government trade events")
                except Exception as e:
                    logger.error(f"GovWatch fetch failed: {e}")

                # Social media
                try:
                    social_events = self.connectors["social"].fetch_events(since_ts)
                    all_events.extend(social_events)
                    logger.info(f"Fetched {len(social_events)} social media events")
                except Exception as e:
                    logger.error(f"Social fetch failed: {e}")

                # Macro data
                try:
                    macro_events = self.connectors["macro"].fetch_events(since_ts)
                    all_events.extend(macro_events)
                    logger.info(f"Fetched {len(macro_events)} macro events")
                except Exception as e:
                    logger.error(f"Macro fetch failed: {e}")

                # Update cache
                self.event_cache.extend(all_events)

                # Prune old events (keep last 7 days)
                cutoff = datetime.now() - timedelta(days=7)
                self.event_cache = [
                    e for e in self.event_cache if e.published_at >= cutoff
                ]

                self.last_fetch_time = datetime.now()

                logger.info(f"Total events in cache: {len(self.event_cache)}")

            except Exception as e:
                logger.error(f"Data ingestion loop error: {e}", exc_info=True)

            # Wait 5 minutes before next fetch
            await asyncio.sleep(300)

    async def _evaluation_loop(self):
        """
        Continuously evaluate positions and look for new opportunities
        Runs every minute
        """
        while self.is_running:
            try:
                logger.info("Evaluating positions and opportunities...")

                for ticker in self.config.universe.tickers:
                    # Get ticker-specific events
                    ticker_events = [e for e in self.event_cache if ticker in e.ticker]

                    # Check if we have a position
                    position = self.broker.positions.get(ticker)

                    if position:
                        # Manage existing position
                        await self._manage_position(ticker, position, ticker_events)
                    else:
                        # Look for new opportunity
                        await self._evaluate_entry(ticker, ticker_events)

            except Exception as e:
                logger.error(f"Evaluation loop error: {e}", exc_info=True)

            # Wait 1 minute before next evaluation
            await asyncio.sleep(60)

    async def _manage_position(self, ticker: str, position, events: list):
        """Manage existing position"""
        # In production, would check stops/TPs/timeouts
        # For now, log
        logger.debug(f"Managing position in {ticker}")

    async def _evaluate_entry(self, ticker: str, events: list):
        """Evaluate potential new entry"""
        # In production, would calculate scores and size position
        # For now, log
        if events:
            logger.debug(f"Evaluating {ticker} with {len(events)} events")

    async def _run_api_server(self):
        """Run FastAPI server with all services"""
        # Create main app
        app = FastAPI(title="ValueCell AI Trader", version="1.0.0")

        # Add CORS
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Mount service apps
        app.mount("/execution", self.execution_service.app)
        app.mount("/scoring", self.scoring_service.app)
        app.mount("/monitor", self.monitor_service.app)

        # Root endpoint
        @app.get("/")
        async def root():
            return {
                "name": "ValueCell AI Trader",
                "version": "1.0.0",
                "status": "running" if self.is_running else "stopped",
                "services": {
                    "execution": "/execution/docs",
                    "scoring": "/scoring/docs",
                    "monitor": "/monitor/docs",
                },
            }

        # Health check
        @app.get("/health")
        async def health():
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "broker_capital": self.broker.get_capital(),
                "num_positions": len(self.broker.get_positions()),
                "num_events": len(self.event_cache),
            }

        # Run server
        config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()

    def stop(self):
        """Stop the trader"""
        logger.info("Stopping trader...")
        self.is_running = False
