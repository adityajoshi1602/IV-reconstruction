"""Shared data-loading and IV surface preparation utilities.

The benchmark uses this module as the single source of truth for parsing the
raw NIFTY option table into a canonical long-form observation table.
"""

from __future__ import annotations

from pathlib import Path
import re
from typing import Iterable

import numpy as np
import pandas as pd


SYMBOL_PATTERN = re.compile(
    r"^NIFTY(?P<expiry>\d{2}[A-Z]{3}\d{2})"
    r"(?P<strike>\d+(?:\.\d+)?)"
    r"(?P<option_type>CE|PE)$"
)

SECONDS_PER_YEAR = 365.25 * 24 * 60 * 60
EXPIRY_HOUR = 15
EXPIRY_MINUTE = 30


def repo_root() -> Path:
    """Return the repository root for code executed from any working directory."""
    return Path(__file__).resolve().parents[1]


def default_data_path() -> Path:
    """Return the canonical raw dataset path."""
    return repo_root() / "data" / "dataset.csv"


def get_option_columns(df: pd.DataFrame) -> list[str]:
    """Return option columns that match the repository's NIFTY symbol convention."""
    option_cols: list[str] = []
    for column in df.columns:
        if column.startswith("NIFTY") and SYMBOL_PATTERN.match(column):
            option_cols.append(column)
    return option_cols


def parse_option_symbol(symbol: str) -> dict[str, object]:
    """Parse a NIFTY option symbol into expiry, strike, and option type metadata."""
    match = SYMBOL_PATTERN.match(symbol)
    if match is None:
        raise ValueError(f"Unrecognised NIFTY option symbol: {symbol}")

    expiry = pd.to_datetime(match.group("expiry"), format="%d%b%y", exact=True)
    return {
        "symbol": symbol,
        "expiry": expiry,
        "strike": float(match.group("strike")),
        "option_type": match.group("option_type"),
    }


def load_raw_dataset(path: str | Path | None = None) -> pd.DataFrame:
    """Load the raw wide-format dataset without modifying it."""
    data_path = Path(path) if path is not None else default_data_path()
    if not data_path.exists():
        raise FileNotFoundError(f"Dataset not found: {data_path}")

    df = pd.read_csv(data_path)

    required = {"datetime", "underlying_price"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Dataset is missing required columns: {sorted(missing)}")

    df["datetime"] = pd.to_datetime(
        df["datetime"],
        format="%d-%m-%Y %H:%M",
        errors="raise",
    )
    df["underlying_price"] = pd.to_numeric(
        df["underlying_price"],
        errors="raise",
    )
    return df


def build_option_metadata(option_columns: Iterable[str]) -> pd.DataFrame:
    """Build one metadata row per option column."""
    metadata = pd.DataFrame(
        [parse_option_symbol(symbol) for symbol in option_columns]
    )
    return metadata.sort_values(
        ["expiry", "option_type", "strike"]
    ).reset_index(drop=True)


def to_long_form(df: pd.DataFrame) -> pd.DataFrame:
    """Convert the raw wide table into one row per timestamp/option observation."""
    option_columns = get_option_columns(df)
    if not option_columns:
        raise ValueError("No NIFTY option columns were found.")

    long_df = df.melt(
        id_vars=["datetime", "underlying_price"],
        value_vars=option_columns,
        var_name="symbol",
        value_name="iv",
    )

    metadata = build_option_metadata(option_columns)
    long_df = long_df.merge(metadata, on="symbol", how="left", validate="many_to_one")

    long_df["iv"] = pd.to_numeric(long_df["iv"], errors="coerce")
    long_df["expiry_datetime"] = (
        long_df["expiry"]
        + pd.Timedelta(hours=EXPIRY_HOUR, minutes=EXPIRY_MINUTE)
    )

    long_df["time_to_expiry_years"] = (
        (long_df["expiry_datetime"] - long_df["datetime"]).dt.total_seconds()
        / SECONDS_PER_YEAR
    )
    long_df["time_to_expiry_years"] = long_df["time_to_expiry_years"].clip(lower=0.0)

    long_df["moneyness"] = long_df["strike"] / long_df["underlying_price"]
    long_df["log_moneyness"] = np.log(long_df["moneyness"])

    long_df["total_variance"] = np.where(
        long_df["iv"].notna() & (long_df["time_to_expiry_years"] > 0),
        long_df["iv"] ** 2 * long_df["time_to_expiry_years"],
        np.nan,
    )

    long_df["observation_id"] = (
        long_df["datetime"].dt.strftime("%Y-%m-%dT%H:%M:%S")
        + "||"
        + long_df["symbol"]
    )

    return long_df.sort_values(
        ["datetime", "expiry", "option_type", "strike"]
    ).reset_index(drop=True)


def prepare_dataset(path: str | Path | None = None) -> pd.DataFrame:
    """Load, validate, and return the canonical long-form benchmark dataset."""
    wide_df = load_raw_dataset(path)
    validate_raw_dataset(wide_df)
    long_df = to_long_form(wide_df)
    validate_long_dataset(long_df)
    return long_df


def validate_raw_dataset(df: pd.DataFrame) -> None:
    """Run structural checks on the raw wide-format dataset."""
    if df["datetime"].duplicated().any():
        duplicated = df.loc[df["datetime"].duplicated(), "datetime"].head().tolist()
        raise ValueError(f"Duplicate timestamps found: {duplicated}")

    if (df["underlying_price"] <= 0).any():
        raise ValueError("Underlying prices must be strictly positive.")

    option_columns = get_option_columns(df)
    if not option_columns:
        raise ValueError("No valid option columns found.")

    observed_iv = df[option_columns].stack().dropna()
    if (observed_iv <= 0).any():
        raise ValueError("Observed IV values must be strictly positive.")


def validate_long_dataset(df: pd.DataFrame) -> None:
    """Run structural checks on the canonical long-form dataset."""
    if df["observation_id"].duplicated().any():
        raise ValueError("Observation IDs must be unique.")

    if (df["strike"] <= 0).any():
        raise ValueError("Strike prices must be strictly positive.")

    if (df["underlying_price"] <= 0).any():
        raise ValueError("Underlying prices must be strictly positive.")

    observed = df["iv"].notna()
    if (df.loc[observed, "iv"] <= 0).any():
        raise ValueError("Observed IV values must be strictly positive.")

    if df["expiry"].isna().any():
        raise ValueError("Every option symbol must have a valid expiry.")
