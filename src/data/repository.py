"""Repository pattern for database operations.

Provides high-level repository interfaces for storing and retrieving historical
analyst ratings and other time-sensitive data from the SQLite database.
"""

import json
import statistics
from datetime import date, datetime, timedelta
from pathlib import Path

import yfinance as yf
from loguru import logger
from sqlalchemy import func
from sqlmodel import and_, select

from src.data.db import DatabaseManager
from src.data.models import (
    AnalystData,
    AnalystRating,
    FundamentalSnapshot,
    PerformanceSummary,
    PriceTracking,
    Recommendation,
    RunSession,
    Ticker,
    TradingJournal,
    Watchlist,
    WatchlistSignal,
)


def get_or_create_ticker(session, ticker_symbol: str, name: str = "") -> Ticker:
    """Get existing ticker or create new one.

    Shared helper function used by multiple repositories to ensure consistent
    ticker creation with automatic company metadata fetching.

    Args:
        session: Database session.
        ticker_symbol: Ticker symbol (e.g., 'AAPL').
        name: Company name (optional, will be fetched if not provided).

    Returns:
        Ticker object.
    """
    ticker_symbol = ticker_symbol.upper()

    # Check if ticker already exists
    existing = session.exec(select(Ticker).where(Ticker.symbol == ticker_symbol)).first()

    if existing:
        return existing

    # Initialize company metadata
    description = None
    sector = None
    industry = None
    currency = "USD"  # Default
    exchange = None

    # Fetch company metadata if name not provided or if it's just the ticker symbol
    if not name or name == ticker_symbol:
        try:
            ticker_obj = yf.Ticker(ticker_symbol)
            info = ticker_obj.info

            # Extract company information
            name = info.get("longName") or info.get("shortName") or ticker_symbol
            description = info.get("longBusinessSummary")
            sector = info.get("sector")
            industry = info.get("industry")
            currency = info.get("currency") or info.get("financialCurrency") or "USD"
            exchange = info.get("exchange")

            logger.debug(
                f"Fetched metadata for {ticker_symbol}: "
                f"name={name}, sector={sector}, industry={industry}"
            )
        except Exception as e:
            logger.warning(f"Could not fetch company metadata for {ticker_symbol}: {e}")
            name = ticker_symbol

    # Create new ticker with all metadata
    new_ticker = Ticker(
        symbol=ticker_symbol,
        name=name,
        description=description,
        sector=sector,
        industry=industry,
        currency=currency,
        exchange=exchange,
        market="us",  # Default, can be overridden later
        instrument_type="stock",
    )
    session.add(new_ticker)
    session.flush()  # Flush to get the ID without committing
    return new_ticker


class AnalystRatingsRepository:
    """Repository for storing and retrieving historical analyst ratings.

    Manages CRUD operations for analyst ratings in the SQLite database,
    with additional methods for querying historical data.
    """

    def __init__(self, db_path: Path | str = "data/falconsignals.db"):
        """Initialize repository with database manager.

        Args:
            db_path: Path to SQLite database file.
        """
        # Create instance-specific database manager (not global) for better test isolation
        self.db_manager = DatabaseManager(db_path)
        self.db_manager.initialize()

    def store_ratings(self, ratings: AnalystRating, data_source: str = "unknown") -> bool:
        """Store analyst ratings for a specific month.

        Stores monthly snapshots of ratings. Automatically converts the rating_date
        to the first day of the month for consistent period grouping.

        Args:
            ratings: AnalystRating object with rating data.
            data_source: Source of the data (e.g., 'Finnhub', 'AlphaVantage').

        Returns:
            True if successful, False otherwise.
        """
        # Normalize ticker to uppercase for consistency
        ticker = ratings.ticker.upper()

        try:
            # Extract month period (first day of month)
            period = self._get_period_start(ratings.rating_date)

            # Parse rating counts from consensus or use defaults
            strong_buy, buy, hold, sell, strong_sell = self._parse_ratings(ratings)

            # Store in database (upsert pattern)
            session = self.db_manager.get_session()
            try:
                # Get or create ticker (handles foreign key relationship)
                ticker_obj = get_or_create_ticker(session, ticker, ratings.name)

                # Check if record exists
                existing = session.exec(
                    select(AnalystData).where(
                        (AnalystData.ticker_id == ticker_obj.id)
                        & (AnalystData.period == period)
                        & (AnalystData.data_source == data_source)
                    )
                ).first()

                if existing:
                    # Update existing record
                    existing.strong_buy = strong_buy
                    existing.buy = buy
                    existing.hold = hold
                    existing.sell = sell
                    existing.strong_sell = strong_sell
                    existing.total_analysts = ratings.num_analysts or 0
                    existing.fetched_at = datetime.now()
                    session.add(existing)
                else:
                    # Create new record
                    analyst_data = AnalystData(
                        ticker_id=ticker_obj.id,
                        period=period,
                        strong_buy=strong_buy,
                        buy=buy,
                        hold=hold,
                        sell=sell,
                        strong_sell=strong_sell,
                        total_analysts=ratings.num_analysts or 0,
                        data_source=data_source,
                        fetched_at=datetime.now(),
                    )
                    session.add(analyst_data)

                session.commit()
                logger.debug(
                    f"Stored analyst ratings for {ticker} (period: {period}, source: {data_source})"
                )
                return True

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error storing analyst ratings for {ticker}: {e}")
            return False

    def get_ratings(self, ticker: str, period: date) -> AnalystRating | None:
        """Get analyst ratings for a specific ticker and period.

        Args:
            ticker: Stock ticker symbol.
            period: Period (first day of month).

        Returns:
            AnalystRating object or None if not found.
        """
        try:
            ticker = ticker.upper()
            session = self.db_manager.get_session()
            try:
                # Find ticker first, then get analyst data
                ticker_obj = session.exec(select(Ticker).where(Ticker.symbol == ticker)).first()

                if not ticker_obj:
                    return None

                analyst_data = session.exec(
                    select(AnalystData).where(
                        (AnalystData.ticker_id == ticker_obj.id) & (AnalystData.period == period)
                    )
                ).first()

                return analyst_data.to_analyst_rating() if analyst_data else None

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error retrieving analyst ratings for {ticker}: {e}")
            return None

    def get_latest_ratings(self, ticker: str) -> AnalystRating | None:
        """Get the most recent analyst ratings for a ticker.

        Args:
            ticker: Stock ticker symbol.

        Returns:
            AnalystRating object or None if not found.
        """
        try:
            ticker = ticker.upper()
            session = self.db_manager.get_session()
            try:
                # Find ticker first
                ticker_obj = session.exec(select(Ticker).where(Ticker.symbol == ticker)).first()

                if not ticker_obj:
                    return None

                analyst_data = session.exec(
                    select(AnalystData)
                    .where(AnalystData.ticker_id == ticker_obj.id)
                    .order_by(AnalystData.period.desc())
                ).first()

                return analyst_data.to_analyst_rating() if analyst_data else None

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error retrieving latest analyst ratings for {ticker}: {e}")
            return None

    def get_ratings_history(
        self, ticker: str, start_period: date, end_period: date
    ) -> list[AnalystRating]:
        """Get historical analyst ratings for a ticker over a date range.

        Args:
            ticker: Stock ticker symbol.
            start_period: Start period (first day of month).
            end_period: End period (first day of month).

        Returns:
            List of AnalystRating objects, sorted by period ascending.
        """
        try:
            ticker = ticker.upper()
            session = self.db_manager.get_session()
            try:
                # Find ticker first
                ticker_obj = session.exec(select(Ticker).where(Ticker.symbol == ticker)).first()

                if not ticker_obj:
                    return []

                analyst_data_list = session.exec(
                    select(AnalystData)
                    .where(
                        (AnalystData.ticker_id == ticker_obj.id)
                        & (AnalystData.period >= start_period)
                        & (AnalystData.period <= end_period)
                    )
                    .order_by(AnalystData.period.asc())
                ).all()

                return [data.to_analyst_rating() for data in analyst_data_list]

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error retrieving analyst ratings history for {ticker}: {e}")
            return []

    def delete_ratings(self, ticker: str, period: date) -> bool:
        """Delete analyst ratings for a specific ticker and period.

        Args:
            ticker: Stock ticker symbol.
            period: Period (first day of month).

        Returns:
            True if successful, False otherwise.
        """
        try:
            ticker = ticker.upper()
            session = self.db_manager.get_session()
            try:
                # Find ticker first
                ticker_obj = session.exec(select(Ticker).where(Ticker.symbol == ticker)).first()

                if not ticker_obj:
                    logger.warning(f"No ratings found for {ticker} (period: {period})")
                    return False

                analyst_data = session.exec(
                    select(AnalystData).where(
                        (AnalystData.ticker_id == ticker_obj.id) & (AnalystData.period == period)
                    )
                ).first()

                if analyst_data:
                    session.delete(analyst_data)
                    session.commit()
                    logger.debug(f"Deleted analyst ratings for {ticker} (period: {period})")
                    return True

                logger.warning(f"No ratings found for {ticker} (period: {period})")
                return False

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error deleting analyst ratings for {ticker}: {e}")
            return False

    def get_all_tickers_with_data(self) -> list[str]:
        """Get all unique tickers with analyst rating data in the database.

        Returns:
            List of unique ticker symbols, sorted alphabetically.
        """
        try:
            session = self.db_manager.get_session()
            try:
                # Get tickers that have at least one analyst rating
                tickers_with_data = session.exec(
                    select(Ticker.symbol).join(AnalystData).distinct()
                ).all()
                return sorted(list(set(tickers_with_data)))

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error retrieving tickers: {e}")
            return []

    def get_data_count(self) -> int:
        """Get total number of analyst rating records in database.

        Returns:
            Total count of records.
        """
        try:
            session = self.db_manager.get_session()
            try:
                # SQLModel doesn't have count() directly, so use func.count()
                count = session.exec(select(func.count(AnalystData.id))).one()
                return count or 0

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error retrieving data count: {e}")
            return 0

    # Helper methods

    @staticmethod
    def _get_period_start(dt: datetime | date) -> date:
        """Convert a datetime/date to the first day of its month.

        Args:
            dt: Input datetime or date.

        Returns:
            First day of the month as date object.
        """
        if isinstance(dt, datetime):
            dt = dt.date()
        return dt.replace(day=1)

    @staticmethod
    def _parse_ratings(ratings: AnalystRating) -> tuple[int, int, int, int, int]:
        """Parse rating counts from AnalystRating.

        Uses actual raw counts if available (e.g., from Finnhub).
        Otherwise, estimates distribution from consensus.

        Args:
            ratings: AnalystRating object.

        Returns:
            Tuple of (strong_buy, buy, hold, sell, strong_sell) counts.
        """
        # If we have raw counts from the provider (e.g., Finnhub), use them directly
        if (
            ratings.strong_buy is not None
            or ratings.buy is not None
            or ratings.hold is not None
            or ratings.sell is not None
            or ratings.strong_sell is not None
        ):
            return (
                ratings.strong_buy or 0,
                ratings.buy or 0,
                ratings.hold or 0,
                ratings.sell or 0,
                ratings.strong_sell or 0,
            )

        # Fall back to estimation if only consensus is available
        total = ratings.num_analysts or 1

        if ratings.consensus:
            consensus = ratings.consensus.lower()
            # Simple distribution: 40% consensus, 15% each of neighbors, 10% other
            if consensus == "strong_buy":
                return (int(total * 0.4), int(total * 0.3), int(total * 0.2), 0, 0)
            elif consensus == "buy":
                return (int(total * 0.2), int(total * 0.4), int(total * 0.3), int(total * 0.1), 0)
            elif consensus == "hold":
                return (
                    int(total * 0.1),
                    int(total * 0.2),
                    int(total * 0.4),
                    int(total * 0.2),
                    int(total * 0.1),
                )
            elif consensus == "sell":
                return (0, int(total * 0.1), int(total * 0.3), int(total * 0.4), int(total * 0.2))
            elif consensus == "strong_sell":
                return (0, 0, int(total * 0.2), int(total * 0.3), int(total * 0.4))

        # Default distribution if no consensus
        return (0, int(total * 0.3), int(total * 0.4), int(total * 0.2), 0)


