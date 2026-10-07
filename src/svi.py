"""Bounded raw-SVI smile fitting for the IV reconstruction benchmark.

The implementation fits total implied variance as a function of log-moneyness
using a deterministic, bounded nonlinear least-squares procedure. Test/holdout
values are never used by this module.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np
from scipy.optimize import least_squares


PARAMETER_NAMES = ("a", "b", "rho", "m", "sigma")


@dataclass(frozen=True)
class SVIFitResult:
    """Result of one SVI smile calibration."""

    success: bool
    parameters: tuple[float, float, float, float, float] | None
    n_points: int
    cost: float | None
    message: str


def raw_svi_total_variance(
    log_moneyness: np.ndarray,
    parameters: Sequence[float],
) -> np.ndarray:
    """Evaluate raw SVI total variance w(k)."""
    a, b, rho, m, sigma = np.asarray(parameters, dtype=float)
    k = np.asarray(log_moneyness, dtype=float)

    return a + b * (
        rho * (k - m)
        + np.sqrt((k - m) ** 2 + sigma**2)
    )


def _initial_guess(
    log_moneyness: np.ndarray,
    total_variance: np.ndarray,
    *,
    rho: float,
    sigma: float,
) -> np.ndarray:
    """Construct a deterministic SVI starting point."""
    k_span = max(float(np.ptp(log_moneyness)), 1e-4)
    w_span = max(float(np.ptp(total_variance)), 1e-8)

    a0 = max(float(np.min(total_variance)) * 0.5, 1e-8)
    b0 = np.clip(w_span / k_span, 1e-4, 10.0)
    m0 = float(np.median(log_moneyness))
    sigma0 = np.clip(float(sigma), 1e-4, 5.0)

    return np.array([a0, b0, rho, m0, sigma0], dtype=float)


def fit_svi(
    log_moneyness: np.ndarray | list[float],
    implied_volatility: np.ndarray | list[float],
    time_to_expiry_years: float,
    *,
    min_points: int = 5,
    max_nfev: int = 1000,
    initial_rhos: Sequence[float] = (-0.5, 0.0, 0.5),
    initial_sigmas: Sequence[float] = (0.05, 0.15),
) -> SVIFitResult:
    """Fit a bounded raw-SVI smile using observed IV points only.

    Parameter bounds are fixed and supplied by the benchmark protocol.
    Multiple deterministic initializations are used only to reduce optimizer
    dependence; they are not selected using validation/test performance.
    """
    k = np.asarray(log_moneyness, dtype=float).reshape(-1)
    iv = np.asarray(implied_volatility, dtype=float).reshape(-1)
    T = float(time_to_expiry_years)

    if k.size != iv.size:
        raise ValueError("log_moneyness and implied_volatility must have equal length.")

    valid = np.isfinite(k) & np.isfinite(iv) & (iv > 0)
    k = k[valid]
    iv = iv[valid]

    if T <= 0 or not np.isfinite(T):
        return SVIFitResult(False, None, int(k.size), None, "invalid_time_to_expiry")

    if k.size < min_points:
        return SVIFitResult(False, None, int(k.size), None, "insufficient_points")

    total_variance = iv**2 * T
    if not np.all(np.isfinite(total_variance)) or np.any(total_variance <= 0):
        return SVIFitResult(False, None, int(k.size), None, "invalid_total_variance")

    scale = max(float(np.median(total_variance)), 1e-4)

    def residuals(params: np.ndarray) -> np.ndarray:
        fitted = raw_svi_total_variance(k, params)
        return (fitted - total_variance) / scale

    # a >= 0, b > 0, |rho| < 1, sigma > 0 gives a non-negative SVI surface.
    lower = np.array([1e-10, 1e-8, -0.999, -5.0, 1e-4], dtype=float)
    upper = np.array([4.0, 10.0, 0.999, 5.0, 5.0], dtype=float)

    best_result = None
    best_cost = np.inf

    for rho0 in initial_rhos:
        for sigma0 in initial_sigmas:
            x0 = _initial_guess(
                k,
                total_variance,
                rho=float(rho0),
                sigma=float(sigma0),
            )

            try:
                result = least_squares(
                    residuals,
                    x0=x0,
                    bounds=(lower, upper),
                    method="trf",
                    max_nfev=max_nfev,
                )
            except Exception:
                continue

            if np.all(np.isfinite(result.x)) and np.isfinite(result.cost):
                if result.cost < best_cost:
                    best_result = result
                    best_cost = float(result.cost)

    if best_result is None:
        return SVIFitResult(False, None, int(k.size), None, "optimizer_failure")

    params = tuple(float(x) for x in best_result.x)

    if not np.all(np.isfinite(raw_svi_total_variance(k, params))):
        return SVIFitResult(False, None, int(k.size), float(best_cost), "invalid_fit")

    return SVIFitResult(
        success=bool(best_result.success),
        parameters=params,
        n_points=int(k.size),
        cost=float(best_result.cost),
        message=str(best_result.message),
    )


def predict_svi_iv(
    log_moneyness: np.ndarray | list[float],
    time_to_expiry_years: float,
    fit_result: SVIFitResult,
) -> np.ndarray:
    """Predict implied volatility from a successful SVI fit."""
    k = np.asarray(log_moneyness, dtype=float).reshape(-1)
    predictions = np.full(k.shape, np.nan, dtype=float)

    if not fit_result.success or fit_result.parameters is None:
        return predictions

    T = float(time_to_expiry_years)
    if T <= 0 or not np.isfinite(T):
        return predictions

    total_variance = raw_svi_total_variance(k, fit_result.parameters)
    valid = np.isfinite(total_variance) & (total_variance > 0)

    predictions[valid] = np.sqrt(total_variance[valid] / T)
    return predictions
