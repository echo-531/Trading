"""
Universe builder.

US  — S&P 1500 (S&P 500 + S&P 400 MidCap + S&P 600 SmallCap),
      scraped live from Wikipedia with proper browser headers.

China — Comprehensive static lists for Shanghai (.SS), Shenzhen (.SZ),
        and Hong Kong (.HK). akshare is blocked outside China, so we
        maintain well-populated static lists and attempt a live akshare
        refresh only if it succeeds (e.g. when run via VPN).
"""

import json
import time
import requests
import pandas as pd


HTTP_TIMEOUT = 30
BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


# ══════════════════════════════════════════════════════════════════════════════
# US — S&P 1500 via Wikipedia (500 + 400 MidCap + 600 SmallCap)
# ══════════════════════════════════════════════════════════════════════════════

def _scrape_wikipedia_table(url: str, table_id: str, symbol_cols: list[str]) -> list[str]:
    """
    Generic Wikipedia table scraper with browser headers.
    symbol_cols: list of candidate column names to try in order.
    """
    try:
        resp = requests.get(url, headers=BROWSER_HEADERS, timeout=HTTP_TIMEOUT)
        resp.raise_for_status()
        tables = pd.read_html(pd.io.common.StringIO(resp.text),
                              attrs={"id": table_id})
        df = tables[0]

        # Try each candidate column name in order
        col = next((c for c in symbol_cols if c in df.columns), None)
        if col is None:
            print(f"  [universe] Column not found. Available: {list(df.columns)}")
            return []

        tickers = df[col].astype(str).tolist()
        # Wikipedia uses dots (BRK.B); yfinance wants dashes (BRK-B)
        tickers = [t.replace(".", "-") for t in tickers
                   if isinstance(t, str) and t not in ("nan", "")]
        return tickers
    except Exception as e:
        print(f"  [universe] Wikipedia scrape failed ({url}): {e}")
        return []


def get_us_universe() -> list[str]:
    """
    Fetch S&P 500 + S&P 400 MidCap + S&P 600 SmallCap from Wikipedia.
    Returns a deduplicated list of ~1,500 tickers.
    """
    print("[universe] Fetching S&P 1500 from Wikipedia…")

    sources = [
        (
            "S&P 500",
            "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
            "constituents",
            ["Symbol", "Ticker", "Ticker symbol"],
        ),
        (
            "S&P 400",
            "https://en.wikipedia.org/wiki/List_of_S%26P_400_companies",
            "constituents",
            ["Ticker", "Symbol", "Ticker symbol"],
        ),
        (
            "S&P 600",
            "https://en.wikipedia.org/wiki/List_of_S%26P_600_companies",
            "constituents",
            ["Ticker", "Symbol", "Ticker symbol"],
        ),
    ]

    all_tickers = set()
    for name, url, table_id, cols in sources:
        tickers = _scrape_wikipedia_table(url, table_id, cols)
        print(f"  [universe] {name}: {len(tickers)} tickers")
        all_tickers.update(tickers)
        time.sleep(1)   # polite delay between Wikipedia requests

    result = sorted(all_tickers)
    print(f"[universe] US (S&P 1500): {len(result)} tickers total")
    return result


# ══════════════════════════════════════════════════════════════════════════════
# China — Static comprehensive lists + optional live akshare refresh
# ══════════════════════════════════════════════════════════════════════════════
#
# akshare pulls from EastMoney which is geo-restricted outside China.
# The static lists below cover all major constituents. Run with a Chinese
# VPN or from within China to get a full live refresh via akshare.
#
# Shanghai codes: 600xxx, 601xxx, 603xxx, 605xxx (main board)
# Shenzhen codes: 000xxx (main), 001xxx (main), 002xxx (SME), 300xxx (ChiNext)
# Hong Kong codes: 4-digit zero-padded, e.g. 0700.HK

