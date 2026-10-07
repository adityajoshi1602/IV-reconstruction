"""Basic IV-surface consistency / arbitrage sanity checks.

These checks are deliberately basic. They do not claim global arbitrage freedom.
"""

from __future__ import annotations

import math
from typing import Iterable

import numpy as np
import pandas as pd
from scipy.stats import norm


def black_scholes_call(
    spot: float,
    strike: float,
    time_to_expiry: float,
    volatility: float,
    *,
    rate: float = 0.0,
) -> float:
    """Black-Scholes European call price with continuous compounding."""
    if any(
        not np.isfinite(x)
        for x in (spot, strike, time_to_expiry, volatility, rate)
    ):
        return float("nan")
    if spot <= 0 or strike <= 0 or time_to_expiry <= 0 or volatility <= 0:
        return float("nan")

    sigma_sqrt_t = volatility * math.sqrt(time_to_expiry)
    d1 = (
        math.log(spot / strike)
        + (rate + 0.5 * volatility * volatility) * time_to_expiry
    ) / sigma_sqrt_t
    d2 = d1 - sigma_sqrt_t

    return (
        spot * norm.cdf(d1)
        - strike * math.exp(-rate * time_to_expiry) * norm.cdf(d2)
    )


def call_price_rows(
    predictions: pd.DataFrame,
    *,
    rate: float = 0.0,
) -> pd.DataFrame:
    """Convert finite predicted IVs to Black-Scholes call prices."""
    required = {
        "datetime",
        "option_type",
        "strike",
        "iv",
        "prediction",
        "underlying_price",
        "time_to_expiry_years",
    }
    missing = required - set(predictions.columns)
    if missing:
        raise ValueError(f"Missing columns for consistency checks: {sorted(missing)}")

    df = predictions.copy()
    df = df[df["option_type"].eq("CE")].copy()
    df["call_price"] = [
        black_scholes_call(
            float(s),
            float(k),
            float(t),
            float(v),
            rate=rate,
        )
        for s, k, t, v in zip(
            df["underlying_price"],
            df["strike"],
            df["time_to_expiry_years"],
            df["prediction"],
        )
    ]
    return df


def consistency_summary(
    predictions: pd.DataFrame,
    *,
    rate: float = 0.0,
) -> pd.DataFrame:
    """Return per-model/condition monotonicity and convexity violation rates."""
    calls = call_price_rows(predictions, rate=rate)

    if calls.empty:
        return pd.DataFrame(
            columns=[
                "model",
                "missingness",
                "n_checks_monotonicity",
                "monotonicity_violations",
                "monotonicity_violation_rate",
                "n_checks_convexity",
                "convexity_violations",
                "convexity_violation_rate",
            ]
        )

    rows = []
    for (model, missingness, dt), group in calls.groupby(
        ["model", "missingness", "datetime"],
        sort=True,
        observed=True,
    ):
        group = group.sort_values("strike").dropna(subset=["call_price"])
        prices = group["call_price"].to_numpy(dtype=float)

        if len(prices) >= 2:
            first_diff = np.diff(prices)
            mono_viol = int(np.sum(first_diff > 1e-8))
            mono_checks = int(len(first_diff))
        else:
            mono_viol = 0
            mono_checks = 0

        if len(prices) >= 3:
            second_diff = prices[:-2] - 2.0 * prices[1:-1] + prices[2:]
            convex_viol = int(np.sum(second_diff < -1e-8))
            convex_checks = int(len(second_diff))
        else:
            convex_viol = 0
            convex_checks = 0

        rows.append(
            {
                "model": model,
                "missingness": missingness,
                "datetime": dt,
                "n_checks_monotonicity": mono_checks,
                "monotonicity_violations": mono_viol,
                "n_checks_convexity": convex_checks,
                "convexity_violations": convex_viol,
            }
        )

    df = pd.DataFrame(rows)
    grouped = (
        df.groupby(["model", "missingness"], as_index=False)
        .agg(
            n_checks_monotonicity=("n_checks_monotonicity", "sum"),
            monotonicity_violations=("monotonicity_violations", "sum"),
            n_checks_convexity=("n_checks_convexity", "sum"),
            convexity_violations=("convexity_violations", "sum"),
        )
    )
    grouped["monotonicity_violation_rate"] = (
        grouped["monotonicity_violations"]
        / grouped["n_checks_monotonicity"].replace(0, np.nan)
    )
    grouped["convexity_violation_rate"] = (
        grouped["convexity_violations"]
        / grouped["n_checks_convexity"].replace(0, np.nan)
    )
    return grouped
