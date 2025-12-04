"""Repository pattern for database operations.

Provides high-level repository interfaces for storing and retrieving historical
analyst ratings and other time-sensitive data from the SQLite database.
"""

from datetime import date, datetime
from pathlib import Path

from loguru import logger
from sqlmodel import select

from src.data.db import DatabaseManager
from src.data.models import (
    AnalystData,
    AnalystRating,
    PriceTracking,
    Recommendation,
    RunSession,
    Ticker,
)


class AnalystRatingsRepository:
    """Repository for storing and retrieving historical analyst ratings.

    Manages CRUD operations for analyst ratings in the SQLite database,
    with additional methods for querying historical data.
    """

    def __init__(self, db_path: Path | str = "data/nordinvest.db"):
        """Initialize repository with database manager.

        Args:
            db_path: Path to SQLite database file.
        """
        # Create instance-specific database manager (not global) for better test isolation
        self.db_manager = DatabaseManager(db_path)
        self.db_manager.initialize()

    def _get_or_create_ticker(self, session, ticker_symbol: str, name: str = "") -> Ticker:
        """Get existing ticker or create new one.

        Args:
            session: Database session.
            ticker_symbol: Ticker symbol (e.g., 'AAPL').
            name: Company name (optional, defaults to symbol).

        Returns:
            Ticker object.
        """
        ticker_symbol = ticker_symbol.upper()

        # Check if ticker already exists
        existing = session.exec(select(Ticker).where(Ticker.symbol == ticker_symbol)).first()

        if existing:
            return existing

        # Create new ticker
        new_ticker = Ticker(
            symbol=ticker_symbol,
            name=name or ticker_symbol,
            market="us",  # Default, can be overridden later
            instrument_type="stock",
        )
        session.add(new_ticker)
        session.flush()  # Flush to get the ID without committing
        return new_ticker

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
                ticker_obj = self._get_or_create_ticker(session, ticker, ratings.name)

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
                from sqlalchemy import func

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

    def __init__(self, db_path: Path | str = "data/nordinvest.db"):
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
    ) -> str:
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
            Session ID (UUID string).
        """
        import json
        import uuid

        try:
            session_id = str(uuid.uuid4())

            session = self.db_manager.get_session()
            try:
                run_session = RunSession(
                    id=session_id,
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

                logger.debug(f"Created run session: {session_id} ({analysis_mode})")
                return session_id

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error creating run session: {e}")
            raise

    def complete_session(
        self,
        session_id: str,
        signals_generated: int,
        signals_failed: int,
        status: str = "completed",
        error_message: str | None = None,
    ) -> None:
        """Mark session as completed.

        Args:
            session_id: Session ID (UUID).
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


