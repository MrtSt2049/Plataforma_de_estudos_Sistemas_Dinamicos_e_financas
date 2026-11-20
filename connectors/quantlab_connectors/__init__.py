"""Connectors to external services, kept outside the scientific engine.

The engine (``quantlab``) must not depend on HTTP APIs (RULE 002). A connector does
the opposite: it depends on the engine and implements one of its interfaces, such as
:class:`quantlab.data.PriceProvider`, so the engine never imports anything from here.

Each connector lives in its own module and is **not** imported by this package, so
that a connector's optional dependency is needed only when that connector is used:

* :mod:`quantlab_connectors.yahoo` (extra ``yahoo``): historical prices from Yahoo Finance.
"""
