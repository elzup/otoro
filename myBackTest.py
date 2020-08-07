from pprint import pprint

import numpy as np
import pandas as pd
import requests
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.cm as cm

from config import Tradeconfig as tconf
from ExecLogic import ExecLogic
# if tconf.plot:
#     from datetime import datetime

# -----------------------------------------------------------------
# 取引所関係のmethod


def parse_csv_line(line):
    return list(map(float, line.split(",")))

# 2017~ からの5分足データ


def get_local_data(bgn=tconf.backtest_bgn, end=tconf.backtest_end):
    f = open("./data/btcjpn_2017_2020_5m.csv")
    txt = f.read()
    f.close()
    csvarr = list(map(parse_csv_line, txt.strip().split("\n")))

    # print(len(list(csvarr)))
    return np.array(list(csvarr)[bgn:end])


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
def buy_signal(response, i, size):
    ex = ExecLogic()
    return ex.buy_judge(data=response, i=i, size=size)


def sell_signal(response, i, size):
    ex = ExecLogic()
    return ex.sell_judge(data=response, i=i, size=size)

# --------------------------------------------------------------
# ここからアルゴリズム


comm = 0.0015
# 何秒足
period = tconf.size_candle
# flag
# res = get_price_data()


def backtest(res, count, size):
    # return str(size)
    i = 0
    # profit = loss = count1 = count2 = 0
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

            if buy_signal(res, i, size):
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
            if sell_signal(res, i, size):
                if tconf.log:
                    print("Sell order")
                    print(i)
                # print(datetime.fromtimestamp(res[i][0]))
                # count1 += 1
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

    if tconf.plot:
        print(len(asset_list))
        x = np.array(list(map(lambda v: pd.to_datetime(v[0], unit="s"), res[:len(asset_list)])))
        btc = np.array(list(map(lambda v: v[4], res[:len(asset_list)])))
        yen = np.array(asset_list)

        df = pd.DataFrame({'i': x, 'btc': btc, 'yen': yen})
        # df2 = pd.DataFrame(index=x, data=dict(v=v2))

        fig, ax = plt.subplots()
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))

        ax.plot('i', 'btc', data=df, color=cm.Set1.colors[0])
        ax2 = ax.twinx()
        ax2.plot('i', 'yen', data=df, color=cm.Set1.colors[1])
        plt.show()
        # fig.savefig(f"data/{tconf.backtest_season}_{size}.png")

    # print("profit:" + str(profit))
    # print("loss:" + str(loss))
    # print("earn:" + str(myjpy + mybtc * res[i][4]))
    # print("count1:" + str(count1))
    # print("count2:" + str(count2))
    # print(datetime.fromtimestamp(res[0][0]))
    # print(res[0][0])
    # print("〜")
    # print(datetime.fromtimestamp(res[-1][0]))
    print(res[-1][0])
    # print(f"{size},{asset_list[-1]}")
    return str(asset_list[-1])


def main():
    res = get_local_data()
    count = len(res)
    backtest(res, count, tconf.channel_breakout_size)


def range_backtest():
    band = 10000
    arr = []
    # for s in range(10, 32):
    for s in range(10, 32):
        res = get_local_data(band * s, band * (s + 1))
        count = len(res)
        # pprint(count)
        h = int(60 * 60 / tconf.size_candle)
        # h = 1
        arr.append(list(map(lambda i: backtest(res, count, h * i), range(6, 48))))
        # arr.append([str(100000 * res[-1][4] / res[0][4])])
    # print(arr)

    print("\n".join(map(lambda a: ",".join(a), np.transpose(arr))))


if __name__ == "__main__":
    main()
