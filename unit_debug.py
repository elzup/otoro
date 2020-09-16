from api import WrapperAPI
from _api_ftx import FtxWrapperAPI
from api_binance import BinanceWrapperAPI
from services.slackcli import close_notice, long_entry_notice, short_entry_notice
import time
import json
import os
from config import config as tconf


# from pprint import pprint
from trade_method import TradeMethod
from services.cryptowatcli import get_ohlc


def tradingcommission():
    trader = TradeMethod()
    comm_res = trader.wrap.get_my_tradingcommission()
    print(comm_res)


def slack_notice():
    long_entry_notice(1234560, 1.555552313)
    short_entry_notice(1234560, 1.555552313)
    close_notice(1234560, 1.555552313)

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


def get_amount_fx():
    trader = TradeMethod('FX_BTC_JPY')
    amount, _ = trader.calc_entry_amount_price()
    result = trader.buy_signal(amount, 0, True)
    while not trader.is_completed(result[1]):
        print('.', end="")
        time.sleep(1)
    print(trader.calc_close_amount_price())
    # result = trader.sell_signal(0.01, 0, True)


def full_long():
    trader = TradeMethod('FX_BTC_JPY')
    trader.entry_full_long()
    trader.close_full_long()
    print(trader.calc_close_amount_price())


def full_short():
    trader = TradeMethod('FX_BTC_JPY')
    trader.entry_full_short()
    # trader.close_full_short()


def current_posision():
    trader = TradeMethod('FX_BTC_JPY')
    print(trader.get_position())


def check_trade():
    trader = TradeMethod('FX_BTC_JPY')
    trade_id = 'JRF20200908-082627-088433'
    print(trader.is_completed(trade_id))


def ftx_order():
    api = FtxWrapperAPI("YFI/USD")
    print(api.get_my_balance())
    size = api.buy_amount()
    usd = api.get_my_usd()['free']
    print(usd)
    print(size)
    amount = usd / size
    print(amount)
    # res = api.post_order_market('buy', amount, "YFI/USD")
    # print(res)


def bf_balance():
    api = WrapperAPI('FX_BTC_JPY')
    balances = api.get_my_balance()
    print(balances)


def bn_order():
    api = BinanceWrapperAPI('YFIUSDT')
    # orders = api.get_open_orders()
    # print(orders)

    print(api.get_my_balance_coin('YFI'))
    main = api.get_my_balance_coin('USDT')
    print(main)
    price = api.get_ask()
    print(price)

    size = main / price
    print(size)
    # res = api.post_order_market("BUY", size)
    # print(res)


if __name__ == "__main__":
    # tradingcommission()
    # load_cryptowat()
    # load_cryptowat_lostcheck()
    # order_wait()
    # order_fx()
    # get_amount_fx()
    # full_long()
    # full_short()
    # current_posision()
    # check_trade()
    # slack_notice()
    # ftx_order()
    # bf_balance()
    bn_order()
    pass
