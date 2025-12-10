"""Content sanitization for public website publishing.

Removes sensitive information like portfolio allocations, watchlists,
and personal positions from reports before publishing.
"""

from copy import deepcopy

from src.analysis.models import DailyReport, InvestmentSignal
from src.utils.logging import get_logger

logger = get_logger(__name__)


def sanitize_report_for_web(report: DailyReport) -> DailyReport:
    """Remove private information from report before publishing.

    Removes:
    - Portfolio allocation suggestions
    - Watchlist additions/removals
    - Portfolio alerts
    - Suggested positions

    Args:
        report: Daily report with all data

    Returns:
        Sanitized report safe for public viewing
    """
    # Deep copy to avoid modifying original
    sanitized = deepcopy(report)

    # Remove portfolio allocation
    sanitized.allocation_suggestion = None

    # Remove watchlist
    sanitized.watchlist_additions = []
    sanitized.watchlist_removals = []

    # Remove portfolio alerts
    sanitized.portfolio_alerts = []

    logger.debug(f"Sanitized report for {report.report_date}")

    return sanitized


def sanitize_signal_for_web(signal: InvestmentSignal) -> InvestmentSignal:
    """Remove sensitive information from investment signal.

    Currently signals don't contain sensitive data, but this
    function is provided for future extensibility.

    Args:
        signal: Investment signal

    Returns:
        Sanitized signal safe for public viewing
    """
    # Signals don't currently contain portfolio-specific data
    # Return as-is, but keep function for future changes
    return deepcopy(signal)


def get_safe_signal_summary(signal: InvestmentSignal) -> dict:
    """Get safe summary dict for signal display.

    Returns only public-safe fields for web display.

    Args:
        signal: Investment signal

    Returns:
        Dictionary with safe fields
    """
    return {
        "ticker": signal.ticker,
        "recommendation": signal.recommendation.value,
        "confidence": signal.confidence,
        "current_price": signal.current_price,
        "analysis_date": signal.analysis_date,
        "component_scores": {
            "technical": signal.scores.technical if signal.scores else None,
            "fundamental": signal.scores.fundamental if signal.scores else None,
            "sentiment": signal.scores.sentiment if signal.scores else None,
        },
        "risk_level": signal.risk.level.value if signal.risk else None,
    }
