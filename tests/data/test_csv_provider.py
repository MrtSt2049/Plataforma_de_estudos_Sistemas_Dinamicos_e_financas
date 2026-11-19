from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd
import pytest

from quantlab.analysis import simple_returns
from quantlab.data import CsvPriceProvider, Frequency, PriceProvider, clean_ohlcv
from quantlab.exceptions import DataSourceError, InputValidationError, SymbolNotFoundError

CSV = """date,open,high,low,close,volume
2025-01-02,10.0,10.3,9.8,10.1,1500
2025-01-03,10.1,10.6,9.9,10.5,1000
2025-01-06,10.4,10.9,10.2,10.8,1200
2025-01-07,10.8,11.0,10.5,10.6,900
"""


@pytest.fixture
def csv_dir(tmp_path: Path) -> Path:
    (tmp_path / "PETR4.SA.csv").write_text(CSV, encoding="utf-8")
    (tmp_path / "^BVSP.csv").write_text(CSV, encoding="utf-8")
    (tmp_path / "notes.txt").write_text("not data", encoding="utf-8")
    return tmp_path


@pytest.fixture
def provider(csv_dir: Path) -> CsvPriceProvider:
    return CsvPriceProvider(csv_dir, adjusted=True, currency="BRL")


def test_implements_the_provider_interface(provider: CsvPriceProvider) -> None:
    assert isinstance(provider, PriceProvider)
    assert provider.source == "local-csv"


def test_lists_csv_symbols_only(provider: CsvPriceProvider) -> None:
    assert provider.available_symbols() == ("PETR4.SA", "^BVSP")


def test_fetch_returns_canonical_data_with_metadata(provider: CsvPriceProvider) -> None:
    history = provider.fetch("PETR4.SA")
    assert list(history.data.columns) == ["open", "high", "low", "close", "volume"]
    assert len(history.data) == 4
    assert history.metadata.symbol == "PETR4.SA"
    assert history.metadata.adjusted is True
    assert history.metadata.currency == "BRL"
    assert history.metadata.frequency is Frequency.DAILY
    assert history.close.name == "PETR4.SA"
    assert history.close.tolist() == [10.1, 10.5, 10.8, 10.6]


def test_date_bounds_are_inclusive(provider: CsvPriceProvider) -> None:
    history = provider.fetch("PETR4.SA", start=dt.date(2025, 1, 3), end=dt.date(2025, 1, 6))
    assert [str(day.date()) for day in history.data.index] == ["2025-01-03", "2025-01-06"]


def test_range_without_data_gives_an_empty_history(provider: CsvPriceProvider) -> None:
    assert provider.fetch("PETR4.SA", start=dt.date(2030, 1, 1)).data.empty


def test_full_pipeline_to_returns(provider: CsvPriceProvider) -> None:
    history = provider.fetch("PETR4.SA")
    cleaned = clean_ohlcv(history.data, duplicates="last", missing="drop")
    returns = simple_returns(cleaned.data["close"])
    assert returns.iloc[0] == pytest.approx(10.5 / 10.1 - 1.0, rel=1e-14)


def test_brazilian_locale_files(tmp_path: Path) -> None:
    content = "Data;Fechamento\n02/01/2025;10,10\n03/01/2025;10,50\n"
    (tmp_path / "VALE3.csv").write_text(content, encoding="utf-8")
    provider = CsvPriceProvider(
        tmp_path,
        adjusted=False,
        date_column="Data",
        column_map={"Fechamento": "close"},
        separator=";",
        decimal=",",
    )
    history = provider.fetch("VALE3")
    assert history.close.tolist() == [10.1, 10.5]
    assert history.metadata.adjusted is False


def test_unknown_symbol(provider: CsvPriceProvider) -> None:
    with pytest.raises(SymbolNotFoundError, match="'VALE3'"):
        provider.fetch("VALE3")


@pytest.mark.parametrize("symbol", ["../secret", "a/b", "..", "", ".hidden", "PETR4 SA"])
def test_rejects_symbols_that_could_escape_the_directory(
    provider: CsvPriceProvider, symbol: str
) -> None:
    with pytest.raises(InputValidationError, match="invalid symbol"):
        provider.fetch(symbol)


def test_rejects_inverted_date_range(provider: CsvPriceProvider) -> None:
    with pytest.raises(InputValidationError, match="must not be after"):
        provider.fetch("PETR4.SA", start=dt.date(2025, 2, 1), end=dt.date(2025, 1, 1))


def test_rejects_non_date_bounds(provider: CsvPriceProvider) -> None:
    with pytest.raises(TypeError, match="start"):
        provider.fetch("PETR4.SA", start="2025-01-01")  # type: ignore[arg-type]


def test_missing_directory() -> None:
    with pytest.raises(DataSourceError, match="not found"):
        CsvPriceProvider(Path("this/does/not/exist"), adjusted=True)


def test_empty_and_malformed_files(tmp_path: Path) -> None:
    (tmp_path / "EMPTY.csv").write_text("", encoding="utf-8")
    (tmp_path / "BINARY.csv").write_bytes(b"\xff\xfe\x00\x81garbage")
    (tmp_path / "NOCLOSE.csv").write_text("date,price\n2025-01-02,1\n", encoding="utf-8")
    provider = CsvPriceProvider(tmp_path, adjusted=True)
    with pytest.raises(DataSourceError, match="empty"):
        provider.fetch("EMPTY")
    with pytest.raises(DataSourceError, match="could not read"):
        provider.fetch("BINARY")
    with pytest.raises(InputValidationError, match="close"):
        provider.fetch("NOCLOSE")


def test_price_history_rejects_non_canonical_data() -> None:
    from quantlab.data import PriceHistory, PriceMetadata

    metadata = PriceMetadata(symbol="X", source="test", frequency=Frequency.DAILY, adjusted=True)
    with pytest.raises(InputValidationError, match="'close' column"):
        PriceHistory(
            data=pd.DataFrame({"open": [1.0]}, index=pd.DatetimeIndex(["2025-01-02"])),
            metadata=metadata,
        )