class RunSessionRepository:
    """Repository for managing analysis run sessions.

    Tracks each analysis run with metadata for grouping signals and monitoring progress.
    """

    def __init__(self, db_path: Path | str = "data/falconsignals.db"):
        """Initialize repository with database manager.

        Args:
            db_path: Path to SQLite database file.
        """
        self.db_manager = DatabaseManager(db_path)
        self.db_manager.initialize()

    def create_session(
        self,
        analysis_mode: str,
        analyzed_category: str | None = None,
        analyzed_market: str | None = None,
        analyzed_tickers_specified: list[str] | None = None,
        initial_tickers_count: int = 0,
        anomalies_count: int = 0,
        force_full_analysis: bool = False,
    ) -> int:
        """Create a new run session.

        Args:
            analysis_mode: Analysis mode ('rule_based' or 'llm').
            analyzed_category: Category analyzed (e.g., 'us_tech_software').
            analyzed_market: Market analyzed ('us', 'nordic', 'eu', 'global').
            analyzed_tickers_specified: List of tickers if --ticker flag used.
            initial_tickers_count: Total tickers before filtering.
            anomalies_count: Number of anomalies detected in stage 1.
            force_full_analysis: Whether --force-full-analysis was used.

        Returns:
            Session ID (auto-incrementing integer).
        """

        try:
            session = self.db_manager.get_session()
            try:
                run_session = RunSession(
                    started_at=datetime.now(),
                    analysis_mode=analysis_mode,
                    analyzed_category=analyzed_category,
                    analyzed_market=analyzed_market,
                    analyzed_tickers_specified=(
                        json.dumps(analyzed_tickers_specified)
                        if analyzed_tickers_specified
                        else None
                    ),
                    initial_tickers_count=initial_tickers_count,
                    anomalies_count=anomalies_count,
                    force_full_analysis=force_full_analysis,
                    status="running",
                )

                session.add(run_session)
                session.commit()
                session.refresh(run_session)  # Refresh to get the auto-generated ID

                session_id = run_session.id
                logger.debug(f"Created run session: {session_id} ({analysis_mode})")
                return session_id

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error creating run session: {e}")
            raise

    def complete_session(
        self,
        session_id: int,
        signals_generated: int,
        signals_failed: int,
        status: str = "completed",
        error_message: str | None = None,
    ) -> None:
        """Mark session as completed.

        Args:
            session_id: Session ID (integer).
            signals_generated: Number of signals successfully created.
            signals_failed: Number of tickers that failed analysis.
            status: Final status ('completed', 'failed', 'partial').
            error_message: Error message if run failed.
        """
        try:
            session = self.db_manager.get_session()
            try:
                run_session = session.exec(
                    select(RunSession).where(RunSession.id == session_id)
                ).first()

                if run_session:
                    run_session.completed_at = datetime.now()
                    run_session.signals_generated = signals_generated
                    run_session.signals_failed = signals_failed
                    run_session.status = status
                    run_session.error_message = error_message

                    session.add(run_session)
                    session.commit()

                    logger.debug(
                        f"Completed run session: {session_id} "
                        f"({signals_generated} signals, {signals_failed} failed)"
                    )
                else:
                    logger.warning(f"Run session not found: {session_id}")

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error completing run session {session_id}: {e}")

    def get_session(self, session_id: str) -> RunSession | None:
        """Get session by ID.

        Args:
            session_id: Session ID (UUID).

        Returns:
            RunSession object or None if not found.
        """
        try:
            session = self.db_manager.get_session()
            try:
                run_session = session.exec(
                    select(RunSession).where(RunSession.id == session_id)
                ).first()
                return run_session

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error retrieving run session {session_id}: {e}")
            return None

    def get_recent_sessions(self, limit: int = 10) -> list[dict]:
        """Get recent analysis sessions.

        Args:
            limit: Maximum number of sessions to return.

        Returns:
            List of session dictionaries with key fields.
        """
        try:
            session = self.db_manager.get_session()
            try:
                sessions = session.exec(
                    select(RunSession)
                    .where(RunSession.status == "completed")
                    .order_by(RunSession.started_at.desc())
                    .limit(limit)
                ).all()

                result = []
                for sess in sessions:
                    # Get analysis date from first signal or use started_at
                    analysis_date = sess.started_at.date().isoformat() if sess.started_at else None

                    result.append(
                        {
                            "id": sess.id,
                            "started_at": sess.started_at.isoformat() if sess.started_at else None,
                            "analysis_date": analysis_date,
                            "analysis_mode": sess.analysis_mode,
                            "total_signals": sess.signals_generated or 0,
                            "status": sess.status,
                        }
                    )

                return result

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error retrieving recent sessions: {e}")
            return []


