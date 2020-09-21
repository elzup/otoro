# from pprint import pprint

from services.cryptowatcli import get_ohlc
import time
from datetime import datetime
from typing import List, Literal, Tuple
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

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("-m", "--market", type=str,
                    default='bitflyer', help="market name")
parser.add_argument("-p", "--pair", type=str,
                    default='btcfxjpy', help="pair name")
parser.add_argument("-r", "--realtime", action="store_true",
                    help="get data from cryptowat")
parser.add_argument("-c", "--candle", type=int, help="candle size",
                    default=tconf.size_candle)
parser.add_argument("-s", "--snake-size", type=float, help="snake size",
                    default=tconf.snake_size)
args = parser.parse_args()

candle = args.candle
# candle = tconf.size_candle
market = args.market
pair = args.pair
use_recent = args.realtime
snake_size = args.snake_size

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


def get_recent_data():
    print(market, pair)
    data, _ = get_ohlc(candle, 100000, market, pair)
    return data


def ymdformat(dt):
    return datetime.fromtimestamp(dt).strftime("%Y-%m-%d")


INIT_JPY = 100000
# comm = 0.0015
DAY_COMM = 1 - 0.0004
DAY_STEP = 12 * 24
FEE = 0

BAND = 10000
HSIZE = int(60 * 60 / tconf.size_candle)

if use_recent:
    data = np.array(get_recent_data())
else:
    data = np.array(get_local_data())
season_count = int(len(data) / BAND)


def backtest(res, size, start=0, end=None, e_margin=0, e_weight_min=0, bc_id="backtestfx_snake"):
    attack = 1
    # attack = 0.5
    # attack = 0.8
    if end == None:
        end = len(res)

    i = start

    myjpy: float = INIT_JPY
    mybtc = 0

    asset_list = [myjpy]
    position: Literal['none', 'long', 'short'] = 'none'
    sht_ypbs: List[Tuple[float, float]] = []
    lngs = [[]]
    shts = [[]]

    while i < end - 10:
        is_last = i == end - 10 - 1
        date = res[i][0]
        ypb = res[i][4]

        hi_touch, hhlw = buy_logic(
            res, size, i, withcache=True, margin=e_margin, entry_min=e_weight_min)
        lo_touch, lhlw = sell_logic(
            res, size, i, withcache=True, margin=e_margin, entry_min=e_weight_min)
        # d = hhlw[0] - hhlw[1]
        # hvp = hhlw[1] + (1 - e_margin) * d
        # lvp = hhlw[1] + e_margin * d

        if is_last or position == 'long' and lo_touch:
            # myjpy += mybtc * lvp
            myjpy += mybtc * ypb
            mybtc = 0
            position = 'none'
            lngs[-1].append(date)
            lngs.append([])
        if is_last or position == 'short' and hi_touch:
            # myjpy += sum(map(lambda pa: pa[1] * pa[0] / hvp, sht_ypbs))
            myjpy += sum(map(lambda pa: pa[1] * pa[0] / ypb, sht_ypbs))
            sht_ypbs = []
            position = 'none'
            shts[-1].append(date)
            shts.append([])
        elif hi_touch:
            pay = myjpy * attack
            myjpy -= pay
            # amount = pay / hvp * (1 - FEE)
            amount = pay / ypb * (1 - FEE)
            mybtc += amount
            position = 'long'
            lngs[-1].append(date)
        elif lo_touch:
            pay = myjpy * attack
            myjpy -= pay
            position = 'short'
            # sht_ypbs.append((lvp, pay * (1 - FEE)))
            sht_ypbs.append((ypb, pay * (1 - FEE)))
            shts[-1].append(date)

        if position == 'short':
            asset_list.append(
                myjpy + sum(map(lambda pa: pa[1] * pa[0] / ypb, sht_ypbs)))
        else:
            asset_list.append(myjpy + mybtc * ypb)

        i += 1
        if i % DAY_STEP == 0:
            sht_ypbs = list(map(lambda v: (v[0] * DAY_COMM, v[1]), sht_ypbs))
            # sht_ypbs *= DAY_COMM
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
            if len(lng) < 2: continue
            plt.axvspan(to_sec(lng[0]), to_sec(lng[-1]),
                        color='blue', alpha=0.2, lw=0)
        for sht in shts:
            if len(sht) < 2: continue
            plt.axvspan(to_sec(sht[0]), to_sec(sht[-1]),
                        color='red', alpha=0.2, lw=0)

        ax2 = ax.twinx()
        ax2.plot('i', 'yen', data=df, color=cm.Set1.colors[1])
        if tconf.plotshow:
            plt.show()

        if tconf.plot:
            # filename = f"backtestfx_{ymdformat(res[0][0])}_{ymdformat(res[-1][0])}_{hsize}_{lsize}.png"
            filename = f"{bc_id}_{size/1000}k_em{e_margin}_{ymdformat(res[0][0])}_{ymdformat(res[-1][0])}.png"
            fig.savefig(f"img/backtestfx_tmp/{filename}")
            time.sleep(1)

        plt.close()

    return round(asset_list[-1] / INIT_JPY, 4)


def main():
    prices = [snake_size, 1.0]
    btcs = ['btc', 1]
    times = ["time", ""]

    # for s in [14]:
    for s in range(season_count + 1):
        # for s in range(11, season_count + 1):
        # for s in [0]:
        # for s in range(season_count - 10, season_count + 1):
        res = np.array(data[BAND * s: BAND * (s + 1)])
        times.append(str(datetime.fromtimestamp(res[0][0])))
        btcs.append(str(round(res[-1][4] / res[0][4], 4)))
        clean()
        prices.append(backtest(
            res,
            snake_size,
            e_margin=tconf.snake_entry_margin,
            e_weight_min=tconf.snake_entry_min
        ))
        # prices.append(str(round((res[-1][1] + res[0][1]) / 2, 4)))
    print("\t".join(times))
    # print("\t".join(prices))
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
    margins = [0.3]
    # margins = [0, 0.1, 0.2, 0.3]
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
    for mrg in margins:
        # print(f"emg: {em}, cmg: {cm}")
        # clean_snake()
        for size in sizes:
            ress = list(map(lambda s:
                            backtest(data, size, start=BAND * s, end=BAND * (s + 1), e_margin=mrg), seasons))
            # print(f"emg: {em}, cmg: {cm} {size}" + "\t".join(map(str, ress)))
            lisprint(f"mrg: {mrg} {size}", ress)
    # print(
        # "\n".join(map(lambda v: f"{v[0]}\t{v[1]}", print_snake_cache().items())))


if __name__ == "__main__":
    main()
    # multi_backtest()
