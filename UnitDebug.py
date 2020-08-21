
# from pprint import pprint
from TradeMethod import TradeMethod

trader = TradeMethod()


def tradingcommission():
    comm_res = trader.wrap.get_my_tradingcommission()
    print(comm_res)


if __name__ == "__main__":
    tradingcommission()