# ── Shanghai (.SS) ────────────────────────────────────────────────────────────
_SS_STATIC = [
    # Financials
    "600036.SS","601398.SS","601288.SS","601166.SS","601988.SS",
    "601328.SS","600016.SS","601601.SS","601318.SS","601628.SS",
    "601336.SS","600030.SS","601688.SS","601211.SS","600837.SS",
    # Consumer / Staples
    "600519.SS","600887.SS","600276.SS","603288.SS","600690.SS",
    "600048.SS","600309.SS","603986.SS","600196.SS","600585.SS",
    # Energy / Resources
    "600028.SS","600900.SS","601088.SS","601857.SS","600011.SS",
    "601985.SS","600025.SS","600886.SS","601666.SS","600362.SS",
    # Industrials / Infrastructure
    "601390.SS","601186.SS","601800.SS","600010.SS","600018.SS",
    "601006.SS","601872.SS","600029.SS","601111.SS","600050.SS",
    # Technology
    "600703.SS","603501.SS","600745.SS","601360.SS","600588.SS",
    "603799.SS","600183.SS","600522.SS","603160.SS","600570.SS",
    # Healthcare
    "600276.SS","601607.SS","600436.SS","600763.SS","603259.SS",
    "600867.SS","600812.SS","603858.SS","600332.SS","600161.SS",
    # Materials
    "600019.SS","600581.SS","600126.SS","601600.SS","600060.SS",
    "600150.SS","600201.SS","600251.SS","600316.SS","600346.SS",
    # More large caps
    "600000.SS","600015.SS","600020.SS","600021.SS","600022.SS",
    "600026.SS","600031.SS","600033.SS","600038.SS","600039.SS",
    "600048.SS","600050.SS","600051.SS","600052.SS","600053.SS",
    "600055.SS","600056.SS","600058.SS","600059.SS","600060.SS",
    "600061.SS","600062.SS","600064.SS","600066.SS","600068.SS",
    "600069.SS","600070.SS","600071.SS","600072.SS","600073.SS",
    "600075.SS","600076.SS","600077.SS","600078.SS","600079.SS",
    "600080.SS","600081.SS","600082.SS","600083.SS","600084.SS",
    "600085.SS","600086.SS","600087.SS","600088.SS","600089.SS",
    "600090.SS","600091.SS","600093.SS","600094.SS","600095.SS",
    "600096.SS","600097.SS","600098.SS","600099.SS","600100.SS",
]

