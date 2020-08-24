import time

# from pprint import pprint
from TradeMethod import TradeMethod
from services.cryptowatcli import get_ohlc

trader = TradeMethod()


def tradingcommission():
    comm_res = trader.wrap.get_my_tradingcommission()
    print(comm_res)

# https://docs.cryptowat.ch/rest-api/rate-limit
# CPU 4sec/hour/IP
#  170(more) times


def load_cryptowat_large():
    i = 0
    while i < 1000:
        time.sleep(1)
        get_ohlc(300, 1)
        i += 1
        print(i)


def load_cryptowat_short():
    i = 0
    while i < 1000:
        time.sleep(1)
        get_ohlc(300, 1)
        i += 1
        print(i)


def load_cryptowat():
    for _ in range(10):
        time.sleep(0.5)
        res = get_ohlc(300, 1)
        print(res)
        print(len(res))


if __name__ == "__main__":
    # tradingcommission()
    load_cryptowat()
