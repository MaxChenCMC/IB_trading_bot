import pandas as pd
import numpy as np
import time, warnings
from datetime import datetime, timedelta
import shioaji as sj

warnings.filterwarnings("ignore")

# 永豐API初始化、讀取憑證與登入
api = sj.Shioaji()
accounts = api.login(身份證字號, 密碼)
api.activate_ca(
    ca_path=憑證路徑,
    ca_passwd=身份證字號,
    person_id=身份證字號,
)

# 由於盤後盤無法交易現股，以及台指期與權的成交量會縮小，故在交易商品種類與觸發條件上需與日盤做區隔
yday = (datetime.today() - timedelta(1)).strftime("%Y-%m-%d")
tday = datetime.today().strftime("%Y-%m-%d")
am = tday + " 08:46:00"
pm = tday + " 15:01:00"


def ohlc(sid, start, end):
    """
    獲取個股的1分K價量
    """
    df = pd.DataFrame({**api.kbars(api.Contracts.Stocks[sid], start, end)})
    df.ts = pd.to_datetime(df.ts)
    df.set_index("ts", inplace=True)
    return df[["Open", "High", "Low", "Close", "Volume"]]


def ohlc_txf(sid, start, end):
    """
    獲取台指期的1分K價量
    """
    df = pd.DataFrame({**api.kbars(api.Contracts.Futures.TXF[sid], start, end)})
    df.ts = pd.to_datetime(df.ts)
    df.set_index("ts", inplace=True)
    return df[["Open", "High", "Low", "Close", "Volume"]]


def bid_increase(contract):
    """
    觀察最近一分鐘的委買量，是否比過去十分鐘的均量還多出25%。主要用在盤後盤的台指期
    """
    data = pd.DataFrame({**api.ticks(api.Contracts.Stocks[contract])})
    data.ts = pd.to_datetime(data.ts)
    data.set_index("ts", inplace=True)
    bid_1m = data["bid_volume"].resample("1Min", label="right", closed="right").sum()
    return (bid_1m > bid_1m.rolling(10).mean() * 1.25)[-1]


while True:
    """
    台指期日盤策略：
    1. 振幅全距僅50點內
    2. 最新報價大於3分K均價
    3. 近3分K均量大於目前成交易前20大的90%
    4. 前十大權值股，超過4檔的符合 bid_increase 函式條件
    """
    df = ohlc_txf("TXF202109", tday, tday)[am:]
    cond1 = max(df["High"][-15:]) - df["Close"][-1] > 50
    cond2 = df["Close"][-1] >= df["Close"][-3:].mean()
    cond3 = df["Volume"][-3:].mean() >= df["Volume"].nlargest(20)[-1] * 0.9
    cond4 = (
        np.sum(
            [
                bid_increase("2330"),
                bid_increase("2454"),
                bid_increase("2317"),
                bid_increase("2308"),
                bid_increase("2303"),
                bid_increase("6505"),
                bid_increase("1303"),
                bid_increase("1301"),
                bid_increase("2882"),
                bid_increase("2881"),
            ]
        )
        >= 4
    )
    if cond1 and cond2 and cond3 and cond4:
        print(f"{df[-1:].index[0].strftime('%H:%M:%S')}時條件達成")
        break
    else:
        macth = np.sum([cond1, cond2, cond3, cond4])
        print(f"目前{df['Close'][-1]}點，僅符合{macth}個條件")
        time.sleep(1)