# ── Shenzhen (.SZ) ────────────────────────────────────────────────────────────
_SZ_STATIC = [
    # Main board (000xxx)
    "000001.SZ","000002.SZ","000006.SZ","000007.SZ","000008.SZ",
    "000009.SZ","000010.SZ","000011.SZ","000012.SZ","000014.SZ",
    "000016.SZ","000017.SZ","000019.SZ","000020.SZ","000021.SZ",
    "000023.SZ","000025.SZ","000026.SZ","000027.SZ","000028.SZ",
    "000029.SZ","000030.SZ","000031.SZ","000032.SZ","000033.SZ",
    "000034.SZ","000036.SZ","000037.SZ","000038.SZ","000039.SZ",
    "000040.SZ","000042.SZ","000043.SZ","000045.SZ","000046.SZ",
    "000048.SZ","000049.SZ","000050.SZ","000055.SZ","000056.SZ",
    "000058.SZ","000059.SZ","000060.SZ","000061.SZ","000062.SZ",
    "000063.SZ","000065.SZ","000066.SZ","000068.SZ","000069.SZ",
    "000070.SZ","000078.SZ","000079.SZ","000080.SZ","000081.SZ",
    "000082.SZ","000085.SZ","000088.SZ","000089.SZ","000090.SZ",
    "000091.SZ","000092.SZ","000093.SZ","000096.SZ","000099.SZ",
    "000100.SZ","000150.SZ","000151.SZ","000152.SZ","000153.SZ",
    "000156.SZ","000158.SZ","000159.SZ","000160.SZ","000161.SZ",
    # Major names
    "000333.SZ","000568.SZ","000596.SZ","000625.SZ","000630.SZ",
    "000651.SZ","000656.SZ","000661.SZ","000671.SZ","000688.SZ",
    "000700.SZ","000708.SZ","000709.SZ","000711.SZ","000712.SZ",
    "000718.SZ","000725.SZ","000728.SZ","000729.SZ","000733.SZ",
    "000738.SZ","000739.SZ","000750.SZ","000758.SZ","000761.SZ",
    "000768.SZ","000776.SZ","000778.SZ","000783.SZ","000786.SZ",
    "000800.SZ","000807.SZ","000810.SZ","000813.SZ","000819.SZ",
    "000820.SZ","000821.SZ","000822.SZ","000825.SZ","000826.SZ",
    "000830.SZ","000831.SZ","000833.SZ","000836.SZ","000839.SZ",
    "000848.SZ","000850.SZ","000851.SZ","000852.SZ","000853.SZ",
    "000856.SZ","000858.SZ","000859.SZ","000860.SZ","000861.SZ",
    "000862.SZ","000863.SZ","000868.SZ","000869.SZ","000876.SZ",
    "000877.SZ","000878.SZ","000880.SZ","000881.SZ","000882.SZ",
    "000883.SZ","000885.SZ","000886.SZ","000887.SZ","000888.SZ",
    # SME board (002xxx)
    "002001.SZ","002002.SZ","002003.SZ","002004.SZ","002005.SZ",
    "002007.SZ","002008.SZ","002009.SZ","002010.SZ","002011.SZ",
    "002013.SZ","002014.SZ","002015.SZ","002016.SZ","002017.SZ",
    "002019.SZ","002020.SZ","002021.SZ","002022.SZ","002023.SZ",
    "002024.SZ","002025.SZ","002026.SZ","002027.SZ","002028.SZ",
    "002030.SZ","002031.SZ","002032.SZ","002033.SZ","002034.SZ",
    "002035.SZ","002036.SZ","002037.SZ","002038.SZ","002039.SZ",
    "002040.SZ","002041.SZ","002042.SZ","002043.SZ","002044.SZ",
    "002045.SZ","002049.SZ","002050.SZ","002051.SZ","002052.SZ",
    "002053.SZ","002056.SZ","002057.SZ","002058.SZ","002059.SZ",
    "002060.SZ","002061.SZ","002062.SZ","002063.SZ","002064.SZ",
    "002065.SZ","002066.SZ","002068.SZ","002069.SZ","002070.SZ",
    "002074.SZ","002075.SZ","002076.SZ","002077.SZ","002078.SZ",
    "002079.SZ","002080.SZ","002081.SZ","002082.SZ","002083.SZ",
    "002085.SZ","002086.SZ","002087.SZ","002088.SZ","002089.SZ",
    "002090.SZ","002091.SZ","002092.SZ","002093.SZ","002094.SZ",
    "002095.SZ","002096.SZ","002097.SZ","002098.SZ","002099.SZ",
    "002100.SZ","002101.SZ","002102.SZ","002103.SZ","002104.SZ",
    "002179.SZ","002202.SZ","002230.SZ","002236.SZ","002241.SZ",
    "002252.SZ","002271.SZ","002294.SZ","002299.SZ","002304.SZ",
    "002311.SZ","002352.SZ","002371.SZ","002372.SZ","002373.SZ",
    "002375.SZ","002376.SZ","002385.SZ","002390.SZ","002399.SZ",
    "002405.SZ","002408.SZ","002415.SZ","002416.SZ","002422.SZ",
    "002423.SZ","002424.SZ","002426.SZ","002429.SZ","002430.SZ",
    "002431.SZ","002432.SZ","002436.SZ","002439.SZ","002440.SZ",
    "002444.SZ","002450.SZ","002456.SZ","002460.SZ","002463.SZ",
    "002466.SZ","002468.SZ","002470.SZ","002471.SZ","002475.SZ",
    "002476.SZ","002477.SZ","002481.SZ","002482.SZ","002484.SZ",
    "002487.SZ","002493.SZ","002495.SZ","002500.SZ","002508.SZ",
    "002555.SZ","002557.SZ","002558.SZ","002568.SZ","002572.SZ",
    "002579.SZ","002594.SZ","002601.SZ","002602.SZ","002603.SZ",
    "002604.SZ","002607.SZ","002608.SZ","002610.SZ","002611.SZ",
    "002612.SZ","002614.SZ","002616.SZ","002624.SZ","002625.SZ",
    "002626.SZ","002627.SZ","002628.SZ","002629.SZ","002630.SZ",
    # ChiNext (300xxx)
    "300001.SZ","300002.SZ","300003.SZ","300004.SZ","300005.SZ",
    "300006.SZ","300007.SZ","300008.SZ","300009.SZ","300010.SZ",
    "300011.SZ","300012.SZ","300013.SZ","300014.SZ","300015.SZ",
    "300017.SZ","300018.SZ","300019.SZ","300020.SZ","300022.SZ",
    "300024.SZ","300025.SZ","300026.SZ","300027.SZ","300028.SZ",
    "300029.SZ","300033.SZ","300034.SZ","300035.SZ","300036.SZ",
    "300037.SZ","300038.SZ","300039.SZ","300040.SZ","300041.SZ",
    "300042.SZ","300043.SZ","300044.SZ","300045.SZ","300046.SZ",
    "300047.SZ","300048.SZ","300049.SZ","300050.SZ","300051.SZ",
    "300052.SZ","300053.SZ","300054.SZ","300055.SZ","300056.SZ",
    "300057.SZ","300058.SZ","300059.SZ","300060.SZ","300061.SZ",
    "300062.SZ","300063.SZ","300064.SZ","300065.SZ","300066.SZ",
    "300067.SZ","300068.SZ","300069.SZ","300070.SZ","300071.SZ",
    "300072.SZ","300073.SZ","300074.SZ","300075.SZ","300076.SZ",
    "300122.SZ","300124.SZ","300133.SZ","300136.SZ","300142.SZ",
    "300144.SZ","300146.SZ","300148.SZ","300168.SZ","300170.SZ",
    "300171.SZ","300182.SZ","300183.SZ","300184.SZ","300187.SZ",
    "300188.SZ","300190.SZ","300191.SZ","300192.SZ","300193.SZ",
    "300207.SZ","300212.SZ","300223.SZ","300228.SZ","300229.SZ",
    "300233.SZ","300236.SZ","300251.SZ","300253.SZ","300257.SZ",
    "300271.SZ","300274.SZ","300276.SZ","300285.SZ","300286.SZ",
    "300288.SZ","300296.SZ","300297.SZ","300315.SZ","300316.SZ",
    "300317.SZ","300318.SZ","300319.SZ","300347.SZ","300357.SZ",
    "300360.SZ","300374.SZ","300376.SZ","300379.SZ","300382.SZ",
    "300383.SZ","300384.SZ","300385.SZ","300388.SZ","300389.SZ",
    "300390.SZ","300394.SZ","300395.SZ","300396.SZ","300397.SZ",
    "300399.SZ","300400.SZ","300401.SZ","300408.SZ","300413.SZ",
    "300418.SZ","300419.SZ","300420.SZ","300421.SZ","300422.SZ",
    "300423.SZ","300424.SZ","300425.SZ","300426.SZ","300427.SZ",
    "300428.SZ","300429.SZ","300430.SZ","300433.SZ","300450.SZ",
    "300451.SZ","300452.SZ","300453.SZ","300454.SZ","300455.SZ",
    "300456.SZ","300457.SZ","300458.SZ","300459.SZ","300460.SZ",
    "300463.SZ","300468.SZ","300469.SZ","300470.SZ","300471.SZ",
    "300472.SZ","300473.SZ","300474.SZ","300475.SZ","300476.SZ",
    "300477.SZ","300478.SZ","300479.SZ","300480.SZ","300481.SZ",
    "300482.SZ","300483.SZ","300484.SZ","300485.SZ","300486.SZ",
    "300487.SZ","300488.SZ","300489.SZ","300490.SZ","300491.SZ",
    "300493.SZ","300496.SZ","300498.SZ","300499.SZ","300500.SZ",
    "300502.SZ","300503.SZ","300504.SZ","300505.SZ","300506.SZ",
    "300507.SZ","300508.SZ","300509.SZ","300510.SZ","300511.SZ",
    "300513.SZ","300515.SZ","300516.SZ","300517.SZ","300518.SZ",
    "300519.SZ","300520.SZ","300521.SZ","300522.SZ","300523.SZ",
    "300526.SZ","300529.SZ","300530.SZ","300531.SZ","300533.SZ",
    "300534.SZ","300535.SZ","300536.SZ","300537.SZ","300538.SZ",
    "300539.SZ","300540.SZ","300541.SZ","300543.SZ","300547.SZ",
    "300548.SZ","300549.SZ","300550.SZ","300551.SZ","300552.SZ",
    "300553.SZ","300554.SZ","300555.SZ","300556.SZ","300557.SZ",
    "300558.SZ","300559.SZ","300560.SZ","300561.SZ","300562.SZ",
    "300563.SZ","300564.SZ","300565.SZ","300566.SZ","300568.SZ",
    "300569.SZ","300570.SZ","300571.SZ","300572.SZ","300573.SZ",
    "300601.SZ","300604.SZ","300607.SZ","300610.SZ","300613.SZ",
    "300616.SZ","300617.SZ","300618.SZ","300619.SZ","300621.SZ",
    "300622.SZ","300623.SZ","300624.SZ","300625.SZ","300628.SZ",
    "300629.SZ","300630.SZ","300631.SZ","300632.SZ","300633.SZ",
    "300634.SZ","300635.SZ","300636.SZ","300637.SZ","300638.SZ",
    "300639.SZ","300640.SZ","300641.SZ","300642.SZ","300643.SZ",
    "300645.SZ","300647.SZ","300649.SZ","300650.SZ","300651.SZ",
    "300652.SZ","300653.SZ","300654.SZ","300655.SZ","300656.SZ",
    "300657.SZ","300658.SZ","300659.SZ","300661.SZ","300662.SZ",
    "300663.SZ","300664.SZ","300665.SZ","300666.SZ","300667.SZ",
    "300668.SZ","300669.SZ","300670.SZ","300671.SZ","300672.SZ",
    "300674.SZ","300676.SZ","300677.SZ","300678.SZ","300679.SZ",
    "300680.SZ","300681.SZ","300682.SZ","300683.SZ","300685.SZ",
    "300686.SZ","300687.SZ","300688.SZ","300689.SZ","300690.SZ",
    "300691.SZ","300692.SZ","300693.SZ","300694.SZ","300695.SZ",
    "300696.SZ","300697.SZ","300698.SZ","300699.SZ","300700.SZ",
    "300701.SZ","300702.SZ","300703.SZ","300705.SZ","300706.SZ",
    "300707.SZ","300708.SZ","300709.SZ","300710.SZ","300711.SZ",
    "300712.SZ","300713.SZ","300715.SZ","300716.SZ","300717.SZ",
    "300718.SZ","300719.SZ","300720.SZ","300721.SZ","300722.SZ",
    "300723.SZ","300724.SZ","300725.SZ","300726.SZ","300727.SZ",
    "300728.SZ","300729.SZ","300730.SZ","300731.SZ","300732.SZ",
    "300733.SZ","300735.SZ","300736.SZ","300737.SZ","300738.SZ",
    "300739.SZ","300740.SZ","300741.SZ","300742.SZ","300743.SZ",
    "300745.SZ","300746.SZ","300747.SZ","300748.SZ","300749.SZ",
    "300750.SZ","300751.SZ","300752.SZ","300753.SZ","300754.SZ",
    "300755.SZ","300756.SZ","300757.SZ","300758.SZ","300759.SZ",
    "300760.SZ","300761.SZ","300762.SZ","300763.SZ","300765.SZ",
    "300766.SZ","300767.SZ","300768.SZ","300769.SZ","300770.SZ",
    "300771.SZ","300772.SZ","300773.SZ","300775.SZ","300776.SZ",
    "300777.SZ","300778.SZ","300779.SZ","300780.SZ","300781.SZ",
    "300782.SZ","300783.SZ","300785.SZ","300786.SZ","300787.SZ",
    "300788.SZ","300789.SZ","300790.SZ","300791.SZ","300792.SZ",
    "300793.SZ","300794.SZ","300795.SZ","300796.SZ","300797.SZ",
    "300798.SZ","300799.SZ","300800.SZ","300801.SZ","300802.SZ",
    "300803.SZ","300804.SZ","300805.SZ","300806.SZ","300807.SZ",
    "300808.SZ","300809.SZ","300810.SZ","300811.SZ","300812.SZ",
    "300813.SZ","300814.SZ","300815.SZ","300816.SZ","300817.SZ",
    "300818.SZ","300819.SZ","300820.SZ","300821.SZ","300822.SZ",
    "300823.SZ","300824.SZ","300825.SZ","300826.SZ","300827.SZ",
    "300828.SZ","300829.SZ","300830.SZ","300831.SZ","300832.SZ",
    "300833.SZ","300834.SZ","300835.SZ","300836.SZ","300837.SZ",
    "300838.SZ","300839.SZ","300840.SZ","300841.SZ","300842.SZ",
    "300843.SZ","300845.SZ","300846.SZ","300847.SZ","300848.SZ",
    "300849.SZ","300850.SZ","300851.SZ","300852.SZ","300853.SZ",
    "300854.SZ","300855.SZ","300856.SZ","300857.SZ","300858.SZ",
    "300859.SZ","300860.SZ","300861.SZ","300862.SZ","300863.SZ",
    "300864.SZ","300865.SZ","300866.SZ","300867.SZ","300868.SZ",
    "300869.SZ","300870.SZ","300871.SZ","300872.SZ","300873.SZ",
    "300874.SZ","300875.SZ","300876.SZ","300877.SZ","300878.SZ",
    "300879.SZ","300880.SZ","300881.SZ","300882.SZ","300883.SZ",
    "300884.SZ","300885.SZ","300886.SZ","300887.SZ","300888.SZ",
    "300889.SZ","300890.SZ","300891.SZ","300892.SZ","300893.SZ",
    "300894.SZ","300895.SZ","300896.SZ","300897.SZ","300898.SZ",
    "300899.SZ","300900.SZ","300901.SZ","300902.SZ","300903.SZ",
    "300904.SZ","300905.SZ","300906.SZ","300907.SZ","300908.SZ",
    "300909.SZ","300910.SZ","300911.SZ","300912.SZ","300913.SZ",
    "300915.SZ","300916.SZ","300917.SZ","300918.SZ","300919.SZ",
    "300920.SZ","300921.SZ","300922.SZ","300923.SZ","300924.SZ",
    "300925.SZ","300926.SZ","300927.SZ","300928.SZ","300929.SZ",
    "300930.SZ","300931.SZ","300932.SZ","300933.SZ","300934.SZ",
    "300935.SZ","300936.SZ","300937.SZ","300938.SZ","300939.SZ",
    "300940.SZ","300941.SZ","300942.SZ","300943.SZ","300944.SZ",
    "300945.SZ","300946.SZ","300947.SZ","300948.SZ","300949.SZ",
    "300950.SZ","300951.SZ","300952.SZ","300953.SZ","300954.SZ",
    "300955.SZ","300956.SZ","300957.SZ","300958.SZ","300959.SZ",
    "300960.SZ","300961.SZ","300962.SZ","300963.SZ","300964.SZ",
    "300965.SZ","300966.SZ","300967.SZ","300968.SZ","300969.SZ",
    "300970.SZ","300971.SZ","300972.SZ","300973.SZ","300974.SZ",
    "300975.SZ","300976.SZ","300977.SZ","300978.SZ","300979.SZ",
    "300980.SZ","300981.SZ","300982.SZ","300983.SZ","300984.SZ",
    "300985.SZ","300986.SZ","300987.SZ","300988.SZ","300989.SZ",
    "300990.SZ","300991.SZ","300992.SZ","300993.SZ","300994.SZ",
    "300995.SZ","300996.SZ","300997.SZ","300998.SZ","300999.SZ",
]

