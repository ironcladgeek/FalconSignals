"""Repository pattern for database operations.

Provides high-level repository interfaces for storing and retrieving historical
analyst ratings and other time-sensitive data from the SQLite database.
"""

from datetime import date, datetime
from pathlib import Path

from loguru import logger
from sqlmodel import and_, select

from src.data.db import DatabaseManager
from src.data.models import (
    AnalystData,
    AnalystRating,
    PerformanceSummary,
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
        import json

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
        import json
        from datetime import datetime

        try:
            session = self.db_manager.get_session()
            try:
                # Get or create ticker
                ticker_obj = self._get_or_create_ticker(session, signal.ticker, signal.name)

                # Convert analysis_date string to date object
                if isinstance(signal.analysis_date, str):
                    analysis_date = datetime.strptime(signal.analysis_date, "%Y-%m-%d").date()
                else:
                    analysis_date = signal.analysis_date

                # Serialize complex fields to JSON
                risk_flags_json = json.dumps(signal.risk.flags) if signal.risk.flags else None
                key_reasons_json = json.dumps(signal.key_reasons) if signal.key_reasons else None
                caveats_json = json.dumps(signal.caveats) if signal.caveats else None

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
        import json

        from src.analysis import InvestmentSignal
        from src.analysis.models import ComponentScores, RiskAssessment, RiskLevel
        from src.analysis.models import Recommendation as RecommendationType

        # Deserialize JSON fields
        risk_flags = json.loads(recommendation.risk_flags) if recommendation.risk_flags else []
        key_reasons = json.loads(recommendation.key_reasons) if recommendation.key_reasons else []
        caveats = json.loads(recommendation.caveats) if recommendation.caveats else []

        # Create ComponentScores
        scores = ComponentScores(
            technical=recommendation.technical_score or 50.0,
            fundamental=recommendation.fundamental_score or 50.0,
            sentiment=recommendation.sentiment_score or 50.0,
        )

        # Create RiskAssessment
        risk = RiskAssessment(
            level=RiskLevel(recommendation.risk_level)
            if recommendation.risk_level
            else RiskLevel.MEDIUM,
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
        )

    def get_recommendations_by_session(self, run_session_id: int) -> list:
        """Get all recommendations for a specific run session.

        Args:
            run_session_id: Integer ID of the run session.

        Returns:
            List of InvestmentSignal Pydantic models.
        """
        try:
            session = self.db_manager.get_session()
            try:
                recommendations = session.exec(
                    select(Recommendation)
                    .where(Recommendation.run_session_id == run_session_id)
                    .order_by(Recommendation.created_at)
                ).all()

                # Convert to InvestmentSignal objects
                return [self._to_investment_signal(rec) for rec in recommendations]

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error retrieving recommendations for session {run_session_id}: {e}")
            return []

    def get_recommendations_by_date(self, report_date: date | str) -> list:
        """Get all recommendations created on a specific date for report generation.

        Args:
            report_date: Date when report is being generated (date object or YYYY-MM-DD string).
                        Retrieves recommendations created on this date, regardless of analysis_date.

        Returns:
            List of InvestmentSignal Pydantic models.
        """
        from datetime import datetime

        try:
            # Convert string to date if needed
            if isinstance(report_date, str):
                report_date = datetime.strptime(report_date, "%Y-%m-%d").date()

            session = self.db_manager.get_session()
            try:
                # Filter by analysis_date
                recommendations = session.exec(
                    select(Recommendation)
                    .where(Recommendation.analysis_date == report_date)
                    .order_by(Recommendation.created_at)
                ).all()

                # Convert to InvestmentSignal objects
                return [self._to_investment_signal(rec) for rec in recommendations]

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error retrieving recommendations for date {report_date}: {e}")
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

    Provides methods for storing price tracking data, calculating performance metrics,
    and generating performance reports.
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
                from datetime import timedelta

                from sqlmodel import select

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
                from datetime import timedelta

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
                import statistics

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
