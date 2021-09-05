# Application:
Subscribes real-time market data, places order when pattern fits certain criteria.

# Tools:
Processing high frequency data from broker’s official API(Sonipac-Shioaji, Capital-Skcom, Interactive broker-ibapi), inspecting trade results, intergrating account balance and existed position .

<hr>

#以永豐的shioaji為例

現股交易策略：
1. 日內回撤大於「參數2」
2. 近十分鐘回撤大於「參數3」
3. 當下價格大於前3分K的均價
4. 當下成交量是過去10分K均量的「參數4」

台指期日盤交易策略：
1. 振幅全距僅50點內
2. 最新報價大於3分K均價
3. 近3分K均量大於目前成交易前20大的90%
4. 前十大權值股，超過4檔的符合 bid_increase 函式條件