# ── Hong Kong (.HK) ───────────────────────────────────────────────────────────
_HK_STATIC = [
    # Hang Seng Index & major blue chips
    "0700.HK","0941.HK","0005.HK","0939.HK","1299.HK","0388.HK",
    "2318.HK","1398.HK","2628.HK","0883.HK","0386.HK","0011.HK",
    "0003.HK","0006.HK","0012.HK","0016.HK","0017.HK","0019.HK",
    "0020.HK","0023.HK","0027.HK","0066.HK","0083.HK","0101.HK",
    "0151.HK","0175.HK","0267.HK","0288.HK","0291.HK","0293.HK",
    "0316.HK","0322.HK","0330.HK","0341.HK","0345.HK","0358.HK",
    "0363.HK","0371.HK","0384.HK","0392.HK","0400.HK","0410.HK",
    "0425.HK","0435.HK","0440.HK","0454.HK","0460.HK","0467.HK",
    "0489.HK","0494.HK","0522.HK","0525.HK","0536.HK","0548.HK",
    "0552.HK","0560.HK","0563.HK","0570.HK","0575.HK","0576.HK",
    "0579.HK","0582.HK","0586.HK","0588.HK","0590.HK","0604.HK",
    "0606.HK","0619.HK","0636.HK","0639.HK","0656.HK","0658.HK",
    "0660.HK","0669.HK","0683.HK","0688.HK","0696.HK","0728.HK",
    "0737.HK","0753.HK","0762.HK","0763.HK","0772.HK","0780.HK",
    "0788.HK","0799.HK","0806.HK","0813.HK","0817.HK","0819.HK",
    "0823.HK","0836.HK","0837.HK","0839.HK","0845.HK","0853.HK",
    "0857.HK","0868.HK","0874.HK","0881.HK","0884.HK","0886.HK",
    "0895.HK","0902.HK","0909.HK","0914.HK","0916.HK","0921.HK",
    "0960.HK","0966.HK","0968.HK","0981.HK","0992.HK","0998.HK",
    "1003.HK","1008.HK","1010.HK","1024.HK","1025.HK","1030.HK",
    "1033.HK","1038.HK","1044.HK","1053.HK","1055.HK","1057.HK",
    "1059.HK","1060.HK","1061.HK","1062.HK","1066.HK","1068.HK",
    "1071.HK","1072.HK","1075.HK","1080.HK","1083.HK","1084.HK",
    "1088.HK","1093.HK","1099.HK","1101.HK","1103.HK","1107.HK",
    "1109.HK","1113.HK","1114.HK","1119.HK","1122.HK","1123.HK",
    "1128.HK","1133.HK","1137.HK","1138.HK","1139.HK","1143.HK",
    "1145.HK","1148.HK","1157.HK","1159.HK","1161.HK","1163.HK",
    "1166.HK","1167.HK","1169.HK","1171.HK","1175.HK","1177.HK",
    "1180.HK","1182.HK","1184.HK","1186.HK","1188.HK","1193.HK",
    "1196.HK","1199.HK","1200.HK","1201.HK","1203.HK","1205.HK",
    "1207.HK","1208.HK","1209.HK","1211.HK","1212.HK","1213.HK",
    "1215.HK","1216.HK","1217.HK","1218.HK","1221.HK","1222.HK",
    "1223.HK","1224.HK","1225.HK","1226.HK","1227.HK","1228.HK",
    "1229.HK","1230.HK","1231.HK","1232.HK","1233.HK","1234.HK",
    "1235.HK","1236.HK","1238.HK","1239.HK","1240.HK","1241.HK",
    "1243.HK","1245.HK","1246.HK","1247.HK","1248.HK","1249.HK",
    "1250.HK","1251.HK","1252.HK","1253.HK","1255.HK","1256.HK",
    "1257.HK","1258.HK","1259.HK","1260.HK","1261.HK","1262.HK",
    "1263.HK","1265.HK","1266.HK","1268.HK","1269.HK","1270.HK",
    "1271.HK","1272.HK","1273.HK","1275.HK","1276.HK","1277.HK",
    "1278.HK","1280.HK","1281.HK","1282.HK","1283.HK","1285.HK",
    "1286.HK","1287.HK","1288.HK","1289.HK","1290.HK","1291.HK",
    "1292.HK","1293.HK","1294.HK","1295.HK","1296.HK","1297.HK",
    "1298.HK","1300.HK","1301.HK","1302.HK","1303.HK","1304.HK",
    "1305.HK","1306.HK","1308.HK","1310.HK","1311.HK","1312.HK",
    "1313.HK","1314.HK","1315.HK","1316.HK","1317.HK","1318.HK",
    "1319.HK","1321.HK","1322.HK","1323.HK","1324.HK","1325.HK",
    "2018.HK","2019.HK","2020.HK","2038.HK","2039.HK","2099.HK",
    "2196.HK","2202.HK","2208.HK","2238.HK","2269.HK","2282.HK",
    "2313.HK","2319.HK","2333.HK","2338.HK","2343.HK","2355.HK",
    "2359.HK","2362.HK","2368.HK","2369.HK","2378.HK","2382.HK",
    "2388.HK","2393.HK","2399.HK","2400.HK","2448.HK","2600.HK",
    "2601.HK","2607.HK","2611.HK","2618.HK","2626.HK","2638.HK",
    "2688.HK","2689.HK","2799.HK","2800.HK","2801.HK","2802.HK",
    "2803.HK","2804.HK","2805.HK","2806.HK","2807.HK","2808.HK",
    "2809.HK","2810.HK","2811.HK","2812.HK","2813.HK","2814.HK",
    "2815.HK","2816.HK","2817.HK","2818.HK","2819.HK","2820.HK",
    "3690.HK","3692.HK","3698.HK","3699.HK","3700.HK","3701.HK",
    "3708.HK","3709.HK","3718.HK","3719.HK","3728.HK","3737.HK",
    "3738.HK","3759.HK","3760.HK","3768.HK","3778.HK","3788.HK",
    "3789.HK","3798.HK","3799.HK","3800.HK","3808.HK","3813.HK",
    "3816.HK","3818.HK","3819.HK","3820.HK","3821.HK","3822.HK",
    "3828.HK","3838.HK","3839.HK","3848.HK","3858.HK","3868.HK",
    "3869.HK","3878.HK","3888.HK","3898.HK","3899.HK","3900.HK",
    "3908.HK","3918.HK","3928.HK","3938.HK","3948.HK","3958.HK",
    "3968.HK","3978.HK","3988.HK","3998.HK","6030.HK","6060.HK",
    "6078.HK","6080.HK","6088.HK","6098.HK","6099.HK","6100.HK",
    "6110.HK","6111.HK","6113.HK","6116.HK","6118.HK","6119.HK",
    "6120.HK","6121.HK","6122.HK","6123.HK","6124.HK","6125.HK",
    "6126.HK","6127.HK","6128.HK","6129.HK","6130.HK","6131.HK",
    "6132.HK","6133.HK","6136.HK","6138.HK","6139.HK","6158.HK",
    "6160.HK","6161.HK","6162.HK","6163.HK","6166.HK","6168.HK",
    "6169.HK","6170.HK","6178.HK","6180.HK","6181.HK","6182.HK",
    "6183.HK","6185.HK","6186.HK","6188.HK","6189.HK","6190.HK",
    "6191.HK","6192.HK","6193.HK","6196.HK","6198.HK","6199.HK",
]


