# from pprint import pprint

from config.config import cbs_fx_close_margin, cbs_fx_size
from services.cryptowatcli import get_ohlc
import time
from datetime import datetime
from typing import Literal
import sys

import matplotlib.cm as cm
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from config import config as tconf
from logic import buy_judge_snake as buy_logic, clean_snake
from logic import clean
from logic import sell_judge_snake as sell_logic

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


print(sys.argv[1])
market = sys.argv[1] if len(sys.argv) >= 1 else 'bitflyer'
pair = sys.argv[2] if len(sys.argv) >= 2 else 'btcfxjpy'


def get_recent_data():
    print(market, pair)
    data, _ = get_ohlc(tconf.size_candle, 1000, market, pair)
    return data


def ymdformat(dt):
    return datetime.fromtimestamp(dt).strftime("%Y-%m-%d")


INIT_JPY = 100000
# comm = 0.0015
DAY_COMM = 1 - 0.0004
DAY_STEP = 12 * 24

BAND = 10000
HSIZE = int(60 * 60 / tconf.size_candle)

# data = np.array(get_local_data())
data = np.array(get_recent_data())
season_count = int(len(data) / BAND)


def backtest(res, size, start=0, end=None, hmargin=0, lmargin=0, e_margin=0, c_margin=0, e_weight_min=0, bc_id="backtestfx_snake"):
    if end == None:
        end = len(res)

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
        date = res[i][0]
        ypb = res[i][4]
        if position == 'none':
            if buy_logic(res, size, i, withcache=True, margin=e_margin, entry_min=e_weight_min)[0]:
                mybtc = myjpy / ypb
                myjpy = 0
                position = 'long'
                lngs.append([date])
            elif sell_logic(res, size, i, withcache=True, margin=e_margin, entry_min=e_weight_min)[0]:
                position = 'short'
                out_ypb = ypb
                shts.append([date])
        elif position == 'long':
            if is_last or sell_logic(res, size, i, margin=c_margin, withcache=True)[0]:
                myjpy = mybtc * ypb
                mybtc = 0
                position = 'none'
                lngs[-1].append(date)
        elif position == 'short':
            if is_last or buy_logic(res, size, i, margin=c_margin, withcache=True)[0]:
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

    if tconf.plot or tconf.plotshow:
        x = np.array(
            list(map(lambda v: to_sec(v[0]), res[start:start + len(asset_list)])))
        btc = np.array(
            list(map(lambda v: v[4], res[start:start + len(asset_list)])))
        yen = np.array(asset_list)
        df = pd.DataFrame({'i': x, 'btc': btc, 'yen': yen})
        fig, ax = plt.subplots(figsize=(14, 6))
        # fig, ax = plt.subplots(figsize=(30, 20))
        plt.subplots_adjust(left=0.1, right=0.95, bottom=0.1, top=0.95)

        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        ax.plot('i', 'btc', data=df, color=cm.Set1.colors[0])
        for lng in lngs:
            if len(lng) == 1: continue
            plt.axvspan(to_sec(lng[0]), to_sec(lng[1]),
                        color='blue', alpha=0.2, lw=0)
        for sht in shts:
            if len(sht) == 1: continue
            plt.axvspan(to_sec(sht[0]), to_sec(sht[1]),
                        color='red', alpha=0.2, lw=0)

        ax2 = ax.twinx()
        ax2.plot('i', 'yen', data=df, color=cm.Set1.colors[1])
        if tconf.plotshow:
            plt.show()

        if tconf.plot:
            # filename = f"backtestfx_{ymdformat(res[0][0])}_{ymdformat(res[-1][0])}_{hsize}_{lsize}.png"
            filename = f"{bc_id}_{size/1000}k_cm{c_margin}_em{e_margin}_{ymdformat(res[0][0])}_{ymdformat(res[-1][0])}.png"
            fig.savefig(f"img/backtestfx_tmp/{filename}")
            time.sleep(1)

        plt.close()

    return round(asset_list[-1] / INIT_JPY, 4)


def main():
    prices = [tconf.snake_size, 1.0]
    btcs = ['btc', 1]
    times = ["time", ""]

    # for s in [14]:
    for s in range(season_count + 1):
        # for s in range(11, season_count + 1):
        # for s in range(season_count - 10, season_count + 1):
        # for s in [0]:
        res = np.array(data[BAND * s: BAND * (s + 1)])
        times.append(str(datetime.fromtimestamp(res[0][0])))
        btcs.append(str(round(res[-1][4] / res[0][4], 4)))
        clean()
        prices.append(
            backtest(res, tconf.snake_size, e_margin=tconf.snake_entry_margin, c_margin=tconf.snake_close_margin, e_weight_min=tconf.snake_entry_min))
    print("\t".join(times))
    print("\t".join(map(str, btcs)))
    print("\t".join(map(str, prices)))


def lisprint(name, arr):
    format = lambda v: v if isinstance(v, str) else str(round(float(v), 4))
    print("\t".join(
        map(format, [name, max(arr), min(arr), np.average(arr), np.prod(arr)])))


def multi_backtest():
    btcrates = []
    times = ['']
    sizes = [30000]
    # sizes = range(50000, 300000 + 1, 10000)
    cmargins = [0.3]
    emargins = [0.3]
    print(len(data))
    print(season_count)
    # seasons = range(21, 25)
    seasons = [14]
    # seasons = range(0, season_count)
    # seasons = range(season_count - 10, season_count)

    for s in seasons:
        res = np.array(data[BAND * s: BAND * (s + 1)])
        times.append(str(datetime.fromtimestamp(res[0][0])))
        btcrates.append(round(res[-1][4] / res[0][4], 4))
    print("\t".join(['time'] + times))
    # print("\t".join(['btc'] + btcrates))
    print("\t".join(["size, max, min, ave, total"]))
    lisprint('btc', btcrates)
    # print(f"btc\t" + "\t".join(map(str, btcrates)))
    for em in emargins:
        for cm in cmargins:
            # print(f"emg: {em}, cmg: {cm}")
            # clean_snake()
            for size in sizes:
                ress = list(map(lambda s:
                                backtest(data, size, start=BAND * s,
                                         end=BAND * (s + 1), c_margin=cm, e_margin=em), seasons))
                # print(f"emg: {em}, cmg: {cm} {size}" + "\t".join(map(str, ress)))
                lisprint(f"emg: {em}, cmg: {cm} {size}", ress)
    # print(
        # "\n".join(map(lambda v: f"{v[0]}\t{v[1]}", print_snake_cache().items())))


if __name__ == "__main__":
    main()
    # multi_backtest()
