import pandas as pd
import numpy as np
import time, os, ffn, warnings
from threading import Thread
from datetime import datetime, timedelta

warnings.filterwarnings("ignore")
import shioaji as sj

api = sj.Shioaji()
accounts = api.login("身份證字號", "密碼")
api.activate_ca(ca_path="憑證路徑", ca_passwd="身份證字號", person_id="密碼")

yday = (datetime.today() - timedelta(1)).strftime("%Y-%m-%d")
tday = datetime.today().strftime("%Y-%m-%d")
am = tday + " 08:46:00"
pm = tday + " 15:01:00"


def ohlc(sid, start, end):
    df = pd.DataFrame({**api.kbars(api.Contracts.Stocks[sid], start, end)})
    df.ts = pd.to_datetime(df.ts)
    df.set_index("ts", inplace=True)
    return df[["Open", "High", "Low", "Close", "Volume"]]


def ohlc_txf(sid, start, end):
    df = pd.DataFrame({**api.kbars(api.Contracts.Futures.TXF[sid], start, end)})
    df.ts = pd.to_datetime(df.ts)
    df.set_index("ts", inplace=True)
    return df[["Open", "High", "Low", "Close", "Volume"]]


def bid_increase(contract):
    data = pd.DataFrame({**api.ticks(api.Contracts.Stocks[contract])})
    data.ts = pd.to_datetime(data.ts)
    data.set_index("ts", inplace=True)
    bid_1m = data["bid_volume"].resample("1Min", label="right", closed="right").sum()
    return (bid_1m > bid_1m.rolling(10).mean() * 1.25)[-1]


def bounce_trade_stock(contract, dd_target, dd_recent, vol_gain):
    df = ohlc(contract)
    mdd = max(df["Close"].to_drawdown_series() * -100)
    cond1 = mdd > dd_target
    recent10_dd = df["Close"][-10:].to_drawdown_series()[-1] * -100
    cond2 = recent10_dd > dd_recent
    cond3 = df["Close"][-1] >= df["Close"][-4:-1].mean()
    cond4 = df["Volume"][-1] >= df["Volume"][-10:].mean() * vol_gain
    if cond1 and cond2 and cond3 and cond4:
        print(f"{contract}在{df[-1:].index.strftime('%H:%M:%S')[0]}時條件達成")
        tick = 0.05 if df["Close"][-1] < 50 else 0.1
        order = api.Order(
            price=df["Close"][-1] - 5 * tick,
            quantity=1,
            action="Buy",
            price_type="LMT",
            order_type="ROD",
        )
        trade = api.place_order(api.Contracts.Stocks[contract], order)
        print(pd.DataFrame({**trade}).T[["name", "action", "price"]][1:], "\n")
    else:
        macth = np.sum([cond1, cond2, cond3, cond4])
        print(
            f"{contract}☛ {df['Close'][-1]}，僅符合 {macth}個條件，近10分鐘DD {recent10_dd:.3}％"
        )  # MDD {mdd:.3}％

    # while True:
    #     for sid in ['2332','2340','2393','8358','2455','3673']:
    #         Thread(target = bounce_trade_stock(sid, 3, 1, 1.33)).start() # t3 = Thread(target = bounce_trade('2605', 10))  # t3.start()
    #     print('==='*17)
    #     time.sleep(5)
    #     os.system('cls')


while True:
    df = ohlc_txf("TXF202108", tday, tday)[am:]
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
