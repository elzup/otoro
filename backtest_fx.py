# from pprint import pprint

from typing import Literal
from logger import log
import numpy as np
import pandas as pd
import requests
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.cm as cm
import time
from datetime import datetime
from logic import buy_judge_channelbreakout_ic as buy_logic, sell_judge_channelbreakout_ic as sell_logic, clean

from config import config as tconf


# output_file_name = "./data/btcjpn_2017_2020_5m_full.csv"
output_file_name = "./data/btcjpn_2015_2020_5m_cc.csv"
# -----------------------------------------------------------------
# 取引所関係のmethod


def parse_csv_line(line):
    return list(map(float, line.split(",")))

def get_local_data():
    f = open(output_file_name)
    txt = f.read()
    f.close()
    csvarr = list(map(parse_csv_line, txt.strip().split("\n")))

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


def ymdformat(dt):
    return datetime.fromtimestamp(dt).strftime("%Y-%m-%d")


# 何秒足
period = tconf.size_candle
# flag
# res = get_price_data()

INIT_JPY = 100000
# comm = 0.0015
DAY_COMM = 1 - 0.0004
DAY_STEP = 12 * 24

def backtest(res, count, hsize, lsize = None, hmargin = 0, lmargin = 0):
    lsize = lsize or hsize
    i = 0

    myjpy = INIT_JPY
    mybtc = 0

    asset_list = [myjpy]
    position: Literal['none', 'long', 'short'] = 'none'
    out_ypb = 0

    while i < count - 500:
        ypb = res[i][4]
        if position == 'none':
            if buy_logic(i=i, data=res, size=hsize, margin=hmargin):
                mybtc = myjpy / ypb
                myjpy = 0
                position = 'long'
            elif sell_logic(data=res, i=i, size=lsize, margin=lmargin):
                # TODO
                position = 'short'
                out_ypb = ypb
        elif position == 'long':
            if sell_logic(data=res, i=i, size=lsize, margin=0.5):
                myjpy = mybtc * ypb
                mybtc = 0
                position = 'none'
        elif position == 'short':
            if buy_logic(i=i, data=res, size=hsize, margin=0.5):
                myjpy = myjpy * out_ypb / ypb
                out_ypb = 0
                position = 'none'
    
        if position is 'short':
            asset_list.append((myjpy * out_ypb / ypb))
        else:
            asset_list.append(myjpy + mybtc * ypb)

        i += 1
        if i % DAY_STEP == 0:
            out_ypb *= DAY_COMM
            mybtc *= DAY_COMM

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


        filename = f"backtest_{ymdformat(res[0][0])}_{ymdformat(res[-1][0])}_{hsize}_{lsize}.png"
        fig.savefig(f"img/backtest/{filename}")

        time.sleep(1)
        plt.close()

    return str(round(asset_list[-1] / INIT_JPY, 4))


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
