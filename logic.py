from datetime import datetime
from logger import log

from config import config as tconf
from services.cryptowatcli import get_ohlc

I_BGN = 1
I_MAX = 2
I_MIN = 3
I_END = 4


class ExecLogic:

    def buy_judge(self, size=tconf.channel_breakout_size):
        if tconf.cycle_debug: return True
        data, _ = get_ohlc(tconf.size_candle, size)
        return buy_judge_channelbreakout(data)

    def sell_judge(self, size=tconf.channel_breakout_size):
        if tconf.cycle_debug: return True
        data, _ = get_ohlc(tconf.size_candle, size)

        return sell_judge_channelbreakout(data)




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
def dmax(a, b, data):
    if (a, b) in cmax: return cmax[a, b]
    if (a, b - 1) in cmax:
        cmax[a, b] = max(cmax[a, b - 1], data[b - 1, I_MAX])
    else:
        cmax[a, b] = max(data[a:b, I_MAX])
    return cmax[a, b]

cmin = {}
def dmin(a, b, data):
    if (a, b) in cmin: return cmin[a, b]
    if (a, b - 1) in cmin:
        cmin[a, b] = min(cmin[a, b - 1], data[b - 1, I_MIN])
    else:
        cmin[a, b] = min(data[a:b, I_MIN])
    return cmin[a, b]

def clean():
    global cmax, cmin
    cmax = {}
    cmin = {}


def buy_judge_channelbreakout_ic(i, size, data, margin=0):
    si = i - size + 1
    if si < 0: return

    hv = dmax(si, i + 1, data)
    lv = dmin(si, i + 1, data)
    v = data[i, I_MAX]
    d = (hv - lv)
    tv = v - lv
    return (1 - margin) <= tv / d

def sell_judge_channelbreakout_ic(i, size, data, margin=0):
    si = i - size + 1
    if si < 0: return

    hv = dmax(si, i + 1, data)
    lv = dmin(si, i + 1, data)
    v = data[i, I_MIN]
    d = (hv - lv)
    tv = v - lv
    return margin >= tv / d <= margin


def buy_judge_channelbreakout(data):
    hv = max(data[:, I_MAX])
    lv = min(data[:, I_MIN])
    v = data[-1, I_MAX]
    exec_log("b", hv, lv, v)
    return hv <= v


def sell_judge_channelbreakout(data):
    hv = max(data[:, I_MAX])
    lv = min(data[:, I_MIN])
    v = data[-1, I_MIN]
    exec_log("b", hv, lv, v)
    return lv >= v
