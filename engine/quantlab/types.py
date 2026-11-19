"""Type aliases shared by the engine's public interfaces."""

import pandas as pd

type NumericSeries = pd.Series[float] | pd.Series[int]
"""A real-valued series accepted as input. Integer data is converted to float64."""

__all__ = ["NumericSeries"]
