# from pprint import pprint

import numpy as np
import pandas as pd
import requests
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.cm as cm
import time
from datetime import datetime

from config import Tradeconfig as tconf
from logic import ExecLogic


# output_file_name = "./data/btcjpn_2017_2020_5m_full.csv"
output_file_name = "./data/btcjpn_2015_2020_5m_cc.csv"
# -----------------------------------------------------------------
# 取引所関係のmethod


def parse_csv_line(line):
    return list(map(float, line.split(",")))

# 2017~ からの5分足データ


def get_local_data():
    f = open(output_file_name)
    txt = f.read()
    f.close()
    csvarr = list(map(parse_csv_line, txt.strip().split("\n")))

    # print(len(list(csvarr)))
    return list(csvarr)


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


# comm = 0.0015
comm = 0
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
    change_point = res[0][1]

    daystep = 12 * 24
    while i < count - 500:
        while(flag["check"]):

            if i % daystep == 0:
                myjpy *= (1 - 0.00004)
            price = res[i][4]
            try:
                asset_list.append((myjpy * change_point / price) + mybtc * price)
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

                mybtc = (myjpy * price / change_point) / price * (1 - comm)
                myjpy = 0
                # print(myjpy+mybtc*res[i][4])
                flag["buy_position"] = True
                flag["check"] = False

            i += 1

        while(flag["buy_position"]):
            if i % daystep == 0:
                mybtc *= (1 - 0.00004)
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
                change_point = res[i][4]
            i += 1
            if i > count - 500:
                asset_list.append(myjpy + mybtc * res[i][4])
                break
    # chart = list(map(lambda v: v[4], res))
    # ts = pd.Series(chart, index=date_range('2000-01-01', periods=1000))

    if tconf.plot:
        # print(len(asset_list))
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
        # plt.show()

        def ymdformat(dt):
            return datetime.fromtimestamp(dt).strftime("%Y-%m-%d")

        filename = f"backtest_{ymdformat(res[0][0])}_{ymdformat(res[-1][0])}_{size}.png"
        fig.savefig(f"img/backtest63/{filename}")

        time.sleep(1)
        plt.close()

    # print("profit:" + str(profit))
    # print("loss:" + str(loss))
    # print("earn:" + str(myjpy + mybtc * res[i][4]))
    # print("count1:" + str(count1))
    # print("count2:" + str(count2))
    # print(datetime.fromtimestamp(res[0][0]))
    # print(res[0][0])
    # print("〜")
    # print(datetime.fromtimestamp(res[-1][0]))
    # print(res[-1][0])
    # print(f"{size},{asset_list[-1]}")
    return str(asset_list[-1] / 100000)


def main():
    res = np.array(get_local_data()[tconf.backtest_bgn:tconf.backtest_end])
    count = len(res)
    backtest(res, count, tconf.channel_breakout_size)


def range_backtest():
    band = 10000
    arr = []
    btcrates = []
    times = []
    data = get_local_data()
    print(len(data))
    # for s in range(10, 32):
    print(int(len(data) / band))
    for s in range(1, int(len(data) / band)):
        # for s in range(1, 2):
        res = np.array(data[band * s: band * (s + 1)])
        times.append(str(datetime.fromtimestamp(res[0][0])))
        count = len(res)
        # pprint(count)
        h = int(60 * 60 / tconf.size_candle)
        # h = 1
        arr.append(list(map(lambda i: backtest(res, count, h * i), range(5, 41, 5))))
        btcrates.append(str(res[-1][4] / res[0][4]))

    print("times")
    print(",".join(times))
    print("btc")
    print(",".join(btcrates))

    print("my")
    print("\n".join(map(lambda a: ",".join(a), np.transpose(arr))))


if __name__ == "__main__":
    # main()
    range_backtest()
