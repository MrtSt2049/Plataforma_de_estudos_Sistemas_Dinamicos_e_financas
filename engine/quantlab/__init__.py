"""QuantLab scientific engine.

A framework-independent library of algorithms for quantitative finance and
dynamical systems. It must not import Django, Supabase, HTTP clients or any
user-interface code (RULE 002), so it runs the same way in scripts, notebooks,
tests and inside the backend.

Subpackages
-----------
quantlab.analysis
    Returns and volatility of financial time series.
quantlab.dynamics
    Dynamical systems: the logistic map (fixed-point stability, periodic
    orbits, Lyapunov exponents) and the Lorenz system (adaptive integration,
    equilibria and their eigenvalues, the Hopf threshold).
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("quantlab")
except PackageNotFoundError:  # pragma: no cover - only when running from an uninstalled tree
    __version__ = "0.0.0+unknown"

__all__ = ["__version__"]
