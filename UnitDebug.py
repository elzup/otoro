

# from pprint import pprint
from TradeMethod import TradeMethod
from services.cryptowatcli import get_ohlc

trader = TradeMethod()


def tradingcommission():
    comm_res = trader.wrap.get_my_tradingcommission()
    print(comm_res)


def load_cryptowat():
    res = get_ohlc(5 * 60, 10)
    print(res)


if __name__ == "__main__":
    # tradingcommission()
    load_cryptowat()
