"""Fetch and align macroeconomic drivers for G10 FX crosses.

This module demonstrates:
- Working with pandas DataFrames for time-series manipulation
- Using NumPy for numeric transforms
- Running linear regressions with statsmodels
- Pulling data programmatically from Yahoo Finance and FRED

When executed as a script it will:
1. Download 5+ years of monthly FX and macro data
2. Merge the series into a single DataFrame aligned on month-end dates
3. Save the dataset to ``data/g10_fx_macro_dataset.csv``
4. Produce a EURUSD vs. US-Germany 2Y yield spread plot under ``plots/``
5. Run a sample linear regression of EURUSD returns on the yield spread and VIX
"""

from __future__ import annotations

import io
import os
import textwrap
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict

import numpy as np
import pandas as pd
import requests
import statsmodels.api as sm

FRED_CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"
YAHOO_DOWNLOAD_URL = "https://query1.finance.yahoo.com/v7/finance/download/{symbol}"
DEFAULT_START = datetime.now(timezone.utc) - timedelta(days=365 * 8)
DEFAULT_END = datetime.now(timezone.utc)


@dataclass
class SeriesMeta:
    """Metadata for each series in the combined dataset."""

    name: str
    description: str
    source: str


FX_SYMBOLS: Dict[str, SeriesMeta] = {
    "EURUSD=X": SeriesMeta("eurusd", "EUR/USD spot exchange rate (USD per EUR)", "Yahoo Finance"),
    "GBPUSD=X": SeriesMeta("gbpusd", "GBP/USD spot exchange rate (USD per GBP)", "Yahoo Finance"),
    "AUDUSD=X": SeriesMeta("audusd", "AUD/USD spot exchange rate (USD per AUD)", "Yahoo Finance"),
    "NZDUSD=X": SeriesMeta("nzdusd", "NZD/USD spot exchange rate (USD per NZD)", "Yahoo Finance"),
    "USDJPY=X": SeriesMeta("usdjpy", "USD/JPY spot exchange rate (JPY per USD)", "Yahoo Finance"),
    "USDCHF=X": SeriesMeta("usdchf", "USD/CHF spot exchange rate (CHF per USD)", "Yahoo Finance"),
    "USDCAD=X": SeriesMeta("usdcad", "USD/CAD spot exchange rate (CAD per USD)", "Yahoo Finance"),
    "USDSEK=X": SeriesMeta("usdsek", "USD/SEK spot exchange rate (SEK per USD)", "Yahoo Finance"),
    "USDNOK=X": SeriesMeta("usdnok", "USD/NOK spot exchange rate (NOK per USD)", "Yahoo Finance"),
}

FRED_SERIES: Dict[str, SeriesMeta] = {
    "DGS2": SeriesMeta("us_2y_yield", "US 2-year Treasury yield (percent)", "FRED"),
    "IRLTLT02EZM156N": SeriesMeta("ea_2y_yield", "Euro area 2-year government bond yield (percent)", "FRED"),
    "IRLTLT02JPM156N": SeriesMeta("jp_2y_yield", "Japan 2-year government bond yield (percent)", "FRED"),
    "IRLTLT02GBM156N": SeriesMeta("uk_2y_yield", "United Kingdom 2-year government bond yield (percent)", "FRED"),
    "IRLTLT02AUM156N": SeriesMeta("au_2y_yield", "Australia 2-year government bond yield (percent)", "FRED"),
    "IRLTLT02NZM156N": SeriesMeta("nz_2y_yield", "New Zealand 2-year government bond yield (percent)", "FRED"),
    "IRLTLT02CAM156N": SeriesMeta("ca_2y_yield", "Canada 2-year government bond yield (percent)", "FRED"),
    "IRLTLT02CHM156N": SeriesMeta("ch_2y_yield", "Switzerland 2-year government bond yield (percent)", "FRED"),
    "IRLTLT02SEM156N": SeriesMeta("se_2y_yield", "Sweden 2-year government bond yield (percent)", "FRED"),
    "IRLTLT02NOM156N": SeriesMeta("no_2y_yield", "Norway 2-year government bond yield (percent)", "FRED"),
    "DTWEXBGS": SeriesMeta("dxy", "Trade-weighted US dollar index (broad)", "FRED"),
    "DCOILWTICO": SeriesMeta("wti_crude", "WTI crude oil spot price (USD/barrel)", "FRED"),
    "GOLDAMGBD228NLBM": SeriesMeta("london_gold_fix", "London gold fixing price, USD per troy ounce", "FRED"),
    "VIXCLS": SeriesMeta("vix", "CBOE Volatility Index (VIX)", "FRED"),
}

YIELD_DIFFERENTIALS = {
    "eurusd": ("us_2y_yield", "ea_2y_yield"),
    "usdjpy": ("us_2y_yield", "jp_2y_yield"),
    "gbpusd": ("us_2y_yield", "uk_2y_yield"),
    "audusd": ("us_2y_yield", "au_2y_yield"),
    "nzdusd": ("us_2y_yield", "nz_2y_yield"),
    "usdcad": ("us_2y_yield", "ca_2y_yield"),
    "usdchf": ("us_2y_yield", "ch_2y_yield"),
    "usdsek": ("us_2y_yield", "se_2y_yield"),
    "usdnok": ("us_2y_yield", "no_2y_yield"),
}

