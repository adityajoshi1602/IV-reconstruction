"""Simple interpolation baselines for the IV reconstruction benchmark."""

from __future__ import annotations

import numpy as np
from scipy.interpolate import interp1d


def _clean_inputs(
    observed_strikes: np.ndarray | list[float],
    observed_ivs: np.ndarray | list[float],
) -> tuple[np.ndarray, np.ndarray]:
    """Return finite, sorted, one-dimensional strike/IV arrays."""
    x = np.asarray(observed_strikes, dtype=float).reshape(-1)
    y = np.asarray(observed_ivs, dtype=float).reshape(-1)

    if x.size != y.size:
        raise ValueError("observed_strikes and observed_ivs must have equal length.")

    valid = np.isfinite(x) & np.isfinite(y)
    x = x[valid]
    y = y[valid]

    if x.size == 0:
        return np.array([], dtype=float), np.array([], dtype=float)

    order = np.argsort(x)
    x = x[order]
    y = y[order]

    unique_x, inverse = np.unique(x, return_inverse=True)
    if unique_x.size != x.size:
        sums = np.bincount(inverse, weights=y)
        counts = np.bincount(inverse)
        y = sums / counts
        x = unique_x

    return x, y


def linear_strike_predict(
    observed_strikes: np.ndarray | list[float],
    observed_ivs: np.ndarray | list[float],
    target_strikes: np.ndarray | list[float],
    *,
    allow_extrapolation: bool = False,
) -> np.ndarray:
    """Predict IV at target strikes by 1D linear strike interpolation.

    By default the function refuses to extrapolate. Targets outside the
    observed strike bracket are returned as NaN so that edge failures can be
    measured explicitly rather than hidden.
    """
    x, y = _clean_inputs(observed_strikes, observed_ivs)
    targets = np.asarray(target_strikes, dtype=float).reshape(-1)

    predictions = np.full(targets.shape, np.nan, dtype=float)

    if x.size == 0:
        return predictions

    if x.size == 1:
        exact = np.isclose(targets, x[0])
        predictions[exact] = y[0]
        return predictions

    if allow_extrapolation:
        interpolator = interp1d(
            x,
            y,
            kind="linear",
            bounds_error=False,
            fill_value="extrapolate",
            assume_sorted=True,
        )
        return np.asarray(interpolator(targets), dtype=float)

    inside = (targets >= x[0]) & (targets <= x[-1])
    if inside.any():
        interpolator = interp1d(
            x,
            y,
            kind="linear",
            bounds_error=False,
            fill_value=np.nan,
            assume_sorted=True,
        )
        predictions[inside] = np.asarray(
            interpolator(targets[inside]),
            dtype=float,
        )

    return predictions


def nearest_strike_predict(
    observed_strikes: np.ndarray | list[float],
    observed_ivs: np.ndarray | list[float],
    target_strikes: np.ndarray | list[float],
) -> np.ndarray:
    """Predict IV at target strikes using the nearest observed strike."""
    x, y = _clean_inputs(observed_strikes, observed_ivs)
    targets = np.asarray(target_strikes, dtype=float).reshape(-1)

    predictions = np.full(targets.shape, np.nan, dtype=float)

    if x.size == 0:
        return predictions

    right = np.searchsorted(x, targets, side="left")
    right = np.clip(right, 0, x.size - 1)
    left = np.clip(right - 1, 0, x.size - 1)

    choose_right = np.abs(x[right] - targets) < np.abs(x[left] - targets)
    nearest_idx = np.where(choose_right, right, left)
    predictions = y[nearest_idx]

    return predictions