class RecommendationsRepository:
    """Repository for storing and retrieving investment recommendations.

    Stores every investment signal immediately after creation, enabling partial report
    generation and historical analysis.
    """

    def __init__(self, db_path: Path | str = "data/falconsignals.db"):
        """Initialize repository with database manager.

        Args:
            db_path: Path to SQLite database file.
        """
        self.db_manager = DatabaseManager(db_path)
        self.db_manager.initialize()

    def store_recommendation(
        self,
        signal,  # InvestmentSignal type (imported dynamically to avoid circular import)
        run_session_id: int,
        analysis_mode: str,
        llm_model: str | None = None,
    ) -> int:
        """Store a single recommendation.

        Args:
            signal: InvestmentSignal Pydantic model.
            run_session_id: Integer ID linking to run session.
            analysis_mode: 'rule_based' or 'llm'.
            llm_model: LLM model name (if applicable).

        Returns:
            recommendation_id (auto-incrementing integer).
        """

        try:
            session = self.db_manager.get_session()
            try:
                # Get or create ticker
                ticker_obj = get_or_create_ticker(session, signal.ticker, signal.name)

                # Convert analysis_date string to date object
                if isinstance(signal.analysis_date, str):
                    analysis_date = datetime.strptime(signal.analysis_date, "%Y-%m-%d").date()
                else:
                    analysis_date = signal.analysis_date

                # Serialize complex fields to JSON
                risk_flags_json = json.dumps(signal.risk.flags) if signal.risk.flags else None
                key_reasons_json = json.dumps(signal.key_reasons) if signal.key_reasons else None
                caveats_json = json.dumps(signal.caveats) if signal.caveats else None

                # Serialize metadata to JSON
                metadata_json = None
                if signal.metadata:
                    metadata_json = json.dumps(
                        signal.metadata.model_dump(mode="json", exclude_none=True)
                    )

                # Create recommendation record
                recommendation = Recommendation(
                    ticker_id=ticker_obj.id,
                    run_session_id=run_session_id,
                    analysis_date=analysis_date,
                    analysis_mode=analysis_mode,
                    llm_model=llm_model,
                    signal_type=signal.recommendation.value,
                    final_score=signal.final_score,
                    confidence=signal.confidence,
                    technical_score=signal.scores.technical if signal.scores else None,
                    fundamental_score=signal.scores.fundamental if signal.scores else None,
                    sentiment_score=signal.scores.sentiment if signal.scores else None,
                    current_price=signal.current_price,
                    currency=signal.currency,
                    expected_return_min=signal.expected_return_min,
                    expected_return_max=signal.expected_return_max,
                    time_horizon=signal.time_horizon,
                    risk_level=signal.risk.level.value if signal.risk else None,
                    risk_volatility=signal.risk.volatility if signal.risk else None,
                    risk_volatility_pct=signal.risk.volatility_pct if signal.risk else None,
                    risk_flags=risk_flags_json,
                    key_reasons=key_reasons_json,
                    rationale=signal.rationale,
                    caveats=caveats_json,
                    metadata_json=metadata_json,
                )

                session.add(recommendation)
                session.commit()
                session.refresh(recommendation)  # Refresh to get the auto-generated ID

                recommendation_id = recommendation.id
                logger.debug(f"Stored recommendation {recommendation_id} for {signal.ticker}")
                return recommendation_id

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error storing recommendation for {signal.ticker}: {e}")
            raise

    def _to_investment_signal(self, recommendation: Recommendation):
        """Convert Recommendation database model to InvestmentSignal Pydantic model.

        Args:
            recommendation: Recommendation database object.

        Returns:
            InvestmentSignal Pydantic model.
        """
        from src.analysis import InvestmentSignal
        from src.analysis.models import AnalysisMetadata, ComponentScores, RiskAssessment, RiskLevel
        from src.analysis.models import Recommendation as RecommendationType

        # Deserialize JSON fields
        risk_flags = json.loads(recommendation.risk_flags) if recommendation.risk_flags else []
        key_reasons = json.loads(recommendation.key_reasons) if recommendation.key_reasons else []
        caveats = json.loads(recommendation.caveats) if recommendation.caveats else []

        # Deserialize metadata
        metadata = None
        if recommendation.metadata_json:
            try:
                metadata_dict = json.loads(recommendation.metadata_json)
                metadata = AnalysisMetadata(**metadata_dict)
            except Exception as e:
                logger.warning(
                    f"Failed to deserialize metadata for recommendation {recommendation.id}: {e}"
                )

        # Create ComponentScores
        scores = ComponentScores(
            technical=recommendation.technical_score or 50.0,
            fundamental=recommendation.fundamental_score or 50.0,
            sentiment=recommendation.sentiment_score or 50.0,
        )

        # Create RiskAssessment
        risk = RiskAssessment(
            level=(
                RiskLevel(recommendation.risk_level)
                if recommendation.risk_level
                else RiskLevel.MEDIUM
            ),
            volatility=recommendation.risk_volatility or "normal",
            volatility_pct=recommendation.risk_volatility_pct or 0.0,
            liquidity="normal",  # Default - not stored in recommendations table
            concentration_risk=False,  # Default - not stored in recommendations table
            flags=risk_flags,
        )

        # Create InvestmentSignal
        return InvestmentSignal(
            ticker=recommendation.ticker_obj.symbol,
            name=recommendation.ticker_obj.name,
            market="unknown",  # Not stored in recommendations table
            sector=None,  # Not stored in recommendations table
            current_price=recommendation.current_price,
            currency=recommendation.currency,
            scores=scores,
            final_score=recommendation.final_score,
            recommendation=RecommendationType(recommendation.signal_type),
            confidence=recommendation.confidence,
            time_horizon=recommendation.time_horizon or "3M",
            expected_return_min=recommendation.expected_return_min or 0.0,
            expected_return_max=recommendation.expected_return_max or 0.0,
            key_reasons=key_reasons,
            risk=risk,
            generated_at=recommendation.created_at,
            analysis_date=recommendation.analysis_date.strftime("%Y-%m-%d"),
            rationale=recommendation.rationale,
            caveats=caveats,
            metadata=metadata,
        )

    def get_recommendations_by_session(
        self,
        run_session_id: int,
        analysis_mode: str | None = None,
        signal_type: str | None = None,
        confidence_threshold: float | None = None,
        final_score_threshold: float | None = None,
    ) -> list:
        """Get all recommendations for a specific run session.

        Args:
            run_session_id: Integer ID of the run session.
            analysis_mode: Filter by analysis mode ('llm' or 'rule_based').
            signal_type: Filter by signal type (e.g., 'strong_buy', 'buy', 'hold').
            confidence_threshold: Minimum confidence score (e.g., 70 means confidence > 70).
            final_score_threshold: Minimum final score (e.g., 70 means final_score > 70).

        Returns:
            List of InvestmentSignal Pydantic models (deduplicated by ticker+analysis_date).
        """
        try:
            session = self.db_manager.get_session()
            try:
                # Build query with filters
                query = select(Recommendation).where(
                    Recommendation.run_session_id == run_session_id
                )
                query = self._apply_filters(
                    query, analysis_mode, signal_type, confidence_threshold, final_score_threshold
                )
                query = query.order_by(Recommendation.created_at)

                recommendations = session.exec(query).all()

                # Deduplicate by ticker+analysis_date, keeping best recommendation
                deduplicated = self._deduplicate_recommendations(recommendations)

                # Convert to InvestmentSignal objects
                return [self._to_investment_signal(rec) for rec in deduplicated]

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error retrieving recommendations for session {run_session_id}: {e}")
            return []

    def get_recommendations_by_date(
        self,
        report_date: date | str,
        analysis_mode: str | None = None,
        signal_type: str | None = None,
        confidence_threshold: float | None = None,
        final_score_threshold: float | None = None,
    ) -> list:
        """Get all recommendations created on a specific date for report generation.

        Args:
            report_date: Date when report is being generated (date object or YYYY-MM-DD string).
                        Retrieves recommendations created on this date, regardless of analysis_date.
            analysis_mode: Filter by analysis mode ('llm' or 'rule_based').
            signal_type: Filter by signal type (e.g., 'strong_buy', 'buy', 'hold').
            confidence_threshold: Minimum confidence score (e.g., 70 means confidence > 70).
            final_score_threshold: Minimum final score (e.g., 70 means final_score > 70).

        Returns:
            List of InvestmentSignal Pydantic models (deduplicated by ticker+analysis_date).
        """
        try:
            # Convert string to date if needed
            if isinstance(report_date, str):
                report_date = datetime.strptime(report_date, "%Y-%m-%d").date()

            session = self.db_manager.get_session()
            try:
                # Build query with filters
                query = select(Recommendation).where(Recommendation.analysis_date == report_date)
                query = self._apply_filters(
                    query, analysis_mode, signal_type, confidence_threshold, final_score_threshold
                )
                query = query.order_by(Recommendation.created_at)

                recommendations = session.exec(query).all()

                # Deduplicate by ticker+analysis_date, keeping best recommendation
                deduplicated = self._deduplicate_recommendations(recommendations)

                # Convert to InvestmentSignal objects
                return [self._to_investment_signal(rec) for rec in deduplicated]

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error retrieving recommendations for date {report_date}: {e}")
            return []

    def _apply_filters(
        self,
        query,
        analysis_mode: str | None = None,
        signal_type: str | None = None,
        confidence_threshold: float | None = None,
        final_score_threshold: float | None = None,
    ):
        """Apply common filters to a recommendation query.

        Args:
            query: SQLModel query to filter.
            analysis_mode: Filter by analysis mode ('llm' or 'rule_based').
            signal_type: Filter by signal type (e.g., 'strong_buy', 'buy', 'hold').
            confidence_threshold: Minimum confidence score (e.g., 70 means confidence > 70).
            final_score_threshold: Minimum final score (e.g., 70 means final_score > 70).

        Returns:
            Filtered query.
        """
        if analysis_mode:
            query = query.where(Recommendation.analysis_mode == analysis_mode)
        if signal_type:
            query = query.where(Recommendation.signal_type == signal_type)
        if confidence_threshold is not None:
            query = query.where(Recommendation.confidence > confidence_threshold)
        if final_score_threshold is not None:
            query = query.where(Recommendation.final_score > final_score_threshold)
        return query

    def _deduplicate_recommendations(self, recommendations: list) -> list:
        """Deduplicate recommendations by ticker+analysis_date, keeping the best one.

        For each unique (ticker_id, analysis_date) combination, keeps only the recommendation
        with the highest final_score. If final_scores are equal, uses highest confidence.
        This ensures reports show only one recommendation per ticker per date.

        Args:
            recommendations: List of Recommendation database objects.

        Returns:
            List of deduplicated Recommendation objects sorted by final_score desc, confidence desc.
        """
        if not recommendations:
            return []

        # Group by (ticker_id, analysis_date)
        groups = {}
        for rec in recommendations:
            key = (rec.ticker_id, rec.analysis_date)
            if key not in groups:
                groups[key] = []
            groups[key].append(rec)

        # For each group, keep the best recommendation
        deduplicated = []
        for group_recs in groups.values():
            # Sort by final_score desc, then confidence desc
            best = sorted(group_recs, key=lambda r: (r.final_score, r.confidence), reverse=True)[0]
            deduplicated.append(best)

        # Sort final list by final_score and confidence for consistent ordering
        deduplicated.sort(key=lambda r: (r.final_score, r.confidence), reverse=True)

        initial_count = len(recommendations)
        final_count = len(deduplicated)
        if initial_count > final_count:
            logger.info(
                f"Deduplicated recommendations: {initial_count} -> {final_count} "
                f"({initial_count - final_count} duplicates removed)"
            )

        return deduplicated

    def get_existing_tickers_for_date(
        self, analysis_date: date | str, analysis_mode: str
    ) -> set[str]:
        """Get ticker symbols that already have recommendations for a specific date and mode.

        Args:
            analysis_date: Date to check (date object or YYYY-MM-DD string).
            analysis_mode: Analysis mode ('llm' or 'rule_based').

        Returns:
            Set of ticker symbols that already have recommendations.
        """
        try:
            # Convert string to date if needed
            if isinstance(analysis_date, str):
                analysis_date = datetime.strptime(analysis_date, "%Y-%m-%d").date()

            session = self.db_manager.get_session()
            try:
                # Query for existing recommendations
                query = (
                    select(Ticker.symbol)
                    .join(Recommendation, Recommendation.ticker_id == Ticker.id)
                    .where(
                        Recommendation.analysis_date == analysis_date,
                        Recommendation.analysis_mode == analysis_mode,
                    )
                    .distinct()
                )

                results = session.exec(query).all()
                return set(results)

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error checking existing recommendations: {e}")
            return set()

    def get_latest_recommendation(self, ticker: str) -> Recommendation | None:
        """Get most recent recommendation for a ticker.

        Args:
            ticker: Stock ticker symbol.

        Returns:
            Recommendation object or None if not found.
        """
        try:
            ticker = ticker.upper()
            session = self.db_manager.get_session()
            try:
                # Find ticker first
                ticker_obj = session.exec(select(Ticker).where(Ticker.symbol == ticker)).first()

                if not ticker_obj:
                    return None

                recommendation = session.exec(
                    select(Recommendation)
                    .where(Recommendation.ticker_id == ticker_obj.id)
                    .order_by(Recommendation.created_at.desc())
                ).first()

                return recommendation

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error retrieving latest recommendation for {ticker}: {e}")
            return None

    def get_recommendations_by_ticker(self, ticker: str) -> list[dict]:
        """Get all recommendations for a specific ticker.

        Args:
            ticker: Stock ticker symbol.

        Returns:
            List of recommendation dictionaries with relevant fields.
        """
        try:
            ticker = ticker.upper()
            session = self.db_manager.get_session()
            try:
                # Find ticker first
                ticker_obj = session.exec(select(Ticker).where(Ticker.symbol == ticker)).first()

                if not ticker_obj:
                    logger.warning(f"Ticker not found: {ticker}")
                    return []

                recommendations = session.exec(
                    select(Recommendation)
                    .where(Recommendation.ticker_id == ticker_obj.id)
                    .order_by(Recommendation.analysis_date.desc())
                ).all()

                # Convert to dicts with key fields
                result = []
                for rec in recommendations:
                    result.append(
                        {
                            "id": rec.id,
                            "ticker": ticker,
                            "recommendation": rec.signal_type,
                            "confidence": rec.confidence,
                            "current_price": rec.current_price,
                            "analysis_date": (
                                rec.analysis_date.isoformat() if rec.analysis_date else None
                            ),
                            "analysis_mode": rec.analysis_mode,
                            "reasoning": rec.rationale,
                        }
                    )

                return result

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error retrieving recommendations for ticker {ticker}: {e}")
            return []

    def get_recommendation_by_id(self, recommendation_id: int) -> dict | None:
        """Get a single recommendation by ID.

        Args:
            recommendation_id: Recommendation ID.

        Returns:
            Dictionary with recommendation details or None if not found.
        """
        try:
            session = self.db_manager.get_session()
            try:
                recommendation = session.exec(
                    select(Recommendation, Ticker)
                    .join(Ticker, Recommendation.ticker_id == Ticker.id)
                    .where(Recommendation.id == recommendation_id)
                ).first()

                if not recommendation:
                    return None

                rec, ticker = recommendation

                return {
                    "id": rec.id,
                    "ticker": ticker.symbol,
                    "name": ticker.name,
                    "recommendation": rec.signal_type,
                    "confidence": rec.confidence,
                    "current_price": rec.current_price,
                    "analysis_date": rec.analysis_date.isoformat() if rec.analysis_date else None,
                    "analysis_mode": rec.analysis_mode,
                    "reasoning": rec.rationale,
                }

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error retrieving recommendation {recommendation_id}: {e}")
            return None

    def get_recent_analysis_dates(self, limit: int = 10) -> list[dict]:
        """Get recent analysis dates with signal counts.

        This method retrieves distinct analysis dates from recommendations,
        ordered by most recent first, with the count of signals for each date.

        Args:
            limit: Maximum number of dates to return

        Returns:
            List of dicts with 'date' and 'signals_count' keys
        """
        try:
            session = self.db_manager.get_session()
            try:
                from sqlalchemy import func

                # Query to get distinct analysis dates with counts
                stmt = (
                    select(
                        Recommendation.analysis_date,
                        func.count(Recommendation.id).label("count"),
                    )
                    .group_by(Recommendation.analysis_date)
                    .order_by(Recommendation.analysis_date.desc())
                    .limit(limit)
                )

                results = session.exec(stmt).all()

                return [
                    {"date": result[0].isoformat(), "signals_count": result[1]}
                    for result in results
                ]

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error retrieving recent analysis dates: {e}")
            return []


