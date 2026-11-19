from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from quantlab.data import IssueKind, check_ohlcv_integrity
from quantlab.exceptions import DataIntegrityError, DomainError, InputValidationError


def kinds(frame: pd.DataFrame, **kwargs: float) -> set[tuple[IssueKind, str | None]]:
    report = check_ohlcv_integrity(frame, **kwargs)
    return {(issue.kind, issue.column) for issue in report.issues}


def test_consistent_bars_are_valid(ohlcv: pd.DataFrame) -> None:
    report = check_ohlcv_integrity(ohlcv, max_abs_log_return=0.4)
    assert report.is_valid
    report.raise_if_invalid()  # does not raise


def test_reports_missing_and_infinite_values(ohlcv: pd.DataFrame) -> None:
    ohlcv.loc[ohlcv.index[1], "close"] = np.nan
    ohlcv.loc[ohlcv.index[2], "volume"] = np.inf
    found = kinds(ohlcv)
    assert (IssueKind.MISSING_VALUE, "close") in found
    assert (IssueKind.NON_FINITE_VALUE, "volume") in found


def test_reports_non_positive_prices_and_negative_volume(ohlcv: pd.DataFrame) -> None:
    ohlcv.loc[ohlcv.index[0], "low"] = 0.0
    ohlcv.loc[ohlcv.index[3], "volume"] = -5.0
    found = kinds(ohlcv)
    assert (IssueKind.NON_POSITIVE_PRICE, "low") in found
    assert (IssueKind.NEGATIVE_VOLUME, "volume") in found


def test_reports_inconsistent_bars(ohlcv: pd.DataFrame) -> None:
    ohlcv.loc[ohlcv.index[1], "high"] = 9.0  # below low, open and close
    ohlcv.loc[ohlcv.index[3], "low"] = 10.9  # above open (10.7) and close (10.8)
    found = kinds(ohlcv)
    assert (IssueKind.HIGH_BELOW_LOW, None) in found
    assert (IssueKind.HIGH_BELOW_OPEN_OR_CLOSE, "close") in found
    assert (IssueKind.HIGH_BELOW_OPEN_OR_CLOSE, "open") in found
    assert (IssueKind.LOW_ABOVE_OPEN_OR_CLOSE, "open") in found
    assert (IssueKind.LOW_ABOVE_OPEN_OR_CLOSE, "close") in found


def test_reports_duplicated_and_unsorted_dates(ohlcv: pd.DataFrame) -> None:
    shuffled = ohlcv.iloc[[0, 2, 1, 2, 3]]
    found = kinds(shuffled)
    assert (IssueKind.DUPLICATE_DATE, None) in found
    assert (IssueKind.UNSORTED_INDEX, None) in found


def test_extreme_move_check_flags_an_unadjusted_split(ohlcv: pd.DataFrame) -> None:
    ohlcv.loc[ohlcv.index[3:], ["open", "high", "low", "close"]] /= 2.0  # 2:1 split
    report = check_ohlcv_integrity(ohlcv, max_abs_log_return=0.4)
    (issue,) = [issue for issue in report.issues if issue.kind is IssueKind.EXTREME_RETURN]
    assert issue.dates == (ohlcv.index[3],)
    assert check_ohlcv_integrity(ohlcv).is_valid  # check disabled by default


def test_extreme_move_check_skips_missing_prices(ohlcv: pd.DataFrame) -> None:
    ohlcv.loc[ohlcv.index[2], "close"] = np.nan
    report = check_ohlcv_integrity(ohlcv, max_abs_log_return=0.4)
    assert IssueKind.EXTREME_RETURN not in {issue.kind for issue in report.issues}


def test_issue_lists_every_affected_date_and_describes_itself(ohlcv: pd.DataFrame) -> None:
    ohlcv["close"] = np.nan
    (issue,) = check_ohlcv_integrity(ohlcv[["close"]]).issues
    assert issue.count == 5
    assert issue.dates == tuple(ohlcv.index)
    assert issue.describe() == (
        "missing_value in 'close': 5 observation(s), e.g. 2025-03-03, 2025-03-04, 2025-03-05 "
        "(+2 more)"
    )


def test_raise_if_invalid_lists_the_problems(ohlcv: pd.DataFrame) -> None:
    ohlcv.loc[ohlcv.index[0], "volume"] = -1.0
    with pytest.raises(DataIntegrityError, match="negative_volume in 'volume'"):
        check_ohlcv_integrity(ohlcv).raise_if_invalid()


def test_rejects_non_canonical_structure(ohlcv: pd.DataFrame) -> None:
    with pytest.raises(InputValidationError, match="non-canonical"):
        check_ohlcv_integrity(ohlcv.rename(columns={"close": "Close"}))
    with pytest.raises(TypeError, match="DatetimeIndex"):
        check_ohlcv_integrity(ohlcv.reset_index(drop=True))
    with pytest.raises(InputValidationError, match="timezone-naive"):
        check_ohlcv_integrity(ohlcv.tz_localize("UTC"))
    with pytest.raises(InputValidationError, match="'close' column"):
        check_ohlcv_integrity(ohlcv.drop(columns="close"))


def test_rejects_non_positive_threshold(ohlcv: pd.DataFrame) -> None:
    with pytest.raises(DomainError, match="max_abs_log_return"):
        check_ohlcv_integrity(ohlcv, max_abs_log_return=0.0)


def test_rejects_non_frames_and_duplicated_columns(ohlcv: pd.DataFrame) -> None:
    with pytest.raises(TypeError, match="DataFrame"):
        check_ohlcv_integrity(ohlcv["close"])  # type: ignore[arg-type]
    duplicated = pd.concat([ohlcv["close"], ohlcv["close"]], axis=1)
    with pytest.raises(InputValidationError, match="duplicated columns"):
        check_ohlcv_integrity(duplicated)
