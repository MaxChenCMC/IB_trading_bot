# Application:
Subscribes real-time market data, places order when pattern fits certain criteria.

# Tools:
Processing high frequency data from broker’s official API(Sonipac-Shioaji, Capital-Skcom, Interactive broker-ibapi), inspecting trade results, intergrating account balance and existed position .

<hr>

# 以永豐的shioaji為例

#### 現股交易策略：
1. 日內回撤「> 3%」
2. 近十分鐘回撤「> 1%」
3. 當下價格 > 前3分K的均價
4. 當下成交量是過去10分K均量的「1.33倍」

☛ 條件達成後，掛比成交價低1個tick的委買價


#### 台指期日盤交易策略：
1. 近15分鐘跌點「> 50」
2. 最新報價大於3分K均價
3. 近3分K均量大於目前成交易前20大的90%
4. 前10大權值股，超過4檔的符合「bid_increase函式」的條件

☛ 條件達成後出現提示字串