class PerformanceRepository:
    """Repository for tracking recommendation performance.

    Provides methods for storing price tracking data, calculating performance metrics,
    and generating performance reports.
    """

    def __init__(self, db_path: Path | str = "data/falconsignals.db"):
        """Initialize repository with database manager.

        Args:
            db_path: Path to SQLite database file.
        """
        self.db_manager = DatabaseManager(db_path)
        self.db_manager.initialize()

    def track_price(
        self,
        recommendation_id: int,
        tracking_date: date,
        price: float,
        benchmark_price: float | None = None,
        benchmark_ticker: str = "SPY",
    ) -> bool:
        """Record price at specific date for performance tracking.

        Args:
            recommendation_id: Integer ID of the recommendation.
            tracking_date: Date when price was tracked.
            price: Stock price on tracking date.
            benchmark_price: Benchmark price on tracking date.
            benchmark_ticker: Benchmark ticker symbol (default: SPY).

        Returns:
            True if successful, False otherwise.
        """
        try:
            session = self.db_manager.get_session()
            try:
                # Check if recommendation exists
                recommendation = session.exec(
                    select(Recommendation).where(Recommendation.id == recommendation_id)
                ).first()

                if not recommendation:
                    logger.warning(f"Recommendation not found: {recommendation_id}")
                    return False

                # Calculate days since recommendation
                days_since = (tracking_date - recommendation.analysis_date).days

                # Calculate price change percentage
                price_change_pct = (
                    ((price - recommendation.current_price) / recommendation.current_price) * 100
                    if recommendation.current_price > 0
                    else None
                )

                # Get initial benchmark price from first tracking record or store it
                initial_benchmark = self._get_initial_benchmark_price(
                    session, recommendation_id, benchmark_price, benchmark_ticker
                )

                # Calculate benchmark change percentage
                benchmark_change_pct = None
                alpha = None
                if benchmark_price and initial_benchmark:
                    benchmark_change_pct = (
                        ((benchmark_price - initial_benchmark) / initial_benchmark) * 100
                        if initial_benchmark > 0
                        else None
                    )
                    if price_change_pct is not None and benchmark_change_pct is not None:
                        alpha = price_change_pct - benchmark_change_pct

                # Check if tracking record exists (upsert pattern)
                existing = session.exec(
                    select(PriceTracking).where(
                        (PriceTracking.recommendation_id == recommendation_id)
                        & (PriceTracking.tracking_date == tracking_date)
                    )
                ).first()

                if existing:
                    # Update existing
                    existing.price = price
                    existing.price_change_pct = price_change_pct
                    existing.days_since_recommendation = days_since
                    existing.benchmark_price = benchmark_price
                    existing.benchmark_change_pct = benchmark_change_pct
                    existing.alpha = alpha
                    session.add(existing)
                else:
                    # Create new
                    price_tracking = PriceTracking(
                        recommendation_id=recommendation_id,
                        tracking_date=tracking_date,
                        days_since_recommendation=days_since,
                        price=price,
                        price_change_pct=price_change_pct,
                        benchmark_ticker=benchmark_ticker,
                        benchmark_price=benchmark_price,
                        benchmark_change_pct=benchmark_change_pct,
                        alpha=alpha,
                    )
                    session.add(price_tracking)

                session.commit()
                logger.debug(
                    f"Tracked price for recommendation {recommendation_id} on {tracking_date}"
                )
                return True

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error tracking price for recommendation {recommendation_id}: {e}")
            return False

    def _get_initial_benchmark_price(
        self, session, recommendation_id: int, current_benchmark_price: float | None, ticker: str
    ) -> float | None:
        """Get initial benchmark price at time of recommendation.

        Looks for the earliest price tracking record to get the baseline benchmark price.
        If this is the first tracking, uses the current benchmark price as baseline.

        Args:
            session: Database session.
            recommendation_id: ID of the recommendation.
            current_benchmark_price: Current benchmark price.
            ticker: Benchmark ticker symbol.

        Returns:
            Initial benchmark price or None.
        """
        # Get the earliest tracking record for this recommendation
        earliest = session.exec(
            select(PriceTracking)
            .where(PriceTracking.recommendation_id == recommendation_id)
            .order_by(PriceTracking.tracking_date.asc())
        ).first()

        if earliest and earliest.benchmark_price:
            return earliest.benchmark_price

        # If no existing tracking or no benchmark price, use current as baseline
        return current_benchmark_price

    def get_performance_data(self, recommendation_id: int) -> list[PriceTracking]:
        """Get all price tracking data for a recommendation.

        Args:
            recommendation_id: Integer ID of the recommendation.

        Returns:
            List of PriceTracking objects.
        """
        try:
            session = self.db_manager.get_session()
            try:
                tracking_data = session.exec(
                    select(PriceTracking)
                    .where(PriceTracking.recommendation_id == recommendation_id)
                    .order_by(PriceTracking.tracking_date.asc())
                ).all()

                return list(tracking_data)

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error retrieving performance data for {recommendation_id}: {e}")
            return []

    def get_active_recommendations(
        self, max_age_days: int = 180, signal_types: list[str] | None = None
    ) -> list[Recommendation]:
        """Get active recommendations that should be tracked.

        Args:
            max_age_days: Maximum age of recommendations to track (default: 180 days).
            signal_types: Filter by signal types (e.g., ['buy', 'strong_buy']).

        Returns:
            List of Recommendation objects.
        """
        try:
            session = self.db_manager.get_session()
            try:
                # Calculate cutoff date
                cutoff_date = date.today() - timedelta(days=max_age_days)

                # Build query with eager loading of ticker relationship
                query = (
                    select(Recommendation)
                    .join(Ticker)
                    .where(Recommendation.analysis_date >= cutoff_date)
                )

                if signal_types:
                    query = query.where(Recommendation.signal_type.in_(signal_types))

                recommendations = session.exec(query).all()

                # Force load the ticker_obj relationship before closing session
                for rec in recommendations:
                    _ = rec.ticker_obj.symbol  # Access to force load

                return list(recommendations)

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error retrieving active recommendations: {e}")
            return []

    def update_performance_summary(
        self,
        ticker_id: int | None = None,
        signal_type: str | None = None,
        analysis_mode: str | None = None,
        period_days: int = 30,
    ) -> bool:
        """Calculate and store aggregated performance metrics.

        Args:
            ticker_id: Filter by ticker ID (None for overall summary).
            signal_type: Filter by signal type (None for all signals).
            analysis_mode: Filter by analysis mode (None for all modes).
            period_days: Tracking period in days (7, 30, 90, 180).

        Returns:
            True if successful, False otherwise.
        """
        try:
            session = self.db_manager.get_session()
            try:
                # Build query to get recommendations and their tracking data
                cutoff_date = date.today() - timedelta(days=period_days)

                # Base query for recommendations
                query = select(Recommendation).where(Recommendation.analysis_date >= cutoff_date)

                if ticker_id:
                    query = query.where(Recommendation.ticker_id == ticker_id)
                if signal_type:
                    query = query.where(Recommendation.signal_type == signal_type)
                if analysis_mode:
                    query = query.where(Recommendation.analysis_mode == analysis_mode)

                recommendations = session.exec(query).all()

                if not recommendations:
                    logger.info("No recommendations found for performance summary")
                    return True

                # Collect performance metrics
                returns = []
                alphas = []
                confidences = []
                wins = 0

                for rec in recommendations:
                    # Get latest tracking data for this recommendation
                    latest_tracking = session.exec(
                        select(PriceTracking)
                        .where(PriceTracking.recommendation_id == rec.id)
                        .order_by(PriceTracking.tracking_date.desc())
                    ).first()

                    if latest_tracking and latest_tracking.price_change_pct is not None:
                        returns.append(latest_tracking.price_change_pct)
                        if latest_tracking.price_change_pct > 0:
                            wins += 1
                        if latest_tracking.alpha is not None:
                            alphas.append(latest_tracking.alpha)

                    confidences.append(rec.confidence)

                # Calculate metrics
                total_recommendations = len(recommendations)
                avg_return = statistics.mean(returns) if returns else None
                median_return = statistics.median(returns) if returns else None
                win_rate = (wins / len(returns) * 100) if returns else None
                avg_alpha = statistics.mean(alphas) if alphas else None

                # Sharpe ratio (simplified - assumes risk-free rate of 0)
                sharpe_ratio = None
                if returns and len(returns) > 1:
                    std_dev = statistics.stdev(returns)
                    sharpe_ratio = (avg_return / std_dev) if std_dev > 0 else None

                # Max drawdown (simplified)
                max_drawdown = min(returns) if returns else None

                # Confidence calibration
                avg_confidence = statistics.mean(confidences) if confidences else None
                actual_win_rate = win_rate
                calibration_error = (
                    abs(avg_confidence - actual_win_rate)
                    if avg_confidence and actual_win_rate
                    else None
                )

                # Store or update summary
                # Build WHERE conditions - handle NULL properly
                where_conditions = [PerformanceSummary.period_days == period_days]

                if ticker_id is not None:
                    where_conditions.append(PerformanceSummary.ticker_id == ticker_id)
                else:
                    where_conditions.append(PerformanceSummary.ticker_id.is_(None))

                if signal_type is not None:
                    where_conditions.append(PerformanceSummary.signal_type == signal_type)
                else:
                    where_conditions.append(PerformanceSummary.signal_type.is_(None))

                if analysis_mode is not None:
                    where_conditions.append(PerformanceSummary.analysis_mode == analysis_mode)
                else:
                    where_conditions.append(PerformanceSummary.analysis_mode.is_(None))

                existing = session.exec(
                    select(PerformanceSummary).where(and_(*where_conditions))
                ).first()

                if existing:
                    # Update
                    existing.total_recommendations = total_recommendations
                    existing.avg_return = avg_return
                    existing.median_return = median_return
                    existing.win_rate = win_rate
                    existing.avg_alpha = avg_alpha
                    existing.sharpe_ratio = sharpe_ratio
                    existing.max_drawdown = max_drawdown
                    existing.avg_confidence = avg_confidence
                    existing.actual_win_rate = actual_win_rate
                    existing.calibration_error = calibration_error
                    existing.updated_at = datetime.now()
                    session.add(existing)
                else:
                    # Create new
                    summary = PerformanceSummary(
                        ticker_id=ticker_id,
                        signal_type=signal_type,
                        analysis_mode=analysis_mode,
                        period_days=period_days,
                        total_recommendations=total_recommendations,
                        avg_return=avg_return,
                        median_return=median_return,
                        win_rate=win_rate,
                        avg_alpha=avg_alpha,
                        sharpe_ratio=sharpe_ratio,
                        max_drawdown=max_drawdown,
                        avg_confidence=avg_confidence,
                        actual_win_rate=actual_win_rate,
                        calibration_error=calibration_error,
                    )
                    session.add(summary)

                session.commit()
                logger.info(f"Updated performance summary for period: {period_days} days")
                return True

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error updating performance summary: {e}")
            return False

    def get_performance_report(
        self,
        ticker_symbol: str | None = None,
        signal_type: str | None = None,
        analysis_mode: str | None = None,
        period_days: int = 30,
    ) -> dict:
        """Generate performance report with statistics.

        Args:
            ticker_symbol: Filter by ticker symbol (None for all tickers).
            signal_type: Filter by signal type (None for all signals).
            analysis_mode: Filter by analysis mode (None for all modes).
            period_days: Tracking period in days.

        Returns:
            Dictionary with performance statistics.
        """
        try:
            session = self.db_manager.get_session()
            try:
                # Get ticker ID if symbol provided
                ticker_id = None
                if ticker_symbol:
                    ticker = session.exec(
                        select(Ticker).where(Ticker.symbol == ticker_symbol.upper())
                    ).first()
                    if ticker:
                        ticker_id = ticker.id
                    else:
                        logger.warning(f"Ticker not found: {ticker_symbol}")
                        return {}

                # Get performance summary
                query = select(PerformanceSummary).where(
                    PerformanceSummary.period_days == period_days
                )

                if ticker_id:
                    query = query.where(PerformanceSummary.ticker_id == ticker_id)
                if signal_type:
                    query = query.where(PerformanceSummary.signal_type == signal_type)
                if analysis_mode:
                    query = query.where(PerformanceSummary.analysis_mode == analysis_mode)

                summaries = session.exec(query).all()

                if not summaries:
                    return {
                        "period_days": period_days,
                        "ticker": ticker_symbol,
                        "signal_type": signal_type,
                        "analysis_mode": analysis_mode,
                        "message": "No performance data available",
                    }

                # Aggregate if multiple summaries
                report = {
                    "period_days": period_days,
                    "ticker": ticker_symbol,
                    "signal_type": signal_type,
                    "analysis_mode": analysis_mode,
                    "total_recommendations": sum(s.total_recommendations for s in summaries),
                }

                # Safely aggregate metrics (handle None values)
                avg_returns = [s.avg_return for s in summaries if s.avg_return is not None]
                report["avg_return"] = sum(avg_returns) / len(avg_returns) if avg_returns else None

                median_returns = [s.median_return for s in summaries if s.median_return is not None]
                report["median_return"] = (
                    sum(median_returns) / len(median_returns) if median_returns else None
                )

                win_rates = [s.win_rate for s in summaries if s.win_rate is not None]
                report["win_rate"] = sum(win_rates) / len(win_rates) if win_rates else None

                alphas = [s.avg_alpha for s in summaries if s.avg_alpha is not None]
                report["avg_alpha"] = sum(alphas) / len(alphas) if alphas else None

                sharpe_ratios = [s.sharpe_ratio for s in summaries if s.sharpe_ratio is not None]
                report["sharpe_ratio"] = (
                    sum(sharpe_ratios) / len(sharpe_ratios) if sharpe_ratios else None
                )

                drawdowns = [s.max_drawdown for s in summaries if s.max_drawdown is not None]
                report["max_drawdown"] = min(drawdowns) if drawdowns else None

                confidences = [s.avg_confidence for s in summaries if s.avg_confidence is not None]
                report["avg_confidence"] = (
                    sum(confidences) / len(confidences) if confidences else None
                )

                calibration_errors = [
                    s.calibration_error for s in summaries if s.calibration_error is not None
                ]
                report["calibration_error"] = (
                    sum(calibration_errors) / len(calibration_errors)
                    if calibration_errors
                    else None
                )

                return report

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error generating performance report: {e}")
            return {}


