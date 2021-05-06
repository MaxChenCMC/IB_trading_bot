import ibapi, threading, time, os, math
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import *
import pandas as pd
import yfinance as yf

IBApi = EClient(EWrapper())
IBApi.connect('127.0.0.1', 7496, 1)

def quote(symbol):
    while True:
        df = pd.DataFrame(yf.download(symbol, period = '1d', interval = '1m'))
        global last_price
        trigger_price  = df['Adj Close'].mean() # 均價
        # 若以開盤價為基準☛ trigger_price  = df['Open'].first()
        # 跌破今低後才低掛0.3%委買☛ trigger_price  = df['Low'].min() * 0.997
        last_price = df['Adj Close'].last('T')[0]
        print(df.tail(3))
        print(f'觸發價 {trigger_price}，最新報價 {last_price}')
        if last_price <= trigger_price :
            break
        else:
            time.sleep(60) # yfinance 最快只能1分鐘1筆更新
            os.system("cls") # 清空舊的報價

symbol = input('今晚 我想來點... ').upper()
myThread = threading.Thread(target = quote(symbol), daemon =  True)
myThread.start()

# Order()與Contract()規範需依照IB的documentation
order = Order()
order.action = 'BUY'
# 這裡為觸價後低掛0.3%委買；乘1就是不討價還價，不能超過小數3位不然委託會NaN
order.lmtPrice = round(last_price * 0.997, 2)
print(f'委託價 {order.lmtPrice}')
# 單一個股欲下單金額，股數無條件進位
per_position_amt = 10000
order.totalQuantity = math.ceil(per_position_amt / last_price)
# 若直接市價'MKT'下單，則會忽略order.lmtPrice
order.orderType = 'LMT'
contract = Contract()
contract.symbol = symbol
contract.secType =  'STK'
contract.exchange = 'SMART'
contract.currency = 'USD'
# 第一個參數是委託單序號，不可重複，這用time.time()方便省事
IBApi.placeOrder(int(time.time()), contract, order)
print('\n ★ ★ ★ 委買成功')