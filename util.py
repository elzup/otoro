from backtest import tconf
import time


def next_sleep(step_time=tconf.sleep_time):
    return (step_time - time.time() % step_time) + 10


def find(func, arr):
    rs = list(filter(func, arr))
    if len(rs) == 0: return None
    return rs[0]
