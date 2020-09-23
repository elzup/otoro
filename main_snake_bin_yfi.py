from api_binance import BinanceWrapperAPI
import time
from typing import Literal
from util import next_sleep

from config import config as tconf
from logic import SnakeLogic
from services.slackcli import (
    close_notice, error_notice, long_entry_notice, short_entry_notice, start_notice)
# from pprint import pprint
from trade_method import TradeMethod


class TradeController:
    def __init__(self, pair: str, cur_symbol: str, tar_symbol: str, precision: int, leverage: int, size_candle: int, snake_size: int, market: str):
        wrapper = BinanceWrapperAPI(pair.upper(), tar_symbol.upper(), precision)
        self.trader = TradeMethod(wrapper, leverage=leverage)
        self.trader.wait_ordarable()
        self.logic = SnakeLogic(snake_size, market=market, pair=pair.lower(),
                                size_candle=size_candle)

        self.size_candle = size_candle
        self.posi: Literal["none", "shor", "long"] = self.trader.get_position()
        print("Initialize completed")

    def run(self):
        print(self.posi)
        while True:
            if self.posi == 'none':
                self.none_step()
            elif self.posi == 'long':
                self.long_step()
            elif self.posi == 'shor':
                self.shor_step()
            time.sleep(next_sleep(self.size_candle))

    def none_step(self):
        # データを取得して買い判定か調べる
        if self.logic.entry_long_judge():
            amount, price = self.trader.entry_full_long()
            long_entry_notice(price, amount)
            self.posi = 'long'
        elif self.logic.entry_short_judge():
            amount, price = self.trader.entry_full_short()
            short_entry_notice(price, amount)
            self.posi = 'shor'

    def long_step(self):
        if not self.logic.close_long_judge(): return
        amount, price = self.trader.close_full_long()
        print(price, amount)
        close_notice(price, amount)
        self.posi = 'none'

    def shor_step(self):
        if not self.logic.close_short_judge(): return
        amount, price = self.trader.close_full_short()
        print(price, amount)
        close_notice(price, amount)
        self.posi = 'none'


def main():
    tc = TradeController('TRBUSDT', 'USDT', 'TRB', 1, 2, 300, 20, 'binance')
    # tc = TradeController('TRXUSDT', 'USDT', 'TRX', 0, 2, 60, 0.004, 'binance')
    start_notice()
    tc.run()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        error_notice(str(e))
        raise e
