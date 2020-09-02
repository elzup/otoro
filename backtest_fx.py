# from pprint import pprint

from services.cryptowatcli import get_ohlc
import time
from datetime import datetime
from typing import Literal

import matplotlib.cm as cm
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from config import config as tconf
from logic import buy_judge_channelbreakout_ic as buy_logic
from logic import clean
from logic import sell_judge_channelbreakout_ic as sell_logic

# output_file_name = "./data/btcjpn_2017_2020_5m_full.csv"
output_file_name = "./data/btcjpn_2015_2020_5m_cc.csv"
to_sec = lambda v: pd.to_datetime(v, unit="s")

def parse_csv_line(line):
    return list(map(float, line.split(",")))

def get_local_data():
    f = open(output_file_name)
    txt = f.read()
    f.close()
    csvarr = list(map(parse_csv_line, txt.strip().split("\n")))

    return list(csvarr)

def get_price_data():
    data, _ = get_ohlc(tconf.size_candle, 1000)
    return data



def ymdformat(dt):
    return datetime.fromtimestamp(dt).strftime("%Y-%m-%d")



INIT_JPY = 100000
# comm = 0.0015
DAY_COMM = 1 - 0.0004
DAY_STEP = 12 * 24

def backtest(res, count, hsize, lsize = None, hmargin = 0, lmargin = 0):
    count = len(res)
    lsize = lsize or hsize
    i = 0

    myjpy = INIT_JPY
    mybtc = 0

    asset_list = [myjpy]
    position: Literal['none', 'long', 'short'] = 'none'
    out_ypb = 0
    lngs = []
    shts = []

    while i < count - 500:
        is_last = i == count - 501
        date, _, _, _, ypb, _ = res[i]
        if position == 'none':
            if buy_logic(i=i, data=res, size=hsize, margin=0):
                mybtc = myjpy / ypb
                myjpy = 0
                position = 'long'
                lngs.append([date])
            elif sell_logic(data=res, i=i, size=lsize, margin=0):
                position = 'short'
                out_ypb = ypb
                shts.append([date])
        elif position == 'long':
            if  is_last or sell_logic(data=res, i=i, size=lsize, margin=0.75):
                myjpy = mybtc * ypb
                mybtc = 0
                position = 'none'
                lngs[-1].append(date)
        elif position == 'short':
            if is_last or buy_logic(i=i, data=res, size=hsize, margin=0.75):
                myjpy = myjpy * out_ypb / ypb
                out_ypb = 0
                position = 'none'
                shts[-1].append(date)
    
        if position == 'short':
            asset_list.append((myjpy * out_ypb / ypb))
        else:
            asset_list.append(myjpy + mybtc * ypb)

        i += 1
        if i % DAY_STEP == 0:
            out_ypb *= DAY_COMM
            mybtc *= DAY_COMM

    if tconf.plot:
        x = np.array(list(map(lambda v: to_sec(v[0]), res[:len(asset_list)])))
        btc = np.array(list(map(lambda v: v[4], res[:len(asset_list)])))
        yen = np.array(asset_list)
        df = pd.DataFrame({'i': x, 'btc': btc, 'yen': yen})
        fig, ax = plt.subplots()
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        ax.plot('i', 'btc', data=df, color=cm.Set1.colors[0])
        for lng in lngs:
            plt.axvspan(to_sec(lng[0]), to_sec(lng[1]), color='blue', alpha=0.2, lw=0)
        for sht in shts:
            plt.axvspan(to_sec(sht[0]), to_sec(sht[1]), color='red', alpha=0.2, lw=0)

        ax2 = ax.twinx()
        ax2.plot('i', 'yen', data=df, color=cm.Set1.colors[1])
        plt.show()


        filename = f"backtestfx_{ymdformat(res[0][0])}_{ymdformat(res[-1][0])}_{hsize}_{lsize}.png"
        fig.savefig(f"img/backtestfx/{filename}")

        time.sleep(1)
        plt.close()

    return str(round(asset_list[-1] / INIT_JPY, 4))


def main():
    data = np.array(get_local_data())
    # data = get_price_data()
    band = 10000
    prices = []
    print(len(data))

    for s in [22]:
    # for s in range(0, int(len(data) / band) + 1):
        res = np.array(data[band * s: band * (s + 1)])
        count = len(res)
        clean()
        prices.append(backtest(res, count, tconf.channel_breakout_size_fx))
    print("\t".join(prices))

def range_backtest():
    band = 10000
    arr = []
    btcrates = []
    times = []
    sizes = range(6, 24)
    # data = get_price_data()
    data = get_local_data()
    print(len(data))
    # for s in range(10, 32):
    print(int(len(data) / band))
    arr.append(list(map(str,  sizes)))

    for s in range(11, int(len(data) / band)):
        # for s in range(1, 2):
        res = np.array(data[band * s: band * (s + 1)])
        times.append(str(datetime.fromtimestamp(res[0][0])))
        count = len(res)
        # pprint(count)
        h = int(60 * 60 / tconf.size_candle)
        # h = 1
        clean()
        # arr.append(list(map(lambda i: str(i), sizes)))
        arr.append(list(map(lambda i: backtest(res, count, i), sizes)))
        btcrates.append(str(round(res[-1][4] / res[0][4], 4)))
        

    print("\t".join(['time'] + times))
    print("\t".join(['btc'] + btcrates))

    print("\n".join(map(lambda a: "\t".join(a), np.transpose(arr))))
    # print("\n".join(map(lambda a: "\t".join(a), arr)))


if __name__ == "__main__":
    main()
    # range_backtest()
