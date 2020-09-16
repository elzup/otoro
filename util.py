import time


def next_sleep():
    return (300 - time.time() % 300) + 10


def find(func, arr):
    rs = list(filter(func, arr))
    if len(rs) == 0: return None
    return rs[0]
