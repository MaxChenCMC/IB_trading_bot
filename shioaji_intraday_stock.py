import pandas as pd
import numpy as np
import time, warnings, os
from threading import Thread
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


def ohlc(sid, start, end):
    """
    獲取個股的1分K價量
    """
    df = pd.DataFrame({**api.kbars(api.Contracts.Stocks[sid], start, end)})
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


def bounce_trade_stock(contract, dd_target, dd_recent, vol_gain):
    """
    觸發條件：
    1. 日內回撤「> 3%」
    2. 近十分鐘回撤「> 1%」
    3. 當下價格 > 前3分K的均價
    4. 當下成交量是過去10分K均量的「1.33倍」
    """
    df = ohlc(contract)
    mdd = max(df["Close"].to_drawdown_series() * -100)
    cond1 = mdd > dd_target
    recent10_dd = df["Close"][-10:].to_drawdown_series()[-1] * -100
    cond2 = recent10_dd > dd_recent
    cond3 = df["Close"][-1] >= df["Close"][-4:-1].mean()
    cond4 = df["Volume"][-1] >= df["Volume"][-10:].mean() * vol_gain
    if cond1 and cond2 and cond3 and cond4:
        # 當4個條件都符合時就回報，並遞交委買單
        print(f"{contract}在{df[-1:].index.strftime('%H:%M:%S')[0]}時條件達成")
        # 低掛1個tick買進，非市價委託
        tick = 0.05 if df["Close"][-1] < 50 else 0.1
        order = api.Order(
            price=df["Close"][-1] - 1 * tick,
            quantity=1,
            action="Buy",
            price_type="LMT",
            order_type="ROD",
        )
        trade = api.place_order(api.Contracts.Stocks[contract], order)
        # 回報託買明細
        print(pd.DataFrame({**trade}).T[["name", "action", "price"]][1:], "\n")
    else:
        macth = np.sum([cond1, cond2, cond3, cond4])
        #
        print(f"{contract}☛ {df['Close'][-1]}，僅符合 {macth}個條件，近10分鐘DD {recent10_dd:.3}％")


while True:
    # 只對單商品
    # test = Thread(target = bounce_trade('2605', 3, 1, 1.33))
    # test.start()

    # 對以下候選股
    for sid in ["2332", "2340", "2393", "8358", "2455", "3673"]:
        Thread(target=bounce_trade_stock(sid, 3, 1, 1.33)).start()
    print("===" * 17)
    time.sleep(5)
    os.system("cls")
