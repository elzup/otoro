# from pprint import pprint

from services.cryptowatcli import get_ohlc
import numpy as np
import pandas as pd
import requests
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.cm as cm
import time
from datetime import datetime

from config import config as tconf
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
    return get_ohlc(period, 1000)

# --------------------------------------------------------------------
# 評価値系


def buy_signal(response, i, size):
    ex = ExecLogic()
    return ex.buy_judge(data=response, i=i, size=size)


def sell_signal(response, i, size):
    ex = ExecLogic()
    return ex.sell_judge(data=response, i=i, size=size)

# --------------------------------------------------------------
# ここからアルゴリズム


fee = 0.0015
# 何秒足
period = tconf.size_candle


INIT_JPY = 100000


def backtest(res, count, size):
    # return str(size)
    i = 0
    # profit = loss = count1 = count2 = 0

    myjpy = INIT_JPY
    mybtc = 0

    asset_list = [myjpy]
    buy_position = True

    while i < count - 500:
        while buy_position:
            asset_list.append(myjpy + mybtc * res[i][4])
            if i > count - 500:
                break

            if buy_signal(res, i, size):
                price = res[i][4]
                mybtc = myjpy / price * (1 - fee)
                myjpy = 0
                buy_position = False

            i += 1

        while not buy_position:
            asset_list.append(myjpy + mybtc * res[i][4])
            if sell_signal(res, i, size):
                myjpy = mybtc * res[i][4] * (1 - fee)
                mybtc = 0
                buy_position = True

            i += 1
            if i > count - 500:
                asset_list.append(myjpy + mybtc * res[i][4])
                break

    if tconf.plot:
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

    return str(asset_list[-1] / INIT_JPY)


def main():
    res = np.array(get_local_data()[tconf.backtest_bgn:tconf.backtest_end])
    count = len(res)
    backtest(res, count, tconf.channel_breakout_size)


ranges = [39]


def range_backtest():
    band = 10000
    arr = []
    btcrates = []
    times = []
    data = get_local_data()

    print(len(data))
    # for s in range(10, 32):
    print(int(len(data) / band))
    for s in range(10, 11):
        # for s in range(10, int(len(data) / band)):
        res = np.array(data[band * s: band * (s + 1)])
        times.append(str(datetime.fromtimestamp(res[0][0])))
        count = len(res)
        # pprint(count)
        h = int(60 * 60 / tconf.size_candle)
        # h = 1
        arr.append(list(map(lambda i: backtest(res, count, h * i), ranges)))
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
