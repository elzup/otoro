# from pprint import pprint

from config.config import cbs_fx_close_margin, cbs_fx_size
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

BAND = 10000
HSIZE = int(60 * 60 / tconf.size_candle)

def backtest(res, hsize, start=0, end=None, lsize = None, hmargin = 0, lmargin = 0, close_margin=0, wcheck=False):
    if end == None:
        end = len(res)

    lsize = lsize or hsize
    i = start

    myjpy = INIT_JPY
    mybtc = 0

    asset_list = [myjpy]
    position: Literal['none', 'long', 'short'] = 'none'
    out_ypb = 0
    lngs = []
    shts = []

    while i < end - 500:
        is_last = i == end - 501
        date, _, _, _, ypb, _ = res[i]
        if position == 'none':
            if buy_logic(i=i, data=res, size=hsize, margin=hmargin, wcheck=wcheck):
                mybtc = myjpy / ypb
                myjpy = 0
                position = 'long'
                lngs.append([date])
            elif sell_logic(data=res, i=i, size=lsize, margin=lmargin, wcheck=wcheck):
                position = 'short'
                out_ypb = ypb
                shts.append([date])
        elif position == 'long':
            if  is_last or sell_logic(data=res, i=i, size=lsize, margin=close_margin, avgcheck=False):
                myjpy = mybtc * ypb
                mybtc = 0
                position = 'none'
                lngs[-1].append(date)
        elif position == 'short':
            if is_last or buy_logic(i=i, data=res, size=hsize, margin=close_margin, avgcheck=False):
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
            if len(lng) == 1: continue
            plt.axvspan(to_sec(lng[0]), to_sec(lng[1]), color='blue', alpha=0.2, lw=0)
        for sht in shts:
            if len(sht) == 1: continue
            plt.axvspan(to_sec(sht[0]), to_sec(sht[1]), color='red', alpha=0.2, lw=0)

        ax2 = ax.twinx()
        ax2.plot('i', 'yen', data=df, color=cm.Set1.colors[1])
        plt.show()


        filename = f"backtestfx_{ymdformat(res[0][0])}_{ymdformat(res[-1][0])}_{hsize}_{lsize}.png"
        fig.savefig(f"img/backtestfx/{filename}")

        time.sleep(1)
        plt.close()

    return round(asset_list[-1] / INIT_JPY, 4)


def main():
    data = np.array(get_local_data())
    # data = get_price_data()
    prices = []
    print(len(data))

    for s in [31]:
    # for s in range(11, int(len(data) / BAND) + 1):
        res = np.array(data[BAND * s: BAND * (s + 1)])
        clean()
        prices.append(str(backtest(res, cbs_fx_size, close_margin=cbs_fx_close_margin)))
    print("\t".join(prices))

def range_backtest():
    btcrates = []
    times = ['']
    sizes = range(1, 61)
    # data = get_price_data()
    data = get_local_data()
    print(len(data))
    # for s in range(10, 32):
    print(int(len(data) / BAND))
    seasons = range(11, int(len(data) / BAND))

    for s in seasons:
        res = np.array(data[BAND * s: BAND * (s + 1)])
        times.append(str(datetime.fromtimestamp(res[0][0])))
        btcrates.append(str(round(res[-1][4] / res[0][4], 4)))

    print("\t".join(['time', ''] + times))
    print("\t".join(['btc', '1'] + btcrates))
    res = np.array(data)
    for size in sizes:
        ress = list(map(lambda s: str(backtest(res, size * HSIZE, start=BAND * s, end=BAND * (s + 1), close_margin=0.3)), seasons))
        print("\t".join([str(size), '1'] + ress))



def lisprint (name, arr):
    print("\t".join(map(str, [name, max(arr), min(arr), np.average(arr), np.prod(arr)])))
def multi_backtest():
    btcrates = []
    times = ['']
    sizes = range(21, 24)
    webchecks = [0]
    cmargins = [0.3]
    # data = get_price_data()
    data = np.array(get_local_data())
    print(len(data))
    # for s in range(10, 32):
    print(int(len(data) / BAND))
    seasons = range(0, int(len(data) / BAND))

    for s in seasons:
        res = np.array(data[BAND * s: BAND * (s + 1)])
        times.append(str(datetime.fromtimestamp(res[0][0])))
        btcrates.append(str(round(res[-1][4] / res[0][4], 4)))
    print("\t".join(['time'] + times))
    # print("\t".join(['btc'] + btcrates))
    print("\t".join(["size, max, min, ave, total"]))
    lisprint('btc', btcrates)

# 0.5, 10000
    for wc in webchecks:
        for cm in cmargins:
            for size in sizes:
                ress = list(map(lambda s: backtest(data, size * HSIZE, start=BAND * s, end=BAND * (s + 1), close_margin=cm, wcheck=wc), seasons))
                lisprint(f"{wc}_{cm}_{size}", ress)


    # print("\n".join(map(lambda a: "\t".join(a), arr)))

if __name__ == "__main__":
    main()
    # range_backtest()
    # multi_backtest()