class WatchlistRepository:
    """Repository for managing watchlist operations.

    Handles adding, removing, and querying tickers in the watchlist.
    """

    def __init__(self, db_path: Path | str = "data/falconsignals.db"):
        """Initialize repository with database manager.

        Args:
            db_path: Path to SQLite database file.
        """
        self.db_manager = DatabaseManager(db_path)
        self.db_manager.initialize()

    def add_to_watchlist(
        self, ticker_symbol: str, recommendation_id: int | None = None
    ) -> tuple[bool, str]:
        """Add ticker to watchlist.

        Args:
            ticker_symbol: Ticker symbol to add.
            recommendation_id: Optional recommendation ID to associate.
                If not provided, will use the first recommendation for the ticker.

        Returns:
            Tuple of (success, message).
        """
        try:
            session = self.db_manager.get_session()

            try:
                ticker_symbol = ticker_symbol.upper()

                # Get or create ticker
                ticker = get_or_create_ticker(session, ticker_symbol)

                # Check if ticker already in watchlist
                existing = session.exec(
                    select(Watchlist).where(Watchlist.ticker_id == ticker.id)
                ).first()

                if existing:
                    return False, f"{ticker_symbol} is already in watchlist"

                # If no recommendation_id provided, fetch first recommendation for this ticker
                if recommendation_id is None:
                    first_rec = session.exec(
                        select(Recommendation)
                        .where(Recommendation.ticker_id == ticker.id)
                        .order_by(Recommendation.analysis_date)
                    ).first()
                    if first_rec:
                        recommendation_id = first_rec.id

                # Create watchlist entry
                watchlist_entry = Watchlist(
                    ticker_id=ticker.id, recommendation_id=recommendation_id
                )
                session.add(watchlist_entry)
                session.commit()

                return True, f"Added {ticker_symbol} to watchlist"

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error adding {ticker_symbol} to watchlist: {e}")
            return False, f"Error: {str(e)}"

    def remove_from_watchlist(self, ticker_symbol: str) -> tuple[bool, str]:
        """Remove ticker from watchlist.

        Args:
            ticker_symbol: Ticker symbol to remove.

        Returns:
            Tuple of (success, message).
        """
        try:
            session = self.db_manager.get_session()

            try:
                ticker_symbol = ticker_symbol.upper()

                # Find ticker
                ticker = session.exec(select(Ticker).where(Ticker.symbol == ticker_symbol)).first()

                if not ticker:
                    return False, f"Ticker {ticker_symbol} not found"

                # Find and delete watchlist entry
                watchlist_entry = session.exec(
                    select(Watchlist).where(Watchlist.ticker_id == ticker.id)
                ).first()

                if not watchlist_entry:
                    return False, f"{ticker_symbol} is not in watchlist"

                session.delete(watchlist_entry)
                session.commit()

                return True, f"Removed {ticker_symbol} from watchlist"

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error removing {ticker_symbol} from watchlist: {e}")
            return False, f"Error: {str(e)}"

    def get_watchlist(self) -> list[dict]:
        """Get all tickers in watchlist.

        Returns:
            List of dictionaries with ticker info.
        """
        try:
            session = self.db_manager.get_session()

            try:
                statement = select(Watchlist, Ticker).join(Ticker).order_by(Watchlist.created_at)
                results = session.exec(statement).all()

                watchlist = []
                for watchlist_entry, ticker in results:
                    watchlist.append(
                        {
                            "ticker": ticker.symbol,
                            "name": ticker.name,
                            "recommendation_id": watchlist_entry.recommendation_id,
                            "created_at": watchlist_entry.created_at,
                        }
                    )

                return watchlist

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error getting watchlist: {e}")
            return []

    def ticker_exists(self, ticker_symbol: str) -> bool:
        """Check if ticker exists in watchlist.

        Args:
            ticker_symbol: Ticker symbol to check.

        Returns:
            True if ticker is in watchlist.
        """
        try:
            session = self.db_manager.get_session()

            try:
                ticker_symbol = ticker_symbol.upper()

                ticker = session.exec(select(Ticker).where(Ticker.symbol == ticker_symbol)).first()

                if not ticker:
                    return False

                existing = session.exec(
                    select(Watchlist).where(Watchlist.ticker_id == ticker.id)
                ).first()

                return existing is not None

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error checking watchlist for {ticker_symbol}: {e}")
            return False