def _try_akshare_refresh(static_list: list, market: str) -> list[str]:
    """
    Attempt a live akshare refresh. Returns static list if akshare fails
    (e.g. when running outside China without VPN).
    """
    try:
        import akshare as ak
        if market == "SS":
            df = ak.stock_sh_a_spot_em()
            codes = df["代码"].astype(str).tolist()
            tickers = [f"{c}.SS" for c in codes]
        elif market == "SZ":
            df = ak.stock_sz_a_spot_em()
            codes = df["代码"].astype(str).tolist()
            tickers = [f"{c}.SZ" for c in codes]
        elif market == "HK":
            df = ak.stock_hk_spot_em()
            codes = df["代码"].astype(str).tolist()
            tickers = [f"{c.zfill(4)}.HK" for c in codes]
        else:
            return static_list
        print(f"  [universe] {market}: live akshare refresh — {len(tickers)} tickers")
        return tickers
    except Exception:
        print(f"  [universe] {market}: akshare unavailable, using static list "
              f"({len(static_list)} tickers)")
        return static_list


def get_china_universe() -> dict[str, list[str]]:
    return {
        "SS": _try_akshare_refresh(_SS_STATIC, "SS"),
        "SZ": _try_akshare_refresh(_SZ_STATIC, "SZ"),
        "HK": _try_akshare_refresh(_HK_STATIC, "HK"),
    }


