"""Market data: canonical schema, providers, standardization, integrity and cleaning.

Typical pipeline::

    history = provider.fetch("PETR4.SA", start=date(2024, 1, 1))
    report = check_ohlcv_integrity(history.data, max_abs_log_return=0.4)
    cleaned = clean_ohlcv(history.data, duplicates="last", missing="drop")
    returns = simple_returns(cleaned.data["close"])
"""

from quantlab.data.processing import (
    CleaningReport,
    CleaningResult,
    IntegrityIssue,
    IntegrityReport,
    IssueKind,
    check_ohlcv_integrity,
    clean_ohlcv,
    standardize_ohlcv,
)
from quantlab.data.providers import CsvPriceProvider, PriceProvider
from quantlab.data.schema import (
    CLOSE,
    HIGH,
    LOW,
    OHLCV_COLUMNS,
    OPEN,
    PRICE_COLUMNS,
    VOLUME,
    Frequency,
    PriceHistory,
    PriceMetadata,
)

__all__ = [
    "CLOSE",
    "HIGH",
    "LOW",
    "OHLCV_COLUMNS",
    "OPEN",
    "PRICE_COLUMNS",
    "VOLUME",
    "CleaningReport",
    "CleaningResult",
    "CsvPriceProvider",
    "Frequency",
    "IntegrityIssue",
    "IntegrityReport",
    "IssueKind",
    "PriceHistory",
    "PriceMetadata",
    "PriceProvider",
    "check_ohlcv_integrity",
    "clean_ohlcv",
    "standardize_ohlcv",
]
