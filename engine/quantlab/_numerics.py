"""Private numerical helpers shared by several algorithms."""

from __future__ import annotations

import numpy as np
import numpy.typing as npt

_DISPERSION_SAFETY_FACTOR = 4.0


def dispersion_is_negligible(values: npt.ArrayLike, std: float) -> bool:
    """Return whether ``std`` is indistinguishable from zero given rounding error.

    The floating-point mean of ``n`` values bounded by ``M`` in magnitude carries an
    error of at most about ``n * eps * M``. A standard deviation below a few times
    that bound may be pure rounding: twenty copies of 0.004, for example, give a
    computed standard deviation near 1e-18 instead of 0. Dividing by such a value
    would produce a meaningless number of order 1e15.

    Parameters
    ----------
    values
        The data whose standard deviation was computed.
    std
        The computed standard deviation.

    Returns
    -------
    bool
        ``True`` if ``std <= 4 * n * eps * max(|values|)``.
    """
    data = np.asarray(values, dtype=np.float64)
    scale = float(np.max(np.abs(data))) if data.size else 0.0
    threshold = _DISPERSION_SAFETY_FACTOR * data.size * float(np.finfo(np.float64).eps) * scale
    return std <= threshold
