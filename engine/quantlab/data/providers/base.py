"""Interface shared by every market-data provider.

A provider hides where data comes from (files, a web API, a database) and always
returns a :class:`quantlab.data.PriceHistory` in the canonical schema. Code that
analyses data depends only on this interface, so changing the source does not
change any analysis.

Error contract:

* :class:`quantlab.exceptions.SymbolNotFoundError` when the symbol does not exist;
* :class:`quantlab.exceptions.DataSourceError` when the source fails (I/O,
  malformed content, unavailable service);
* :class:`quantlab.exceptions.InputValidationError` for invalid requests
  (for example ``start`` after ``end``).
"""

from __future__ import annotations

import datetime as dt
from typing import Protocol, runtime_checkable

from quantlab.data.schema import PriceHistory
from quantlab.exceptions import InputValidationError


@runtime_checkable
class PriceProvider(Protocol):
    """A source of historical prices."""

    @property
    def source(self) -> str:
        """Name of the source, recorded in every returned history's metadata."""
        ...

    def available_symbols(self) -> tuple[str, ...]:
        """Return the symbols this provider can deliver, sorted."""
        ...

    def fetch(
        self, symbol: str, *, start: dt.date | None = None, end: dt.date | None = None
    ) -> PriceHistory:
        """Return the price history of ``symbol`` between ``start`` and ``end``, inclusive.

        ``None`` means unbounded on that side. The result may be empty if the
        source has no observation in the range.
        """
        ...


def validate_date_range(start: dt.date | None, end: dt.date | None) -> None:
    """Raise :class:`InputValidationError` if both bounds are given and ``start > end``."""
    for name, value in (("start", start), ("end", end)):
        if value is not None and not isinstance(value, dt.date):
            raise TypeError(f"{name} must be a datetime.date, got {type(value).__name__}.")
    if start is not None and end is not None and start > end:
        raise InputValidationError(f"start ({start}) must not be after end ({end}).")
