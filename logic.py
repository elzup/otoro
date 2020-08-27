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


def __buy_judge_candle(self, i, data):
    min_datasize = 3
    if i < min_datasize: return False
    d0 = data[i - 2][1] - data[i - 2][4]
    d1 = data[i - 1][1] - data[i - 1][4]
    d2 = data[i][1] - data[i][4]

    limit = tconf.buy_judge_limit

    return ((d0 > 0) and (d1 > 0) and (d2 > 0)) and (d0 / d2 > limit and d1 / d2 > limit)


def __buy_judge_goldencross(self, i, data):
    min_datasize = 11
    if i < min_datasize: return False

    sm_now = sm_post = wm_now = wm_post = 0  # sm means simplemean and wm means weightmean
    sum0 = 0
    for j in range(min_datasize - 1):
        sm_now += data[i - j][4]
        sm_post += data[i - j - 1][4]
        wm_now += data[i - j][4] * (min_datasize - 1 - j)
        wm_post += data[i - j - 1][4] * (min_datasize - 1 - j)
        sum0 += min_datasize - 1 - j

    sm_now /= min_datasize - 1
    sm_post /= min_datasize - 1

    wm_now /= sum0
    wm_post /= sum0

    return sm_post > wm_post and sm_now < wm_now and sm_now < sm_post


def fstr(n):
    return str(int(n)).rjust(8, ' ')


def timestamp():
    return datetime.now().strftime('%m%d_%H%M')


def exec_log(pos, max_v, min_v, current):
    log(f"{pos} {timestamp()}{fstr(max_v)}{fstr(min_v)}{fstr(current)}")


def buy_judge_channelbreakout_i(i, size, data):
    si = i - size + 1
    return si >= 0 and buy_judge_channelbreakout(data[si:i + 1])


def sell_judge_channelbreakout_i(i, size, data):
    si = i - size + 1
    return si >= 0 and sell_judge_channelbreakout(data[si:i + 1])


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
