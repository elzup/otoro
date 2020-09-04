from datetime import datetime
from logger import log

from config import config as tconf
from services.cryptowatcli import get_ohlc
import numpy as np

I_BGN = 1
I_MAX = 2
I_MIN = 3
I_END = 4


class ExecLogic:

    def buy_judge(self, size=tconf.cbs_size, margin=0):
        if tconf.cycle_debug: return True
        data, _ = get_ohlc(tconf.size_candle, size)
        return buy_judge_channelbreakout(data, margin)

    def sell_judge(self, size=tconf.cbs_size, margin=0):
        if tconf.cycle_debug: return True
        data, _ = get_ohlc(tconf.size_candle, size)

        return sell_judge_channelbreakout(data, margin)

    def entry_short_judge(self, size=tconf.cbs_fx_size, margin=0):
        self.sell_judge(size, margin)

    def close_short_judge(self, size=tconf.cbs_fx_size, margin=tconf.cbs_fx_close_margin):
        self.buy_judge(size, margin)

    def entry_long_judge(self, size=tconf.cbs_fx_size, margin=0):
        self.buy_judge(size, margin)

    def close_long_judge(self, size=tconf.cbs_fx_size, margin=tconf.cbs_fx_close_margin):
        self.sell_judge(size, margin)





fstr = lambda n: str(int(n)).rjust(8, ' ')
timestamp = lambda: datetime.now().strftime('%m%d_%H%M')


def exec_log(pos, max_v, min_v, current):
    log(f"{pos} {timestamp()}{fstr(max_v)}{fstr(min_v)}{fstr(current)}")


def buy_judge_channelbreakout_i(i, size, data):
    si = i - size + 1
    return si >= 0 and buy_judge_channelbreakout(data[si:i + 1])


def sell_judge_channelbreakout_i(i, size, data):
    si = i - size + 1
    return si >= 0 and sell_judge_channelbreakout(data[si:i + 1])


cmax = {}
step = 2
def dmax(a, b, data):
    global cmax
    if (a, b) in cmax: return cmax[a, b]
    if (a, b - step) in cmax:
        cmax[a, b] = max(cmax[a, b - step], data[b - step, I_MAX])
    else:
        cmax[a, b] = max(data[a:b, I_MAX])
    return cmax[a, b]

cmin = {}
def dmin(a, b, data):
    global cmin
    if (a, b) in cmin: return cmin[a, b]
    if (a, b - step) in cmin:
        cmin[a, b] = min(cmin[a, b - step], data[b - step, I_MIN])
    else:
        cmin[a, b] = min(data[a:b, I_MIN])
    return cmin[a, b]

def clean():
    global cmax, cmin
    cmax = {}
    cmin = {}


def buy_judge_channelbreakout_ic(i, size, data, margin=0, wcheck=False, avgcheck=False):
    si = i - size + 1
    if si < 0: return
    v = data[i, I_MAX]
    avg = np.average(data[si:i])
    if avgcheck and v > avg:
        return True

    hv = dmax(si, i, data)
    lv = dmin(si, i, data)
    d = (hv - lv)
    tv = v - lv
    if wcheck and d < wcheck:
        return False
    if d == 0:
        # print("diff0: ", size, hv, lv)
        return False
    return (1 - margin) <= tv / d

def sell_judge_channelbreakout_ic(i, size, data, margin=0, wcheck=False, avgcheck=False):
    si = i - size + 1
    if si < 0: return
    v = data[i, I_MIN]
    avg = np.average(data[si:i])
    if avgcheck and avg > v:
        return True

    hv = dmax(si, i, data)
    lv = dmin(si, i, data)
    d = (hv - lv)
    tv = v - lv
    if wcheck and d < wcheck:
        return False
    if d == 0:
        # print("diff0: ", size, hv, lv)
        return False
    return tv / d <= margin


def buy_judge_channelbreakout(data, margin=0):
    hv = max(data[:-1, I_MAX])
    lv = min(data[:-1, I_MIN])
    v = data[-1, I_MAX]
    d = (hv - lv)
    tv = v - lv
    exec_log("b", hv, lv, v)
    return (1 - margin) <= tv / d


def sell_judge_channelbreakout(data, margin=0):
    hv = max(data[:-1, I_MAX])
    lv = min(data[:-1, I_MIN])
    v = data[-1, I_MIN]
    d = (hv - lv)
    tv = v - lv
    exec_log("b", hv, lv, v)
    return tv / d <= margin