class WatchlistSignalRepository:
    """Repository for managing watchlist technical analysis signals.

    Stores periodic technical analysis results for watchlist tickers to help
    identify optimal entry points for opening positions.
    """

    def __init__(self, db_path: Path | str = "data/falconsignals.db"):
        """Initialize repository with database manager.

        Args:
            db_path: Path to SQLite database file.
        """
        self.db_manager = DatabaseManager(db_path)
        self.db_manager.initialize()

    def store_signal(
        self,
        ticker_symbol: str,
        analysis_date: date,
        score: float,
        confidence: float,
        current_price: float,
        rationale: str | None = None,
        action: str | None = None,
        currency: str = "USD",
        entry_price: float | None = None,
        stop_loss: float | None = None,
        take_profit: float | None = None,
        wait_for_price: float | None = None,
    ) -> tuple[bool, str]:
        """Store technical analysis signal for a watchlist ticker.

        Args:
            ticker_symbol: Ticker symbol (must be in watchlist).
            analysis_date: Date when analysis was performed.
            score: Technical analysis score (0-100).
            confidence: Confidence level (0-100).
            current_price: Stock price at time of analysis.
            rationale: Explanation of the technical analysis.
            action: Suggested action (Buy, Wait, Remove).
            currency: Price currency (default: USD).
            entry_price: Suggested entry price for Buy actions.
            stop_loss: Suggested stop loss level for Buy actions.
            take_profit: Suggested take profit target for Buy actions.
            wait_for_price: Price level to wait for if action is Wait.

        Returns:
            Tuple of (success, message).
        """
        try:
            session = self.db_manager.get_session()

            try:
                ticker_symbol = ticker_symbol.upper()

                # Find ticker and verify it's in watchlist
                ticker = session.exec(select(Ticker).where(Ticker.symbol == ticker_symbol)).first()

                if not ticker:
                    return False, f"Ticker {ticker_symbol} not found"

                watchlist_entry = session.exec(
                    select(Watchlist).where(Watchlist.ticker_id == ticker.id)
                ).first()

                if not watchlist_entry:
                    return False, f"{ticker_symbol} is not in watchlist"

                # Check if signal already exists for this ticker and date (upsert pattern)
                existing = session.exec(
                    select(WatchlistSignal).where(
                        (WatchlistSignal.ticker_id == ticker.id)
                        & (WatchlistSignal.analysis_date == analysis_date)
                    )
                ).first()

                if existing:
                    # Update existing signal
                    existing.score = score
                    existing.confidence = confidence
                    existing.current_price = current_price
                    existing.currency = currency
                    existing.rationale = rationale
                    existing.action = action
                    existing.entry_price = entry_price
                    existing.stop_loss = stop_loss
                    existing.take_profit = take_profit
                    existing.wait_for_price = wait_for_price
                    existing.watchlist_id = watchlist_entry.id  # Update in case it changed
                    session.add(existing)
                    message = f"Updated signal for {ticker_symbol} on {analysis_date}"
                else:
                    # Create new signal
                    signal = WatchlistSignal(
                        ticker_id=ticker.id,
                        watchlist_id=watchlist_entry.id,
                        analysis_date=analysis_date,
                        score=score,
                        confidence=confidence,
                        current_price=current_price,
                        currency=currency,
                        rationale=rationale,
                        action=action,
                        entry_price=entry_price,
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                        wait_for_price=wait_for_price,
                    )
                    session.add(signal)
                    message = f"Stored signal for {ticker_symbol} on {analysis_date}"

                session.commit()
                logger.debug(message)
                return True, message

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error storing signal for {ticker_symbol}: {e}")
            return False, f"Error: {str(e)}"

    def get_latest_signal(self, ticker_symbol: str) -> dict | None:
        """Get the most recent technical analysis signal for a ticker.

        Args:
            ticker_symbol: Ticker symbol.

        Returns:
            Dictionary with signal details or None if not found.
        """
        try:
            session = self.db_manager.get_session()

            try:
                ticker_symbol = ticker_symbol.upper()

                # Find ticker
                ticker = session.exec(select(Ticker).where(Ticker.symbol == ticker_symbol)).first()

                if not ticker:
                    return None

                # Get latest signal
                signal = session.exec(
                    select(WatchlistSignal)
                    .where(WatchlistSignal.ticker_id == ticker.id)
                    .order_by(WatchlistSignal.analysis_date.desc())
                ).first()

                if not signal:
                    return None

                return {
                    "id": signal.id,
                    "ticker": ticker_symbol,
                    "analysis_date": signal.analysis_date,
                    "score": signal.score,
                    "confidence": signal.confidence,
                    "current_price": signal.current_price,
                    "currency": signal.currency,
                    "rationale": signal.rationale,
                    "action": signal.action,
                    "entry_price": signal.entry_price,
                    "stop_loss": signal.stop_loss,
                    "take_profit": signal.take_profit,
                    "wait_for_price": signal.wait_for_price,
                    "created_at": signal.created_at,
                }

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error getting latest signal for {ticker_symbol}: {e}")
            return None

    def get_signal_history(self, ticker_symbol: str, days_back: int = 30) -> list[dict]:
        """Get historical technical analysis signals for a ticker.

        Args:
            ticker_symbol: Ticker symbol.
            days_back: Number of days of history to retrieve (default: 30).

        Returns:
            List of signal dictionaries, ordered by date descending.
        """
        try:
            session = self.db_manager.get_session()

            try:
                ticker_symbol = ticker_symbol.upper()

                # Find ticker
                ticker = session.exec(select(Ticker).where(Ticker.symbol == ticker_symbol)).first()

                if not ticker:
                    return []

                # Calculate cutoff date
                cutoff_date = date.today() - timedelta(days=days_back)

                # Get signals
                signals = session.exec(
                    select(WatchlistSignal)
                    .where(
                        (WatchlistSignal.ticker_id == ticker.id)
                        & (WatchlistSignal.analysis_date >= cutoff_date)
                    )
                    .order_by(WatchlistSignal.analysis_date.desc())
                ).all()

                return [
                    {
                        "id": signal.id,
                        "ticker": ticker_symbol,
                        "analysis_date": signal.analysis_date,
                        "score": signal.score,
                        "confidence": signal.confidence,
                        "current_price": signal.current_price,
                        "currency": signal.currency,
                        "rationale": signal.rationale,
                        "action": signal.action,
                        "entry_price": signal.entry_price,
                        "stop_loss": signal.stop_loss,
                        "take_profit": signal.take_profit,
                        "wait_for_price": signal.wait_for_price,
                        "created_at": signal.created_at,
                    }
                    for signal in signals
                ]

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error getting signal history for {ticker_symbol}: {e}")
            return []

    def get_signals_for_watchlist_id(self, watchlist_id: int) -> list[dict]:
        """Get all signals associated with a specific watchlist entry.

        Args:
            watchlist_id: Watchlist entry ID.

        Returns:
            List of signal dictionaries, ordered by date descending.
        """
        try:
            session = self.db_manager.get_session()

            try:
                signals = session.exec(
                    select(WatchlistSignal, Ticker)
                    .join(Ticker, WatchlistSignal.ticker_id == Ticker.id)
                    .where(WatchlistSignal.watchlist_id == watchlist_id)
                    .order_by(WatchlistSignal.analysis_date.desc())
                ).all()

                return [
                    {
                        "id": signal.id,
                        "ticker": ticker.symbol,
                        "name": ticker.name,
                        "analysis_date": signal.analysis_date,
                        "score": signal.score,
                        "confidence": signal.confidence,
                        "current_price": signal.current_price,
                        "currency": signal.currency,
                        "rationale": signal.rationale,
                        "created_at": signal.created_at,
                    }
                    for signal, ticker in signals
                ]

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error getting signals for watchlist {watchlist_id}: {e}")
            return []

    def delete_old_signals(self, days_old: int = 90) -> tuple[int, str]:
        """Delete signals older than specified number of days.

        Args:
            days_old: Delete signals older than this many days (default: 90).

        Returns:
            Tuple of (count_deleted, message).
        """
        try:
            session = self.db_manager.get_session()

            try:
                cutoff_date = date.today() - timedelta(days=days_old)

                # Find old signals
                old_signals = session.exec(
                    select(WatchlistSignal).where(WatchlistSignal.analysis_date < cutoff_date)
                ).all()

                count = len(old_signals)

                if count == 0:
                    return 0, "No old signals to delete"

                # Delete them
                for signal in old_signals:
                    session.delete(signal)

                session.commit()
                message = f"Deleted {count} signals older than {days_old} days"
                logger.info(message)
                return count, message

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error deleting old signals: {e}")
            return 0, f"Error: {str(e)}"

    def get_watchlist_with_latest_signals(self) -> list[dict]:
        """Get all watchlist tickers with their most recent signal scores.

        Useful for dashboard views showing current status of all watched tickers.

        Returns:
            List of dictionaries with ticker info and latest signal (if available).
        """
        try:
            session = self.db_manager.get_session()

            try:
                # Get all watchlist entries with tickers
                watchlist_entries = session.exec(
                    select(Watchlist, Ticker)
                    .join(Ticker, Watchlist.ticker_id == Ticker.id)
                    .order_by(Ticker.symbol)
                ).all()

                result = []
                for watchlist_entry, ticker in watchlist_entries:
                    # Get latest signal for this ticker
                    latest_signal = session.exec(
                        select(WatchlistSignal)
                        .where(WatchlistSignal.ticker_id == ticker.id)
                        .order_by(WatchlistSignal.analysis_date.desc())
                    ).first()

                    entry_data = {
                        "ticker": ticker.symbol,
                        "name": ticker.name,
                        "watchlist_id": watchlist_entry.id,
                        "added_to_watchlist": watchlist_entry.created_at,
                        "latest_signal": None,
                    }

                    if latest_signal:
                        entry_data["latest_signal"] = {
                            "analysis_date": latest_signal.analysis_date,
                            "score": latest_signal.score,
                            "confidence": latest_signal.confidence,
                            "current_price": latest_signal.current_price,
                            "currency": latest_signal.currency,
                            "rationale": latest_signal.rationale,
                            "action": latest_signal.action,
                            "entry_price": latest_signal.entry_price,
                            "stop_loss": latest_signal.stop_loss,
                            "take_profit": latest_signal.take_profit,
                            "wait_for_price": latest_signal.wait_for_price,
                        }

                    result.append(entry_data)

                return result

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error getting watchlist with latest signals: {e}")
            return []


"""TradingJournalRepository implementation to append to repository.py"""