def ensure_directory(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def fetch_yahoo_history(symbol: str, start: datetime, end: datetime, interval: str = "1mo") -> pd.Series:
    """Download price history from Yahoo Finance using the official CSV endpoint."""

    params = {
        "period1": int(start.timestamp()),
        "period2": int(end.timestamp()),
        "interval": interval,
        "events": "history",
        "includeAdjustedClose": "true",
    }
    response = requests.get(YAHOO_DOWNLOAD_URL.format(symbol=symbol), params=params, timeout=30)
    response.raise_for_status()

    df = pd.read_csv(io.StringIO(response.text), parse_dates=["Date"], index_col="Date")
    df = df.sort_index()
    # Use adjusted close to remove roll effects
    series = df["Adj Close"].rename(FX_SYMBOLS[symbol].name)
    return series


def fetch_fred_series(series_id: str) -> pd.Series:
    """Download a FRED series via the CSV export endpoint."""

    params = {"id": series_id}
    response = requests.get(FRED_CSV_URL, params=params, timeout=30)
    response.raise_for_status()
    df = pd.read_csv(io.StringIO(response.text), parse_dates=["DATE"], index_col="DATE")
    df.index.name = "Date"
    series = df.iloc[:, 0].rename(FRED_SERIES[series_id].name)
    series = series.replace({"." : np.nan}).astype(float)
    return series


def to_monthly(series: pd.Series, method: str = "last") -> pd.Series:
    """Convert a higher-frequency series to monthly frequency."""

    if not isinstance(series.index, pd.DatetimeIndex):
        raise TypeError("Series index must be a DatetimeIndex")

    if method == "last":
        return series.resample("M").last()
    if method == "mean":
        return series.resample("M").mean()
    raise ValueError(f"Unknown aggregation method: {method}")


def build_dataset(start: datetime = DEFAULT_START, end: datetime = DEFAULT_END) -> pd.DataFrame:
    """Fetch and merge the FX and macroeconomic series."""

    fx_frames = []
    for symbol in FX_SYMBOLS:
        fx_series = fetch_yahoo_history(symbol, start, end, interval="1mo")
        fx_frames.append(fx_series)

    fx_df = pd.concat(fx_frames, axis=1)

    fred_frames = []
    for series_id in FRED_SERIES:
        fred_series = fetch_fred_series(series_id)
        agg_method = "last" if "yield" not in FRED_SERIES[series_id].name and series_id not in {"DCOILWTICO", "GOLDAMGBD228NLBM", "VIXCLS"} else "mean"
        fred_frames.append(to_monthly(fred_series, method=agg_method))

    fred_df = pd.concat(fred_frames, axis=1)

    combined = pd.concat([fx_df, fred_df], axis=1)
    combined = combined.loc[(combined.index >= start) & (combined.index <= end)]

    # Forward fill to handle missing observations (e.g., holidays)
    combined = combined.sort_index().ffill()

    # Compute log returns for FX rates
    fx_return_cols = {}
    for column in fx_df.columns:
        fx_return_cols[f"{column}_log_return"] = np.log(fx_df[column]).diff()
    fx_returns = pd.concat(fx_return_cols.values(), axis=1)
    fx_returns.columns = fx_return_cols.keys()

    dataset = pd.concat([combined, fx_returns], axis=1)

    # Add interest rate differentials
    for pair, (base, quote) in YIELD_DIFFERENTIALS.items():
        dataset[f"{pair}_2y_differential"] = dataset[base] - dataset[quote]

    return dataset.dropna(how="all")


def run_sample_regression(dataset: pd.DataFrame) -> sm.regression.linear_model.RegressionResultsWrapper:
    """Run an illustrative regression: EURUSD returns vs. yield spread and VIX."""

    sample = dataset[["eurusd_log_return", "eurusd_2y_differential", "vix"]].dropna()
    sample["vix_change"] = sample["vix"].pct_change()
    sample = sample.dropna()

    y = sample["eurusd_log_return"]
    X = sm.add_constant(sample[["eurusd_2y_differential", "vix_change"]])
    model = sm.OLS(y, X, missing="drop")
    results = model.fit()
    return results


def create_plot(dataset: pd.DataFrame, output_path: str) -> None:
    import matplotlib.pyplot as plt

    ensure_directory(os.path.dirname(output_path))
    fig, ax1 = plt.subplots(figsize=(10, 6))

    ax1.set_title("EURUSD vs. US-Euro Area 2Y Yield Spread")
    ax1.plot(dataset.index, dataset["eurusd"], color="tab:blue", label="EURUSD")
    ax1.set_ylabel("EURUSD level (USD per EUR)", color="tab:blue")
    ax1.tick_params(axis="y", labelcolor="tab:blue")

    ax2 = ax1.twinx()
    ax2.plot(dataset.index, dataset["eurusd_2y_differential"], color="tab:orange", label="US - EA 2Y spread")
    ax2.set_ylabel("Yield spread (pp)", color="tab:orange")
    ax2.tick_params(axis="y", labelcolor="tab:orange")

    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)


def export_summary(results: sm.regression.linear_model.RegressionResultsWrapper) -> str:
    summary_text = results.summary().as_text()
    return textwrap.dedent(summary_text)


def main() -> None:
    ensure_directory("data")
    ensure_directory("plots")

    dataset = build_dataset()
    dataset.to_csv("data/g10_fx_macro_dataset.csv", index=True, float_format="%.6f")

    create_plot(dataset, "plots/eurusd_vs_yield_spread.png")

    regression_results = run_sample_regression(dataset)
    summary = export_summary(regression_results)
    with open("data/eurusd_regression_summary.txt", "w", encoding="utf-8") as fh:
        fh.write(summary)

    print("Dataset saved to data/g10_fx_macro_dataset.csv")
    print("Regression summary saved to data/eurusd_regression_summary.txt")
    print("Plot saved to plots/eurusd_vs_yield_spread.png")


if __name__ == "__main__":
    main()
