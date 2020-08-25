from datetime import datetime

from config import config as tconf
from services.cryptowatcli import get_ohlc


class ExecLogic:

    def buy_judge(self, i=0, data=None, size=tconf.channel_breakout_size):
        if data is None:
            data = get_ohlc(tconf.size_candle, size)
            size = len(data)
            i = size - 1
        if i < size - 1 or size == 0:
            return False
        return buy_judge_channelbreakout(i=i, data=data, size=size)

    def sell_judge(self, i=0, data=None, size=tconf.channel_breakout_size):
        if data is None:
            data = get_ohlc(tconf.size_candle, size)
            size = len(data)
            i = size - 1
        if i < size - 1 or size == 0:
            return False

        return sell_judge_channelbreakout(i=i, data=data, size=size)


def __buy_judge_candle(self, i, data):
    min_datasize = 3
    if i < min_datasize:
        return False
    d0 = data[i - 2][1] - data[i - 2][4]
    d1 = data[i - 1][1] - data[i - 1][4]
    d2 = data[i][1] - data[i][4]

    limit = tconf.buy_judge_limit

    if ((d0 > 0) and (d1 > 0) and (d2 > 0)) and (d0 / d2 > limit and d1 / d2 > limit):
        # print(datetime.fromtimestamp(data[i][0]))
        return True
    else:
        return False


def __buy_judge_goldencross(self, i, data):
    min_datasize = 11
    if i < min_datasize:
        return False

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
    print(f"{pos} {timestamp()}{fstr(max_v)}{fstr(min_v)}{fstr(current)}")


def sell_judge_channelbreakout(i, size, data):
    if tconf.cycle_debug:
        return True
    max_v = max(data[i - size + 1:i, 2])
    min_v = min(data[i - size + 1:i, 3])
    if tconf.logic_print:
        exec_log("s", max_v, min_v, data[i][2])
    return max_v != min_v and min_v >= data[i][3]


def buy_judge_channelbreakout(i, size, data=None):
    if tconf.cycle_debug:
        return True
    max_v = max(data[i - size + 1:i, 2])
    min_v = min(data[i - size + 1:i, 3])

    if tconf.logic_print:
        exec_log("b", max_v, min_v, data[i][3])
    return max_v != min_v and max_v <= data[i][2]
