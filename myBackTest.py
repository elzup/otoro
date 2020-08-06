from pprint import pprint

import numpy as np
import pandas as pd
import requests
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.cm as cm

from datetime import datetime
from config import Tradeconfig as tconf
from ExecLogic import ExecLogic

# -----------------------------------------------------------------
# 取引所関係のmethod


def parse_csv_line(line):
    return list(map(float, line.split(",")))

# 2017~ からの5分足データ


def get_local_data():
    f = open("./data/btcjpn_2017_2020_5m.csv")
    txt = f.read()
    f.close()
    csvarr = list(map(parse_csv_line, txt.strip().split("\n")))

    # print(len(list(csvarr)))
    return np.array(list(csvarr)[tconf.backtest_bgn:tconf.backtest_end])


def get_price_data():
    response = requests.get(
        "https://api.cryptowat.ch/markets/bitflyer/btcfxjpy/ohlc",
        params={
            "periods": period,
            "after": 1})
    response = response.json()
    result = response["result"][str(period)]
    return np.array(result)


# --------------------------------------------------------------------
# 評価値系

# RSIとMACDによる買いサイン
def buy_signal(response, i):
    ex = ExecLogic()
    return ex.buy_judge(data=response, i=i)


def sell_signal(response, i):
    ex = ExecLogic()
    return ex.sell_judge(data=response, i=i)

# --------------------------------------------------------------
# ここからアルゴリズム


comm = 0.0015
# 何秒足
period = tconf.size_candle
# flag
# res = get_price_data()


def backtest(res, count):
    i = 0
    profit = loss = count1 = count2 = 0
    flag = {
        "check": True,
        "buy_position": False
    }

    myjpy = 100000
    mybtc = 0

    asset_list = [myjpy]

    while i < count - 500:
        while(flag["check"]):
            try:
                asset_list.append(myjpy + mybtc * res[i][4])
            except BaseException:
                print(myjpy, mybtc)
                print(res[i])
            if i > count - 500:
                # asset_list.append(myjpy + mybtc * res[i][4])
                break

            if buy_signal(res, i):
                if tconf.log:
                    print("Buy order")
                    print(i)
                    # print(datetime.fromtimestamp(res[i][0]))

                price = res[i][4]
                mybtc = myjpy / price * (1 - comm)
                myjpy = 0
                # print(myjpy+mybtc*res[i][4])
                flag["buy_position"] = True
                flag["check"] = False

            i += 1

        while(flag["buy_position"]):
            asset_list.append(myjpy + mybtc * res[i][4])
            if sell_signal(res, i):
                if tconf.log:
                    print("Sell order")
                    print(i)
                # print(datetime.fromtimestamp(res[i][0]))
                count1 += 1
                myjpy = mybtc * res[i][4] * (1 - comm)
                mybtc = 0
                # print(myjpy+mybtc*res[i][4])

                flag["buy_position"] = False
                flag["check"] = True
            i += 1
            if i > count - 500:
                asset_list.append(myjpy + mybtc * res[i][4])
                break
    # chart = list(map(lambda v: v[4], res))
    # ts = pd.Series(chart, index=date_range('2000-01-01', periods=1000))

    x = np.array(list(map(lambda v: pd.to_datetime(v[0], unit="s"), res[:len(asset_list)])))
    btc = np.array(list(map(lambda v: v[4], res[:len(asset_list)])))
    yen = np.array(asset_list)
    print(len(x))
    print(len(yen))

    df = pd.DataFrame({'i': x, 'btc': btc, 'yen': yen})
    # df2 = pd.DataFrame(index=x, data=dict(v=v2))

    fig, ax = plt.subplots()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))

    ax.plot('i', 'btc', data=df, color=cm.Set1.colors[0])
    ax2 = ax.twinx()
    ax2.plot('i', 'yen', data=df, color=cm.Set1.colors[1])

    print("profit:" + str(profit))
    print("loss:" + str(loss))
    print("earn:" + str(myjpy + mybtc * res[i][4]))
    print("count1:" + str(count1))
    print("count2:" + str(count2))
    print(datetime.fromtimestamp(res[0][0]))
    print(res[0][0])
    print("〜")
    print(datetime.fromtimestamp(res[-1][0]))
    print(res[-1][0])
    print(asset_list[-1])

    fig.savefig("data/img.png")


def main():
    res = get_local_data()
    count = len(res)
    pprint(count)
    backtest(res, count)


if __name__ == "__main__":
    main()
