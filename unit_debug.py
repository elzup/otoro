import time
import os
from config import config as tconf


# from pprint import pprint
from trade_method import TradeMethod
from services.cryptowatcli import get_ohlc


def tradingcommission():
    trader = TradeMethod()
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
        res, _ = get_ohlc(300, 1)
        print(res)
        print(len(res))


def load_cryptowat_lostcheck():
    i = 0
    s = ""
    t = 0
    while True:
        res, allo = get_ohlc(300, 1)
        # res = "1"
        t += 1 if len(res) == 1 else 0
        i += 1
        os.system('clear')
        if i % 10 == 0:
            s += "A" if t == 10 else str(t)
            t = 0
            if i % 200 == 0:
                s += "\n"
        print(s + str(t))
        rema = allo["remaining"]
        print(f"{rema}/4000000000")
        time.sleep(10)


def get_orders():
    trader = TradeMethod()
    orders = trader.get_open_order()
    print(orders)


def order_wait():
    trader = TradeMethod()
    # trader.buy_signal(0.001, True)
    orders = trader.get_open_order()
    print(orders)


def order_fx():
    trader = TradeMethod('FX_BTC_JPY')
    fee = trader.wrap.get_my_tradingcommission()
    print(fee)
    assert(fee == 0)

    # permissions  = trader.wrap.get_my_permissions()
    # print(permissions)
    collateral = trader.wrap.get_my_collateral()
    positions = trader.wrap.get_my_positions()
    print(collateral)
    print(positions)

    print(trader.get_position())
    result = trader.sell_signal(0.01, 0, True)
    while not trader.is_completed(result[1]):
        print('.', end="")
        time.sleep(1)
    print()
    print(trader.get_position())

    collateral = trader.wrap.get_my_collateral()
    positions = trader.wrap.get_my_positions()
    print(collateral)
    print(positions)

    result = trader.buy_signal(0.01, 0, True)
    while not trader.is_completed(result[1]):
        print('.', end="")
        time.sleep(1)
    print(trader.get_position())
    print(result)


if __name__ == "__main__":
    # tradingcommission()
    # load_cryptowat()
    # load_cryptowat_lostcheck()
    # order_wait()
    order_fx()
    pass
