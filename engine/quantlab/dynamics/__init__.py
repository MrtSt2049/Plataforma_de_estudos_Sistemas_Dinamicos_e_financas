"""Discrete dynamical systems: the logistic map, stability, periods and chaos."""

from quantlab.dynamics.logistic import (
    R_MAX,
    R_MIN,
    logistic_derivative,
    logistic_fixed_points,
    logistic_lyapunov_exponent,
    logistic_map,
    simulate_logistic_map,
)
from quantlab.dynamics.orbits import detect_period
from quantlab.dynamics.stability import (
    FixedPoint,
    FixedPointStability,
    classify_map_fixed_point,
)

__all__ = [
    "R_MAX",
    "R_MIN",
    "FixedPoint",
    "FixedPointStability",
    "classify_map_fixed_point",
    "detect_period",
    "logistic_derivative",
    "logistic_fixed_points",
    "logistic_lyapunov_exponent",
    "logistic_map",
    "simulate_logistic_map",
]
