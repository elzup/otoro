# from pprint import pprint

from services.cryptowatcli import get_ohlc
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.cm as cm
import time
from datetime import datetime

from config import config as tconf
# from logic import buy_judge_channelbreakout_i as buy_logic, sell_judge_channelbreakout_i as sell_logic
from logic import buy_judge_channelbreakout_ic as buy_logic, sell_judge_channelbreakout_ic as sell_logic, clean


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

    return list(csvarr)


def get_price_data():
    return get_ohlc(period, 1000)

# --------------------------------------------------------------------
# 評価値系


def buy_signal(data, i, size):
    return buy_logic(i=i, data=data, size=size)


def sell_signal(data, i, size):
    return sell_logic(data=data, i=i, size=size)

# --------------------------------------------------------------
# ここからアルゴリズム


fee = 0.0015
# 何秒足
period = tconf.size_candle


INIT_JPY = 100000


def backtest(res, count, hsize, lsize = None, hmargin = 0, lmargin = 0):
    lsize = lsize or hsize
    i = 0

    myjpy = INIT_JPY
    mybtc = 0

    asset_list = [myjpy]
    buy_position = True

    while i < count - 500:
        while buy_position:
            asset_list.append(myjpy + mybtc * res[i][4])
            if i > count - 500:
                break

            if buy_logic(i=i, data=res, size=hsize, margin=hmargin):
                price = res[i][4]
                mybtc = myjpy / price * (1 - fee)
                myjpy = 0
                buy_position = False

            i += 1

        while not buy_position:
            asset_list.append(myjpy + mybtc * res[i][4])
            
            if sell_logic(data=res, i=i, size=lsize, margin=lmargin):
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

        filename = f"backtest_{ymdformat(res[0][0])}_{ymdformat(res[-1][0])}_{hsize}_{lsize}.png"
        fig.savefig(f"img/backtest/{filename}")

        time.sleep(1)
        plt.close()

    return str(round(asset_list[-1] / INIT_JPY, 4))
    # return str(asset_list[-1] / INIT_JPY)


def main():
    res = np.array(get_local_data()[tconf.backtest_bgn:tconf.backtest_end])
    count = len(res)
    backtest(res, count, tconf.cbs_size)




def range_backtest():
    band = 10000
    arr = []
    btcrates = []
    times = []
    data = get_local_data()
    ranges = [39]

    print(len(data))
    # for s in range(10, 32):
    print(int(len(data) / band))
    # for s in range(10, 11):
    for s in range(10, int(len(data) / band)):
        res = np.array(data[band * s: band * (s + 1)])
        times.append(str(datetime.fromtimestamp(res[0][0])))
        count = len(res)
        h = int(60 * 60 / tconf.size_candle)
        clean()
        arr.append(list(map(lambda i: backtest(res, count, 38 * h, 36 * h), ranges)))
        btcrates.append(str(res[-1][4] / res[0][4]))

    print("times")
    print("\t".join(times))
    print("btc")
    print("\t".join(btcrates))

    print("my")
    print("\n".join(map(lambda a: "\t".join(a), np.transpose(arr))))


def range_hl_backtest():
    arr = []
    btcrates = []
    data = get_local_data()
    ranges = list(range(30, 51))
    print("\t".join(['low/high'] + list(map(str,  ranges))))

    res = np.array(data[110000:])
    for l in ranges:
        count = len(res)
        h = int(60 * 60 / tconf.size_candle)
        arr.append([str(l)] + list(map(lambda i: backtest(res, count, h * i, h * l), ranges)))
        btcrates.append(str(res[-1][4] / res[0][4]))

    print("btc\t" + "\t".join(btcrates))
    print("\n".join(map(lambda a: "\t".join(a), arr)))

def range_hl_margin_backtest():
    arr = []
    btcrates = []
    data = get_local_data()
    margins = list(map(lambda i: i * 0.5, range(-5, 5)))
    ranges = list(range(35, 45))
    # print("\t".join(['lm/hm'] + list(map(str,  margins))))
    print("\t".join(['ls\\hs'] + list(map(str,  ranges))))

    band = 100000
    term = 1
    res = np.array(data[100000:])
    print(str(datetime.fromtimestamp(res[0][0])))
    # res = np.array(data[110000:])
    count = len(res)
    print("btc\t" + str(res[-1][4] / res[0][4]))
    # for lm in margins:
    for lsize in ranges:
        h = int(60 * 60 / tconf.size_candle)
        arr.append([str(lsize)] + list(map(lambda hsize: backtest(res, count, hsize * h, lsize * h, -0.05, -0.05), ranges)))
        # arr.append([str(lm)] + list(map(lambda hm: backtest(res, count, 38 * h, 36 * h, lm, hm), margins)))
        btcrates.append(str(res[-1][4] / res[0][4]))
        print("\t".join(arr[-1]))

    # print("\n".join(map(lambda a: "\t".join(a), arr)))


if __name__ == "__main__":
    # main()
    # range_backtest()
    # range_hl_backtest()
    range_hl_margin_backtest()