class TradingJournalRepository:
    """Repository for managing trading journal operations.

    Handles creating, updating, and querying trade records for both open and closed positions.
    Automatically calculates P&L metrics and maintains trade history.
    """

    def __init__(self, db_path: Path | str = "data/falconsignals.db"):
        """Initialize repository with database manager.

        Args:
            db_path: Path to SQLite database file.
        """
        self.db_manager = DatabaseManager(db_path)
        self.db_manager.initialize()

    def create_trade(
        self,
        ticker_symbol: str,
        entry_date: date,
        entry_price: float,
        position_size: float,
        position_type: str = "long",
        fees_entry: float = 0.0,
        stop_loss: float | None = None,
        take_profit: float | None = None,
        recommendation_id: int | None = None,
        currency: str = "USD",
        description: str | None = None,
    ) -> tuple[bool, str, int | None]:
        """Create a new trade entry.

        Args:
            ticker_symbol: Ticker symbol (e.g., 'AAPL').
            entry_date: Date when position was opened.
            entry_price: Price per share/unit at entry.
            position_size: Number of shares/units.
            position_type: Position type ('long' or 'short').
            fees_entry: Fees paid at entry (default: 0.0).
            stop_loss: Stop loss price level (optional).
            take_profit: Take profit price level (optional).
            recommendation_id: Optional link to recommendation that triggered trade.
            currency: Trading currency (default: 'USD').
            description: Notes about the trade (optional).

        Returns:
            Tuple of (success: bool, message: str, trade_id: int | None).
        """
        try:
            # Validate position type
            if position_type not in ["long", "short"]:
                return (
                    False,
                    f"Invalid position type: {position_type}. Must be 'long' or 'short'",
                    None,
                )

            # Validate numeric values
            if entry_price <= 0:
                return False, "Entry price must be positive", None
            if position_size <= 0:
                return False, "Position size must be positive", None
            if fees_entry < 0:
                return False, "Entry fees cannot be negative", None

            session = self.db_manager.get_session()
            try:
                # Get or create ticker
                ticker = get_or_create_ticker(session, ticker_symbol)

                # Calculate total entry amount
                total_entry_amount = (entry_price * position_size) + fees_entry

                # Create trade record
                trade = TradingJournal(
                    ticker_id=ticker.id,
                    recommendation_id=recommendation_id,
                    entry_date=entry_date,
                    entry_price=entry_price,
                    position_size=position_size,
                    position_type=position_type,
                    fees_entry=fees_entry,
                    total_entry_amount=total_entry_amount,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    status="open",
                    currency=currency,
                    description=description,
                )

                session.add(trade)
                session.commit()
                session.refresh(trade)

                trade_id = trade.id
                logger.info(
                    f"Created trade: {ticker_symbol} {position_type} {position_size} @ {entry_price} (ID: {trade_id})"
                )
                return True, f"Trade created successfully for {ticker_symbol}", trade_id

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Failed to create trade: {e}")
            return False, f"Error creating trade: {e}", None

    def update_trade(
        self,
        trade_id: int,
        stop_loss: float | None = None,
        take_profit: float | None = None,
        description: str | None = None,
    ) -> tuple[bool, str]:
        """Update trade details (for open trades only).

        Args:
            trade_id: Trade ID to update.
            stop_loss: New stop loss level (optional).
            take_profit: New take profit level (optional).
            description: New/updated description (optional).

        Returns:
            Tuple of (success: bool, message: str).
        """
        try:
            session = self.db_manager.get_session()
            try:
                # Get trade
                trade = session.get(TradingJournal, trade_id)
                if not trade:
                    return False, f"Trade {trade_id} not found"

                if trade.status != "open":
                    return False, f"Cannot update closed trade {trade_id}"

                # Update fields
                updated = False
                if stop_loss is not None:
                    trade.stop_loss = stop_loss
                    updated = True
                if take_profit is not None:
                    trade.take_profit = take_profit
                    updated = True
                if description is not None:
                    trade.description = description
                    updated = True

                if updated:
                    trade.updated_at = datetime.now()
                    session.commit()
                    logger.info(f"Updated trade {trade_id}")
                    return True, f"Trade {trade_id} updated successfully"
                else:
                    return True, "No changes made"

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Failed to update trade {trade_id}: {e}")
            return False, f"Error updating trade: {e}"

    def close_trade(
        self,
        trade_id: int,
        exit_date: date,
        exit_price: float,
        fees_exit: float = 0.0,
    ) -> tuple[bool, str, float | None]:
        """Close an open trade and calculate P&L.

        Args:
            trade_id: Trade ID to close.
            exit_date: Date when position was closed.
            exit_price: Price per share/unit at exit.
            fees_exit: Fees paid at exit (default: 0.0).

        Returns:
            Tuple of (success: bool, message: str, profit_loss: float | None).
        """
        try:
            # Validate inputs
            if exit_price <= 0:
                return False, "Exit price must be positive", None
            if fees_exit < 0:
                return False, "Exit fees cannot be negative", None

            session = self.db_manager.get_session()
            try:
                # Get trade
                trade = session.get(TradingJournal, trade_id)
                if not trade:
                    return False, f"Trade {trade_id} not found", None

                if trade.status == "closed":
                    return False, f"Trade {trade_id} is already closed", None

                # Calculate total exit amount
                total_exit_amount = (exit_price * trade.position_size) - fees_exit

                # Calculate P&L based on position type
                if trade.position_type == "long":
                    profit_loss = total_exit_amount - trade.total_entry_amount
                else:  # short
                    profit_loss = trade.total_entry_amount - total_exit_amount

                profit_loss_pct = (profit_loss / trade.total_entry_amount) * 100

                # Update trade
                trade.exit_date = exit_date
                trade.exit_price = exit_price
                trade.fees_exit = fees_exit
                trade.total_exit_amount = total_exit_amount
                trade.profit_loss = profit_loss
                trade.profit_loss_pct = profit_loss_pct
                trade.status = "closed"
                trade.updated_at = datetime.now()

                session.commit()

                ticker_symbol = trade.ticker_obj.symbol
                logger.info(
                    f"Closed trade {trade_id}: {ticker_symbol} P&L: {profit_loss:.2f} ({profit_loss_pct:.2f}%)"
                )
                return (
                    True,
                    f"Trade closed: P&L = {profit_loss:.2f} ({profit_loss_pct:.2f}%)",
                    profit_loss,
                )

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Failed to close trade {trade_id}: {e}")
            return False, f"Error closing trade: {e}", None

    def get_open_trades(self, ticker_symbol: str | None = None) -> list[dict]:
        """Get all open trades.

        Args:
            ticker_symbol: Optional filter by ticker symbol.

        Returns:
            List of trade dictionaries.
        """
        try:
            session = self.db_manager.get_session()
            try:
                query = (
                    select(TradingJournal, Ticker)
                    .join(Ticker, TradingJournal.ticker_id == Ticker.id)
                    .where(TradingJournal.status == "open")
                )

                if ticker_symbol:
                    ticker_symbol = ticker_symbol.upper()
                    query = query.where(Ticker.symbol == ticker_symbol)

                query = query.order_by(TradingJournal.id.asc())
                results = session.exec(query).all()

                trades = []
                for trade, ticker in results:
                    trades.append(self._trade_to_dict(trade, ticker))

                return trades

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Failed to get open trades: {e}")
            return []

    def get_closed_trades(
        self,
        ticker_symbol: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[dict]:
        """Get closed trades with optional filters.

        Args:
            ticker_symbol: Optional filter by ticker symbol.
            start_date: Optional filter by exit date (inclusive).
            end_date: Optional filter by exit date (inclusive).

        Returns:
            List of trade dictionaries.
        """
        try:
            session = self.db_manager.get_session()
            try:
                query = (
                    select(TradingJournal, Ticker)
                    .join(Ticker, TradingJournal.ticker_id == Ticker.id)
                    .where(TradingJournal.status == "closed")
                )

                if ticker_symbol:
                    ticker_symbol = ticker_symbol.upper()
                    query = query.where(Ticker.symbol == ticker_symbol)

                if start_date:
                    query = query.where(TradingJournal.exit_date >= start_date)

                if end_date:
                    query = query.where(TradingJournal.exit_date <= end_date)

                query = query.order_by(TradingJournal.id.asc())
                results = session.exec(query).all()

                trades = []
                for trade, ticker in results:
                    trades.append(self._trade_to_dict(trade, ticker))

                return trades

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Failed to get closed trades: {e}")
            return []

    def get_all_trades(self, ticker_symbol: str | None = None) -> list[dict]:
        """Get all trades (both open and closed).

        Args:
            ticker_symbol: Optional filter by ticker symbol.

        Returns:
            List of trade dictionaries ordered by ID ascending.
        """
        try:
            session = self.db_manager.get_session()
            try:
                query = select(TradingJournal, Ticker).join(
                    Ticker, TradingJournal.ticker_id == Ticker.id
                )

                if ticker_symbol:
                    ticker_symbol = ticker_symbol.upper()
                    query = query.where(Ticker.symbol == ticker_symbol)

                query = query.order_by(TradingJournal.id.asc())
                results = session.exec(query).all()

                trades = []
                for trade, ticker in results:
                    trades.append(self._trade_to_dict(trade, ticker))

                return trades

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Failed to get all trades: {e}")
            return []

    def get_trade_by_id(self, trade_id: int) -> dict | None:
        """Get trade by ID.

        Args:
            trade_id: Trade ID.

        Returns:
            Trade dictionary or None if not found.
        """
        try:
            session = self.db_manager.get_session()
            try:
                query = (
                    select(TradingJournal, Ticker)
                    .join(Ticker, TradingJournal.ticker_id == Ticker.id)
                    .where(TradingJournal.id == trade_id)
                )
                result = session.exec(query).first()

                if result:
                    trade, ticker = result
                    return self._trade_to_dict(trade, ticker)
                return None

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Failed to get trade {trade_id}: {e}")
            return None

    def get_trade_history(self, ticker_symbol: str, limit: int = 50) -> list[dict]:
        """Get complete trade history for a ticker.

        Args:
            ticker_symbol: Ticker symbol.
            limit: Maximum number of trades to return (default: 50).

        Returns:
            List of trade dictionaries, sorted by entry date descending.
        """
        try:
            ticker_symbol = ticker_symbol.upper()
            session = self.db_manager.get_session()
            try:
                query = (
                    select(TradingJournal, Ticker)
                    .join(Ticker, TradingJournal.ticker_id == Ticker.id)
                    .where(Ticker.symbol == ticker_symbol)
                    .order_by(TradingJournal.entry_date.desc())
                    .limit(limit)
                )
                results = session.exec(query).all()

                trades = []
                for trade, ticker in results:
                    trades.append(self._trade_to_dict(trade, ticker))

                return trades

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Failed to get trade history for {ticker_symbol}: {e}")
            return []

    def get_performance_summary(self, ticker_symbol: str | None = None) -> dict:
        """Get performance summary for closed trades.

        Args:
            ticker_symbol: Optional filter by ticker symbol.

        Returns:
            Dictionary with performance metrics.
        """
        try:
            session = self.db_manager.get_session()
            try:
                query = select(TradingJournal).where(TradingJournal.status == "closed")

                if ticker_symbol:
                    ticker_symbol = ticker_symbol.upper()
                    query = query.join(Ticker, TradingJournal.ticker_id == Ticker.id).where(
                        Ticker.symbol == ticker_symbol
                    )

                trades = session.exec(query).all()

                if not trades:
                    return {
                        "total_trades": 0,
                        "total_profit_loss": 0.0,
                        "win_rate": 0.0,
                        "avg_profit_loss": 0.0,
                        "avg_profit_loss_pct": 0.0,
                        "total_fees": 0.0,
                    }

                profit_losses = [t.profit_loss for t in trades if t.profit_loss is not None]
                winning_trades = [p for p in profit_losses if p > 0]
                total_fees = sum((t.fees_entry or 0) + (t.fees_exit or 0) for t in trades)

                return {
                    "total_trades": len(trades),
                    "winning_trades": len(winning_trades),
                    "losing_trades": len(profit_losses) - len(winning_trades),
                    "win_rate": (len(winning_trades) / len(profit_losses) * 100)
                    if profit_losses
                    else 0.0,
                    "total_profit_loss": sum(profit_losses),
                    "avg_profit_loss": statistics.mean(profit_losses) if profit_losses else 0.0,
                    "avg_profit_loss_pct": statistics.mean(
                        [t.profit_loss_pct for t in trades if t.profit_loss_pct is not None]
                    )
                    if trades
                    else 0.0,
                    "best_trade": max(profit_losses) if profit_losses else 0.0,
                    "worst_trade": min(profit_losses) if profit_losses else 0.0,
                    "total_fees": total_fees,
                }

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Failed to get performance summary: {e}")
            return {}

    def _trade_to_dict(self, trade: TradingJournal, ticker: Ticker) -> dict:
        """Convert TradingJournal model to dictionary.

        Args:
            trade: TradingJournal object.
            ticker: Ticker object.

        Returns:
            Dictionary representation of trade.
        """
        return {
            "id": trade.id,
            "ticker_symbol": ticker.symbol,
            "ticker_name": ticker.name,
            "recommendation_id": trade.recommendation_id,
            "entry_date": trade.entry_date,
            "entry_price": trade.entry_price,
            "position_size": trade.position_size,
            "position_type": trade.position_type,
            "fees_entry": trade.fees_entry,
            "total_entry_amount": trade.total_entry_amount,
            "stop_loss": trade.stop_loss,
            "take_profit": trade.take_profit,
            "exit_date": trade.exit_date,
            "exit_price": trade.exit_price,
            "fees_exit": trade.fees_exit,
            "total_exit_amount": trade.total_exit_amount,
            "profit_loss": trade.profit_loss,
            "profit_loss_pct": trade.profit_loss_pct,
            "status": trade.status,
            "currency": trade.currency,
            "description": trade.description,
            "created_at": trade.created_at,
            "updated_at": trade.updated_at,
        }


class FundamentalSnapshotRepository:
    """Repository for storing and retrieving historical fundamental data snapshots.

    Stores comprehensive fundamental data from all sources (Alpha Vantage, Finnhub,
    Yahoo Finance) as daily snapshots for accurate historical backtesting.
    """

    def __init__(self, db_path: Path | str = "data/falconsignals.db"):
        """Initialize repository with database manager.

        Args:
            db_path: Path to SQLite database file.
        """
        self.db_manager = DatabaseManager(db_path)
        self.db_manager.initialize()

    def store_snapshot(self, ticker: str, snapshot_date: date, fundamental_data: dict) -> bool:
        """Store daily fundamental data snapshot.

        Args:
            ticker: Stock ticker symbol.
            snapshot_date: Date of snapshot.
            fundamental_data: Complete fundamental data dict from cache/provider.
                             Should contain: company_info, earnings_estimates,
                             analyst_data, price_context, metrics, etc.

        Returns:
            True if successful, False otherwise.
        """
        ticker = ticker.upper()

        try:
            session = self.db_manager.get_session()
            try:
                # Get or create ticker
                ticker_obj = get_or_create_ticker(session, ticker)

                # Create a copy of fundamental_data without the description field (to reduce storage size)
                data_to_store = fundamental_data.copy()
                if (
                    "company_info" in data_to_store
                    and "description" in data_to_store["company_info"]
                ):
                    data_to_store = json.loads(json.dumps(data_to_store))  # Deep copy
                    data_to_store["company_info"].pop("description", None)

                # Extract flattened metrics from fundamental_data
                company_info = fundamental_data.get("company_info", {})
                analyst_data = fundamental_data.get("analyst_data", {})
                price_context = fundamental_data.get("price_context", {})
                metrics = fundamental_data.get("metrics", {})
                valuation = metrics.get("valuation", {})
                profitability = metrics.get("profitability", {})
                financial_health = metrics.get("financial_health", {})
                growth = metrics.get("growth", {})

                # Calculate market cap with fallback (company_info first)
                market_cap = (
                    company_info.get("market_cap")
                    or valuation.get("market_cap")
                    or (
                        company_info.get("shares_outstanding") * price_context.get("latest_price")
                        if company_info.get("shares_outstanding")
                        and price_context.get("latest_price")
                        else None
                    )
                )

                # Extract metrics with fallback (company_info first, then nested metrics)
                pe_ratio = (
                    company_info.get("pe_ratio")
                    or company_info.get("trailing_pe")
                    or valuation.get("trailing_pe")
                )
                forward_pe = company_info.get("forward_pe") or valuation.get("forward_pe")
                peg_ratio = company_info.get("peg_ratio") or valuation.get("peg_ratio")
                price_to_book = company_info.get("price_to_book") or valuation.get("price_to_book")
                price_to_sales = company_info.get("price_to_sales") or valuation.get(
                    "price_to_sales"
                )
                ev_to_revenue = company_info.get("ev_to_revenue") or valuation.get(
                    "enterprise_to_revenue"
                )
                ev_to_ebitda = company_info.get("ev_to_ebitda") or valuation.get(
                    "enterprise_to_ebitda"
                )

                profit_margin = company_info.get("profit_margin") or profitability.get(
                    "profit_margin"
                )
                operating_margin = company_info.get("operating_margin") or profitability.get(
                    "operating_margin"
                )
                return_on_equity = company_info.get("return_on_equity") or profitability.get(
                    "return_on_equity"
                )
                return_on_assets = (
                    company_info.get("return_on_assets")
                    or profitability.get("return_on_assets")
                    or financial_health.get("return_on_assets")
                )

                quarterly_earnings_growth_yoy = company_info.get(
                    "quarterly_earnings_growth_yoy"
                ) or growth.get("earnings_quarterly_growth")
                quarterly_revenue_growth_yoy = company_info.get(
                    "quarterly_revenue_growth_yoy"
                ) or growth.get("revenue_growth")

                # Check if snapshot already exists (upsert pattern)
                existing = session.exec(
                    select(FundamentalSnapshot).where(
                        (FundamentalSnapshot.ticker_id == ticker_obj.id)
                        & (FundamentalSnapshot.snapshot_date == snapshot_date)
                    )
                ).first()

                if existing:
                    # Update existing snapshot
                    existing.data_json = json.dumps(data_to_store)
                    existing.market_cap = market_cap
                    existing.pe_ratio = pe_ratio
                    existing.forward_pe = forward_pe
                    existing.peg_ratio = peg_ratio
                    existing.price_to_book = price_to_book
                    existing.price_to_sales = price_to_sales
                    existing.ev_to_revenue = ev_to_revenue
                    existing.ev_to_ebitda = ev_to_ebitda
                    existing.profit_margin = profit_margin
                    existing.operating_margin = operating_margin
                    existing.return_on_equity = return_on_equity
                    existing.return_on_assets = return_on_assets
                    existing.quarterly_earnings_growth_yoy = quarterly_earnings_growth_yoy
                    existing.quarterly_revenue_growth_yoy = quarterly_revenue_growth_yoy
                    existing.analyst_target_price = analyst_data.get("analyst_target_price")
                    existing.total_analysts = analyst_data.get("total_analysts")
                    existing.strong_buy_count = analyst_data.get("strong_buy")
                    existing.buy_count = analyst_data.get("buy")
                    existing.hold_count = analyst_data.get("hold")
                    existing.latest_price = price_context.get("latest_price")
                    existing.price_change_percent = price_context.get("change_percent")
                    existing.price_trend = price_context.get("trend")
                    existing.data_sources = fundamental_data.get("data_sources")
                    existing.data_availability = fundamental_data.get("data_availability")
                    existing.fetched_at = datetime.now()
                    session.add(existing)
                    logger.debug(f"Updated fundamental snapshot for {ticker} on {snapshot_date}")
                else:
                    # Create new snapshot
                    snapshot = FundamentalSnapshot(
                        ticker_id=ticker_obj.id,
                        snapshot_date=snapshot_date,
                        data_json=json.dumps(data_to_store),
                        # Valuation metrics
                        market_cap=market_cap,
                        pe_ratio=pe_ratio,
                        forward_pe=forward_pe,
                        peg_ratio=peg_ratio,
                        price_to_book=price_to_book,
                        price_to_sales=price_to_sales,
                        ev_to_revenue=ev_to_revenue,
                        ev_to_ebitda=ev_to_ebitda,
                        # Profitability metrics
                        profit_margin=profit_margin,
                        operating_margin=operating_margin,
                        return_on_equity=return_on_equity,
                        return_on_assets=return_on_assets,
                        # Growth metrics
                        quarterly_earnings_growth_yoy=quarterly_earnings_growth_yoy,
                        quarterly_revenue_growth_yoy=quarterly_revenue_growth_yoy,
                        # Analyst data
                        analyst_target_price=analyst_data.get("analyst_target_price"),
                        total_analysts=analyst_data.get("total_analysts"),
                        strong_buy_count=analyst_data.get("strong_buy"),
                        buy_count=analyst_data.get("buy"),
                        hold_count=analyst_data.get("hold"),
                        # Price context
                        latest_price=price_context.get("latest_price"),
                        price_change_percent=price_context.get("change_percent"),
                        price_trend=price_context.get("trend"),
                        # Metadata
                        data_sources=fundamental_data.get("data_sources"),
                        data_availability=fundamental_data.get("data_availability"),
                    )
                    session.add(snapshot)
                    logger.debug(f"Created fundamental snapshot for {ticker} on {snapshot_date}")

                session.commit()
                return True

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Failed to store fundamental snapshot for {ticker}: {e}")
            return False

    def get_snapshot(self, ticker: str, as_of_date: date) -> dict | None:
        """Get complete fundamental snapshot for a specific date.

        Args:
            ticker: Stock ticker symbol.
            as_of_date: Date to retrieve snapshot for.

        Returns:
            Complete fundamental data dict or None if not found.
        """
        ticker = ticker.upper()

        try:
            session = self.db_manager.get_session()
            try:
                # Get ticker object first
                ticker_obj = session.exec(select(Ticker).where(Ticker.symbol == ticker)).first()

                if not ticker_obj:
                    return None

                # Get snapshot for the exact date
                snapshot = session.exec(
                    select(FundamentalSnapshot).where(
                        (FundamentalSnapshot.ticker_id == ticker_obj.id)
                        & (FundamentalSnapshot.snapshot_date == as_of_date)
                    )
                ).first()

                if snapshot:
                    return json.loads(snapshot.data_json)
                return None

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Failed to retrieve fundamental snapshot for {ticker}: {e}")
            return None

    def get_snapshot_range(self, ticker: str, start_date: date, end_date: date) -> list[dict]:
        """Get all fundamental snapshots in date range.

        Args:
            ticker: Stock ticker symbol.
            start_date: Start of date range.
            end_date: End of date range.

        Returns:
            List of dicts with 'snapshot_date' and 'data' keys.
        """
        ticker = ticker.upper()

        try:
            session = self.db_manager.get_session()
            try:
                # Get ticker object first
                ticker_obj = session.exec(select(Ticker).where(Ticker.symbol == ticker)).first()

                if not ticker_obj:
                    return []

                # Get all snapshots in range
                snapshots = session.exec(
                    select(FundamentalSnapshot)
                    .where(
                        (FundamentalSnapshot.ticker_id == ticker_obj.id)
                        & (FundamentalSnapshot.snapshot_date >= start_date)
                        & (FundamentalSnapshot.snapshot_date <= end_date)
                    )
                    .order_by(FundamentalSnapshot.snapshot_date)
                ).all()

                return [
                    {
                        "snapshot_date": snapshot.snapshot_date,
                        "data": json.loads(snapshot.data_json),
                    }
                    for snapshot in snapshots
                ]

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Failed to retrieve fundamental snapshots for {ticker}: {e}")
            return []

    def get_latest_snapshot(
        self, ticker: str, before_date: date | None = None
    ) -> tuple[date, dict] | None:
        """Get most recent snapshot, optionally before a specific date.

        Useful for backtesting - get the most recent data available
        at a historical point in time.

        Args:
            ticker: Stock ticker symbol.
            before_date: Optional date limit (get latest before this date).

        Returns:
            Tuple of (snapshot_date, fundamental_data) or None.
        """
        ticker = ticker.upper()

        try:
            session = self.db_manager.get_session()
            try:
                # Get ticker object first
                ticker_obj = session.exec(select(Ticker).where(Ticker.symbol == ticker)).first()

                if not ticker_obj:
                    return None

                # Build query
                query = select(FundamentalSnapshot).where(
                    FundamentalSnapshot.ticker_id == ticker_obj.id
                )

                # Add date filter if provided
                if before_date:
                    query = query.where(FundamentalSnapshot.snapshot_date <= before_date)

                # Order by date descending and get first
                query = query.order_by(FundamentalSnapshot.snapshot_date.desc()).limit(1)

                snapshot = session.exec(query).first()

                if snapshot:
                    return (snapshot.snapshot_date, json.loads(snapshot.data_json))
                return None

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Failed to retrieve latest fundamental snapshot for {ticker}: {e}")
            return None

    def get_snapshots_for_date(
        self, snapshot_date: date, ticker_symbols: list[str] | None = None
    ) -> list[dict]:
        """Get all fundamental snapshots for a specific date.

        Useful for batch processing and analysis of multiple tickers.

        Args:
            snapshot_date: Date to retrieve snapshots for.
            ticker_symbols: Optional list of ticker symbols to filter by.

        Returns:
            List of dicts with 'ticker', 'snapshot_date', and 'data' keys.
        """
        try:
            session = self.db_manager.get_session()
            try:
                # Build base query
                query = (
                    select(FundamentalSnapshot, Ticker)
                    .join(Ticker, FundamentalSnapshot.ticker_id == Ticker.id)
                    .where(FundamentalSnapshot.snapshot_date == snapshot_date)
                )

                # Add ticker filter if provided
                if ticker_symbols:
                    upper_symbols = [s.upper() for s in ticker_symbols]
                    query = query.where(Ticker.symbol.in_(upper_symbols))

                results = session.exec(query).all()

                return [
                    {
                        "ticker": ticker.symbol,
                        "snapshot_date": snapshot.snapshot_date,
                        "data": json.loads(snapshot.data_json),
                    }
                    for snapshot, ticker in results
                ]

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Failed to retrieve fundamental snapshots for date {snapshot_date}: {e}")
            return []

    def count_snapshots(self, ticker: str | None = None) -> int:
        """Count total number of snapshots, optionally filtered by ticker.

        Args:
            ticker: Optional ticker symbol to filter by.

        Returns:
            Number of snapshots.
        """
        try:
            session = self.db_manager.get_session()
            try:
                if ticker:
                    ticker = ticker.upper()
                    ticker_obj = session.exec(select(Ticker).where(Ticker.symbol == ticker)).first()

                    if not ticker_obj:
                        return 0

                    count = session.exec(
                        select(func.count(FundamentalSnapshot.id)).where(
                            FundamentalSnapshot.ticker_id == ticker_obj.id
                        )
                    ).one()
                else:
                    count = session.exec(select(func.count(FundamentalSnapshot.id))).one()

                return count

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Failed to count fundamental snapshots: {e}")
            return 0

    def delete_snapshot(self, ticker: str, snapshot_date: date) -> bool:
        """Delete a specific fundamental snapshot.

        Args:
            ticker: Stock ticker symbol.
            snapshot_date: Date of snapshot to delete.

        Returns:
            True if deleted, False otherwise.
        """
        ticker = ticker.upper()

        try:
            session = self.db_manager.get_session()
            try:
                # Get ticker object first
                ticker_obj = session.exec(select(Ticker).where(Ticker.symbol == ticker)).first()

                if not ticker_obj:
                    return False

                # Get and delete snapshot
                snapshot = session.exec(
                    select(FundamentalSnapshot).where(
                        (FundamentalSnapshot.ticker_id == ticker_obj.id)
                        & (FundamentalSnapshot.snapshot_date == snapshot_date)
                    )
                ).first()

                if snapshot:
                    session.delete(snapshot)
                    session.commit()
                    logger.info(f"Deleted fundamental snapshot for {ticker} on {snapshot_date}")
                    return True
                return False

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Failed to delete fundamental snapshot for {ticker}: {e}")
            return False
