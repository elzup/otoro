from pprint import pprint

import numpy as np
import pandas as pd
import requests
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


from config import Tradeconfig
from ExecLogic import ExecLogic

# -----------------------------------------------------------------
# 取引所関係のmethod


def get_price_data():
    response = requests.get(
        "https://api.cryptowat.ch/markets/bitflyer/btcfxjpy/ohlc",
        params={
            "periods": period,
            "after": 1})
    response = response.json()
    result = response["result"][str(period)]
    response_data = []
    for i in range(len(result)):
        response_data.append(result[i])
    return response_data


# --------------------------------------------------------------------
# 評価値系

# RSIとMACDによる買いサイン
def buy_signal(response, i):
    ex = ExecLogic()
    if ex.buy_judge(data=response, i=i):
        print("pass")
        return True
    else:
        return False

# --------------------------------------------------------------
# ここからアルゴリズム


# 設定
upper_limit = Tradeconfig.sell_rate
lower_limit = Tradeconfig.close_rate
comm = 0.0015
comm2 = comm * 2
# 何秒足
period = Tradeconfig.size_candle
# flag
flag = {
    "check": True,
    "buy_position": False
}

res = get_price_data()
i = 0
profit = loss = count1 = count2 = drawdown = start = 0
price2 = 0

myjpy = 100000
mybtc = 0

asset_list = [myjpy]

pprint(len(res))

while i < 5500:
    while(flag["check"]):
        asset_list.append(myjpy + mybtc * res[i][4])
        if i > 5500:
            # asset_list.append(myjpy + mybtc * res[i][4])
            break

        if buy_signal(res, i):
            print("Send buy order")
            price = res[i][4]
            mybtc = myjpy / price * (1 - comm)
            myjpy = 0
            # print(myjpy+mybtc*res[i][4])
            flag["buy_position"] = True
            flag["check"] = False

        i += 1

    while(flag["buy_position"]):
        asset_list.append(myjpy + mybtc * res[i][4])
        if res[i][2] > price * upper_limit:
            print("rikaku:")
            count1 += 1
            profit += price * (upper_limit - 1 - comm2)
            myjpy = mybtc * res[i][4] * (1 - comm)
            mybtc = 0
            # print(myjpy+mybtc*res[i][4])

            flag["buy_position"] = False
            flag["check"] = True
        elif res[i][3] < price * lower_limit:
            print("sonkiri:")
            count2 += 1
            loss += price * (1 - lower_limit + comm2)
            myjpy = mybtc * res[i][4] * (1 - comm)
            mybtc = 0
            # print(myjpy+mybtc*res[i][4])

            flag["buy_position"] = False
            flag["check"] = True
        i += 1
        if i > 5500:
            # asset_list.append(myjpy + mybtc * res[i][4])
            break

    if drawdown > profit - loss:
        drawdown = profit - loss


# chart = list(map(lambda v: v[4], res))
# ts = pd.Series(chart, index=date_range('2000-01-01', periods=1000))

x = np.array(list(map(lambda v: pd.to_datetime(v[0], unit="s"), res[:len(asset_list)])))
v = np.array(list(map(lambda v: v[4], res[:len(asset_list)])))
yen = np.array(asset_list)
print(len(x))
print(len(yen))

df = pd.DataFrame({'i': x, 'v': v, 'yen': yen})
# df2 = pd.DataFrame(index=x, data=dict(v=v2))

fig, ax = plt.subplots()
ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))

print("profit:" + str(profit))
print("loss:" + str(loss))
print("earn:" + str(myjpy + mybtc * res[i][4]))
print("count1:" + str(count1))
print("count2:" + str(count2))


pr_pre = None
diff_pre = None
# for v in res:
#     pr = v[4]
#     if pr_pre is not None:
#         diff = pr_pre - pr
#         print(pr, diff, diff_pre)
#         diff_pre = diff
#     pr_pre = pr

plt.plot('i', 'v', data=df)
plt.plot('i', 'yen', data=df)
# plt.plot(df2.index, df2['v'])
plt.show()
