"""
MooMoo / TongDaXin Formula Engine
Bar-by-bar faithful implementation of all required primitives.
Supports dynamic (per-bar variable) window sizes.
"""

import numpy as np
import pandas as pd


def EMA(series: pd.Series, n: int) -> pd.Series:
    """
    Exponential Moving Average — MooMoo uses Wilder-style seed:
    first value = simple mean of first n bars, then EMA from there.
    alpha = 2 / (n + 1)
    """
    arr = series.values.astype(float)
    result = np.full(len(arr), np.nan)
    alpha = 2.0 / (n + 1)

    # find first valid index
    first_valid = 0
    while first_valid < len(arr) and np.isnan(arr[first_valid]):
        first_valid += 1

    if first_valid + n - 1 >= len(arr):
        return pd.Series(result, index=series.index)

    # seed: SMA of first n valid bars
    seed_end = first_valid + n - 1
    result[seed_end] = np.nanmean(arr[first_valid: seed_end + 1])

    # EMA forward
    for i in range(seed_end + 1, len(arr)):
        if np.isnan(arr[i]):
            result[i] = np.nan
        else:
            result[i] = alpha * arr[i] + (1 - alpha) * result[i - 1]

    return pd.Series(result, index=series.index)


def REF(series: pd.Series, n) -> pd.Series:
    """
    REF(X, n): value of X n bars ago.
    n may be a scalar int or a pd.Series of per-bar integers.
    """
    arr = series.values.astype(float)
    result = np.full(len(arr), np.nan)

    if np.isscalar(n):
        n_int = int(n)
        for i in range(len(arr)):
            j = i - n_int
            if j >= 0:
                result[i] = arr[j]
    else:
        n_arr = np.array(n, dtype=float)
        for i in range(len(arr)):
            ni = n_arr[i]
            if np.isnan(ni):
                continue
            j = i - int(ni)
            if j >= 0:
                result[i] = arr[j]

    return pd.Series(result, index=series.index)


def BARSLAST(condition: pd.Series) -> pd.Series:
    """
    BARSLAST(cond): bars since last True.
    Returns NaN if condition has never been True up to that bar.
    """
    cond_arr = condition.values.astype(float)
    result = np.full(len(cond_arr), np.nan)
    last_true = -1

    for i in range(len(cond_arr)):
        if cond_arr[i] == 1.0:
            last_true = i
        if last_true >= 0:
            result[i] = i - last_true

    return pd.Series(result, index=condition.index)


def HHV(series: pd.Series, n) -> pd.Series:
    """
    HHV(X, n): highest value over last n bars (including current bar).
    n may be scalar or pd.Series.
    """
    arr = series.values.astype(float)
    result = np.full(len(arr), np.nan)

    if np.isscalar(n):
        n_int = int(n)
        for i in range(len(arr)):
            start = max(0, i - n_int + 1)
            window = arr[start: i + 1]
            valid = window[~np.isnan(window)]
            if len(valid) > 0:
                result[i] = np.max(valid)
    else:
        n_arr = np.array(n, dtype=float)
        for i in range(len(arr)):
            ni = n_arr[i]
            if np.isnan(ni) or ni < 1:
                continue
            start = max(0, i - int(ni) + 1)
            window = arr[start: i + 1]
            valid = window[~np.isnan(window)]
            if len(valid) > 0:
                result[i] = np.max(valid)

    return pd.Series(result, index=series.index)


def LLV(series: pd.Series, n) -> pd.Series:
    """
    LLV(X, n): lowest value over last n bars (including current bar).
    n may be scalar or pd.Series.
    """
    arr = series.values.astype(float)
    result = np.full(len(arr), np.nan)

    if np.isscalar(n):
        n_int = int(n)
        for i in range(len(arr)):
            start = max(0, i - n_int + 1)
            window = arr[start: i + 1]
            valid = window[~np.isnan(window)]
            if len(valid) > 0:
                result[i] = np.min(valid)
    else:
        n_arr = np.array(n, dtype=float)
        for i in range(len(arr)):
            ni = n_arr[i]
            if np.isnan(ni) or ni < 1:
                continue
            start = max(0, i - int(ni) + 1)
            window = arr[start: i + 1]
            valid = window[~np.isnan(window)]
            if len(valid) > 0:
                result[i] = np.min(valid)

    return pd.Series(result, index=series.index)


def COUNT(condition: pd.Series, n) -> pd.Series:
    """
    COUNT(cond, n): number of True occurrences in last n bars (including current).
    n may be scalar or pd.Series.
    """
    cond_arr = condition.values.astype(float)
    result = np.full(len(cond_arr), np.nan)

    if np.isscalar(n):
        n_int = int(n)
        for i in range(len(cond_arr)):
            start = max(0, i - n_int + 1)
            result[i] = float(np.nansum(cond_arr[start: i + 1]))
    else:
        n_arr = np.array(n, dtype=float)
        for i in range(len(cond_arr)):
            ni = n_arr[i]
            if np.isnan(ni) or ni < 1:
                continue
            start = max(0, i - int(ni) + 1)
            result[i] = float(np.nansum(cond_arr[start: i + 1]))

    return pd.Series(result, index=condition.index)


def _to_bool(series: pd.Series) -> pd.Series:
    """Convert numeric series to boolean, treating NaN as False."""
    return series.fillna(0).astype(bool)
