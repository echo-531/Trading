"""
MRMC (买入卖出) Indicator — faithful line-by-line Python translation
of the MooMoo formula script.

Every variable name is preserved exactly as in the original.
No steps are merged, collapsed, or reordered.

Parameters (MooMoo defaults):
    S = 12  (fast EMA period)
    P = 26  (slow EMA period)
    M = 9   (signal EMA period)

Input: pandas DataFrame with columns: open, high, low, close, volume
Output: same DataFrame with added columns including buy_signal, sell_signal
        and ALL intermediate variables.
"""

import numpy as np
import pandas as pd
from engine import EMA, REF, BARSLAST, HHV, LLV, COUNT, _to_bool


def run_mrmc(df: pd.DataFrame, S: int = 12, P: int = 26, M: int = 9) -> pd.DataFrame:
    """
    Run the MRMC indicator on a price DataFrame.

    Returns a new DataFrame with all intermediate and final signal columns.
    """
    df = df.copy()
    CLOSE = df["close"].astype(float)

    # ── Core MACD ──────────────────────────────────────────────────────────────
    DIFF = EMA(CLOSE, S) - EMA(CLOSE, P)
    DEA  = EMA(DIFF, M)
    MACD = (DIFF - DEA) * 2

    # ── Cycle boundary detection ───────────────────────────────────────────────
    # N1: bars since last negative MACD cross (positive→negative)
    N1 = BARSLAST(_to_bool((REF(MACD, 1) >= 0) & (MACD < 0)))

    # MM1: bars since last positive MACD cross (negative→positive)
    MM1 = BARSLAST(_to_bool((REF(MACD, 1) <= 0) & (MACD > 0)))

    # ── Bullish divergence building blocks ────────────────────────────────────
    # Dynamic window versions — N1+1 and MM1+1 are per-bar Series
    N1p1  = N1  + 1   # per-bar series
    MM1p1 = MM1 + 1   # per-bar series

    CC1   = LLV(CLOSE, N1p1)
    CC2   = REF(CC1,   MM1p1)
    CC3   = REF(CC2,   MM1p1)

    DIFL1 = LLV(DIFF,  N1p1)
    DIFL2 = REF(DIFL1, MM1p1)
    DIFL3 = REF(DIFL2, MM1p1)

    # ── Bearish divergence building blocks ────────────────────────────────────
    CH1   = HHV(CLOSE, MM1p1)
    CH2   = REF(CH1,   N1p1)
    CH3   = REF(CH2,   N1p1)

    DIFH1 = HHV(DIFF,  MM1p1)
    DIFH2 = REF(DIFH1, N1p1)
    DIFH3 = REF(DIFH2, N1p1)

    # ── Bullish signal chain ───────────────────────────────────────────────────
    AAA = _to_bool(
        (CC1 < CC2) &
        (DIFL1 > DIFL2) &
        (REF(MACD, 1) < 0) &
        (DIFF < 0)
    )

    BBB = _to_bool(
        (CC1 < CC3) &
        (DIFL1 < DIFL2) &
        (DIFL1 > DIFL3) &
        (REF(MACD, 1) < 0) &
        (DIFF < 0)
    )

    CCC = _to_bool((AAA | BBB) & (DIFF < 0))

    LLL = _to_bool((REF(CCC.astype(int), 1) == 0) & CCC)

    XXX = _to_bool(
        (
            _to_bool(REF(AAA.astype(float), 1)) &
            (DIFL1 <= DIFL2) &
            (DIFF < DEA)
        ) | (
            _to_bool(REF(BBB.astype(float), 1)) &
            (DIFL1 <= DIFL3) &
            (DIFF < DEA)
        )
    )

    JJJ = _to_bool(
        _to_bool(REF(CCC.astype(float), 1)) &
        (REF(DIFF, 1).abs() >= (DIFF.abs() * 1.01))
    )

    BLBL = _to_bool(
        _to_bool(REF(JJJ.astype(float), 1)) &
        CCC &
        ((REF(DIFF, 1).abs() * 1.01) <= DIFF.abs())
    )

    # ✅ Final BUY signal
    DXDX = _to_bool((REF(JJJ.astype(int), 1) == 0) & JJJ)

    DJGXX = _to_bool(
        ((CLOSE < CC2) | (CLOSE < CC1)) &
        (
            _to_bool(REF(JJJ.astype(float), MM1p1)) |
            _to_bool(REF(JJJ.astype(float), MM1))
        ) &
        (~_to_bool(REF(LLL.astype(float), 1))) &
        (COUNT(JJJ.astype(int), 24) >= 1)
    )

    DJXX = _to_bool(
        (~_to_bool((COUNT(REF(DJGXX.astype(int), 1), 2) >= 1))) &
        DJGXX
    )

    DXX = _to_bool((XXX | DJXX) & ~CCC)

    # ── Bearish signal chain ───────────────────────────────────────────────────
    ZJDBL = _to_bool(
        (CH1 > CH2) &
        (DIFH1 < DIFH2) &
        (REF(MACD, 1) > 0) &
        (DIFF > 0)
    )

    GXDBL = _to_bool(
        (CH1 > CH3) &
        (DIFH1 > DIFH2) &
        (DIFH1 < DIFH3) &
        (REF(MACD, 1) > 0) &
        (DIFF > 0)
    )

    DBBL = _to_bool((ZJDBL | GXDBL) & (DIFF > 0))

    DBL = _to_bool(
        (REF(DBBL.astype(int), 1) == 0) &
        DBBL &
        (DIFF > DEA)
    )

    DBLXS = _to_bool(
        (
            _to_bool(REF(ZJDBL.astype(float), 1)) &
            (DIFH1 >= DIFH2) &
            (DIFF > DEA)
        ) | (
            _to_bool(REF(GXDBL.astype(float), 1)) &
            (DIFH1 >= DIFH3) &
            (DIFF > DEA)
        )
    )

    DBJG = _to_bool(
        _to_bool(REF(DBBL.astype(float), 1)) &
        (REF(DIFF, 1) >= (DIFF * 1.01))
    )

    # ✅ Final SELL signal
    DBJGXC = _to_bool(
        _to_bool(REF((~DBJG).astype(float), 1)) &
        DBJG
    )

    DBJGBL = _to_bool(
        _to_bool(REF(DBJG.astype(float), 1)) &
        DBBL &
        ((REF(DIFF, 1).abs() * 1.01) <= DIFF.abs())
    )

    ZZZZZ = _to_bool(
        ((CLOSE > CH2) | (CLOSE > CH1)) &
        (
            _to_bool(REF(DBJG.astype(float), N1p1)) |
            _to_bool(REF(DBJG.astype(float), N1))
        ) &
        (~_to_bool(REF(DBL.astype(float), 1))) &
        (COUNT(DBJG.astype(int), 23) >= 1)
    )

    YYYYY = _to_bool(
        (~_to_bool((COUNT(REF(ZZZZZ.astype(int), 1), 2) >= 1))) &
        ZZZZZ
    )

    WWWWW = _to_bool((DBLXS | YYYYY) & ~DBBL)

    # ── Attach all variables to output DataFrame ───────────────────────────────
    df["DIFF"]    = DIFF
    df["DEA"]     = DEA
    df["MACD"]    = MACD
    df["N1"]      = N1
    df["MM1"]     = MM1
    df["CC1"]     = CC1
    df["CC2"]     = CC2
    df["CC3"]     = CC3
    df["DIFL1"]   = DIFL1
    df["DIFL2"]   = DIFL2
    df["DIFL3"]   = DIFL3
    df["CH1"]     = CH1
    df["CH2"]     = CH2
    df["CH3"]     = CH3
    df["DIFH1"]   = DIFH1
    df["DIFH2"]   = DIFH2
    df["DIFH3"]   = DIFH3
    df["AAA"]     = AAA.astype(int)
    df["BBB"]     = BBB.astype(int)
    df["CCC"]     = CCC.astype(int)
    df["LLL"]     = LLL.astype(int)
    df["XXX"]     = XXX.astype(int)
    df["JJJ"]     = JJJ.astype(int)
    df["BLBL"]    = BLBL.astype(int)
    df["DXDX"]    = DXDX.astype(int)
    df["DJGXX"]   = DJGXX.astype(int)
    df["DJXX"]    = DJXX.astype(int)
    df["DXX"]     = DXX.astype(int)
    df["ZJDBL"]   = ZJDBL.astype(int)
    df["GXDBL"]   = GXDBL.astype(int)
    df["DBBL"]    = DBBL.astype(int)
    df["DBL"]     = DBL.astype(int)
    df["DBLXS"]   = DBLXS.astype(int)
    df["DBJG"]    = DBJG.astype(int)
    df["DBJGXC"]  = DBJGXC.astype(int)
    df["DBJGBL"]  = DBJGBL.astype(int)
    df["ZZZZZ"]   = ZZZZZ.astype(int)
    df["YYYYY"]   = YYYYY.astype(int)
    df["WWWWW"]   = WWWWW.astype(int)

    # Canonical output columns
    df["buy_signal"]  = DXDX.astype(int)
    df["sell_signal"] = DBJGXC.astype(int)

    return df