class RecommendationsRepository:
    """Repository for storing and retrieving investment recommendations.

    Stores every investment signal immediately after creation, enabling partial report
    generation and historical analysis.
    """

    def __init__(self, db_path: Path | str = "data/nordinvest.db"):
        """Initialize repository with database manager.

        Args:
            db_path: Path to SQLite database file.
        """
        self.db_manager = DatabaseManager(db_path)
        self.db_manager.initialize()

    def _get_or_create_ticker(self, session, ticker_symbol: str, name: str = "") -> Ticker:
        """Get existing ticker or create new one.

        Args:
            session: Database session.
            ticker_symbol: Ticker symbol (e.g., 'AAPL').
            name: Company name (optional, defaults to symbol).

        Returns:
            Ticker object.
        """
        ticker_symbol = ticker_symbol.upper()

        # Check if ticker already exists
        existing = session.exec(select(Ticker).where(Ticker.symbol == ticker_symbol)).first()

        if existing:
            return existing

        # Create new ticker
        new_ticker = Ticker(
            symbol=ticker_symbol,
            name=name or ticker_symbol,
            market="us",  # Default, can be overridden later
            instrument_type="stock",
        )
        session.add(new_ticker)
        session.flush()  # Flush to get the ID without committing
        return new_ticker

    def store_recommendation(
        self,
        signal,  # InvestmentSignal type (imported dynamically to avoid circular import)
        run_session_id: str,
        analysis_mode: str,
        llm_model: str | None = None,
    ) -> str:
        """Store a single recommendation.

        Args:
            signal: InvestmentSignal Pydantic model.
            run_session_id: UUID linking to run session.
            analysis_mode: 'rule_based' or 'llm'.
            llm_model: LLM model name (if applicable).

        Returns:
            recommendation_id (UUID).
        """
        import json
        import uuid

        try:
            recommendation_id = str(uuid.uuid4())

            session = self.db_manager.get_session()
            try:
                # Get or create ticker
                ticker_obj = self._get_or_create_ticker(session, signal.ticker, signal.name)

                # Serialize complex fields to JSON
                risk_flags_json = json.dumps(signal.risk.flags) if signal.risk.flags else None
                key_reasons_json = json.dumps(signal.key_reasons) if signal.key_reasons else None
                caveats_json = json.dumps(signal.caveats) if signal.caveats else None

                # Create recommendation record
                recommendation = Recommendation(
                    id=recommendation_id,
                    ticker_id=ticker_obj.id,
                    run_session_id=run_session_id,
                    analysis_date=signal.analysis_date,
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
                )

                session.add(recommendation)
                session.commit()

                logger.debug(f"Stored recommendation {recommendation_id} for {signal.ticker}")
                return recommendation_id

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error storing recommendation for {signal.ticker}: {e}")
            raise

    def get_recommendations_by_session(self, run_session_id: str) -> list:
        """Get all recommendations for a specific run session.

        Args:
            run_session_id: UUID of the run session.

        Returns:
            List of Recommendation objects.
        """
        try:
            session = self.db_manager.get_session()
            try:
                recommendations = session.exec(
                    select(Recommendation)
                    .where(Recommendation.run_session_id == run_session_id)
                    .order_by(Recommendation.created_at)
                ).all()

                return list(recommendations)

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error retrieving recommendations for session {run_session_id}: {e}")
            return []

    def get_recommendations_by_date(self, analysis_date: date) -> list:
        """Get all recommendations for a specific analysis date.

        Args:
            analysis_date: Date when analysis was performed.

        Returns:
            List of Recommendation objects.
        """
        try:
            session = self.db_manager.get_session()
            try:
                recommendations = session.exec(
                    select(Recommendation)
                    .where(Recommendation.analysis_date == analysis_date)
                    .order_by(Recommendation.created_at)
                ).all()

                return list(recommendations)

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error retrieving recommendations for date {analysis_date}: {e}")
            return []

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


class PerformanceRepository:
    """Repository for tracking recommendation performance.

    Basic implementation for storing price tracking data and performance metrics.
    """

    def __init__(self, db_path: Path | str = "data/nordinvest.db"):
        """Initialize repository with database manager.

        Args:
            db_path: Path to SQLite database file.
        """
        self.db_manager = DatabaseManager(db_path)
        self.db_manager.initialize()

    def track_price(
        self,
        recommendation_id: str,
        tracking_date: date,
        price: float,
        days_since_recommendation: int,
        benchmark_price: float | None = None,
        benchmark_ticker: str = "SPY",
    ) -> bool:
        """Record price at specific date for performance tracking.

        Args:
            recommendation_id: UUID of the recommendation.
            tracking_date: Date when price was tracked.
            price: Stock price on tracking date.
            days_since_recommendation: Number of days since recommendation.
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

                # Calculate price change percentage
                price_change_pct = (
                    ((price - recommendation.current_price) / recommendation.current_price) * 100
                    if recommendation.current_price > 0
                    else None
                )

                # Calculate benchmark change percentage
                benchmark_change_pct = None
                alpha = None
                if benchmark_price and price_change_pct is not None:
                    # Note: Need to store initial benchmark price in recommendation for accurate calculation
                    # This is a simplified version
                    benchmark_change_pct = 0.0  # Placeholder
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
                    existing.benchmark_price = benchmark_price
                    existing.benchmark_change_pct = benchmark_change_pct
                    existing.alpha = alpha
                    session.add(existing)
                else:
                    # Create new
                    price_tracking = PriceTracking(
                        recommendation_id=recommendation_id,
                        tracking_date=tracking_date,
                        days_since_recommendation=days_since_recommendation,
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

    def get_performance_data(self, recommendation_id: str) -> list[PriceTracking]:
        """Get all price tracking data for a recommendation.

        Args:
            recommendation_id: UUID of the recommendation.

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