# ══════════════════════════════════════════════════════════════════════════════
# Main entry point
# ══════════════════════════════════════════════════════════════════════════════

def build_universe(include_us=True, include_china=True) -> dict[str, list[str]]:
    """
    Returns {market_label: [tickers]} consumed by scanner.py.
    Labels: "US", "SS", "SZ", "HK"
    """
    universe = {}

    if include_us:
        universe["US"] = get_us_universe()

    if include_china:
        china = get_china_universe()
        universe.update(china)

    total = sum(len(v) for v in universe.values())
    print(f"\n[universe] Total tickers: {total}")
    for market, tickers in universe.items():
        print(f"  {market}: {len(tickers)}")

    return universe


def clean_static_lists(dry_run: bool = False) -> None:
    """
    Check every ticker in the China static lists against yfinance.
    Removes any ticker that has no price data in the last 30 days (delisted).

    Results are printed to the terminal. Unless dry_run=True, this function
    rewrites universe.py in-place with the cleaned lists.

    Usage:
        python3 universe.py --clean          # check + rewrite file
        python3 universe.py --clean --dry    # check only, don't rewrite
    """
    from fetcher import is_alive

    markets = {
        "SS": _SS_STATIC,
        "SZ": _SZ_STATIC,
        "HK": _HK_STATIC,
    }

    cleaned = {}
    for market, tickers in markets.items():
        print(f"\n[clean] Checking {market} ({len(tickers)} tickers)…")
        alive, dead = [], []
        for i, t in enumerate(tickers):
            if i % 20 == 0:
                print(f"  {i}/{len(tickers)} …")
            if is_alive(t):
                alive.append(t)
            else:
                dead.append(t)
            time.sleep(0.15)

        print(f"  ✅ Alive: {len(alive)}   ❌ Delisted/dead: {len(dead)}")
        if dead:
            print(f"  Removing: {dead}")
        cleaned[market] = alive

    if dry_run:
        print("\n[clean] Dry run — no files modified.")
        return

    # Rewrite this file in-place, replacing the three _STATIC list definitions
    import re
    import os

    this_file = os.path.abspath(__file__)
    with open(this_file, "r", encoding="utf-8") as f:
        source = f.read()

    for market, var in [("SS", "_SS_STATIC"), ("SZ", "_SZ_STATIC"), ("HK", "_HK_STATIC")]:
        tickers = cleaned[market]
        # Build new list literal (4-space indent, 5 tickers per line)
        lines = []
        for i in range(0, len(tickers), 5):
            chunk = tickers[i:i+5]
            lines.append("    " + ",".join(f'"{t}"' for t in chunk) + ",")
        new_body = "\n".join(lines)
        # Replace the existing list body between the [ and ]
        pattern = rf"({re.escape(var)}\s*=\s*\[)[^\]]*(\])"
        replacement = rf"\1\n{new_body}\n\2"
        source = re.sub(pattern, replacement, source, flags=re.DOTALL)

    with open(this_file, "w", encoding="utf-8") as f:
        f.write(source)

    print(f"\n[clean] ✅ universe.py updated in-place.")
    total_removed = sum(
        len(markets[m]) - len(cleaned[m]) for m in markets
    )
    print(f"[clean] Removed {total_removed} dead tickers across SS/SZ/HK.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--clean", action="store_true",
                        help="Verify China static lists and remove delisted tickers")
    parser.add_argument("--dry",   action="store_true",
                        help="Used with --clean: check only, don't rewrite file")
    args = parser.parse_args()

    if args.clean:
        clean_static_lists(dry_run=args.dry)
    else:
        u = build_universe()
        with open("universe.json", "w", encoding="utf-8") as f:
            json.dump(u, f, ensure_ascii=False, indent=2)
        print("\nSaved universe.json")
