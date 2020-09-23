import time
from typing import Literal

from api_binance import BinanceWrapperAPI
from logic import SnakeLogic
from services.slackcli import SlackNoticeClient
# from pprint import pprint
from trade_method import TradeMethod
from util import next_sleep


class TradeController:
    def __init__(self, pair: str, cur_symbol: str, tar_symbol: str, precision: int, leverage: int, size_candle: int, snake_size: int, market: str):
        wrapper = BinanceWrapperAPI(pair.upper(), tar_symbol.upper(), precision)
        self.precision = precision
        self.slackcli = SlackNoticeClient(cur_symbol, tar_symbol)
        self.slackcli.start_notice()
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
            self.slackcli.long_entry_notice(
                price, amount, round(price * amount, self.precision))
            self.posi = 'long'
        elif self.logic.entry_short_judge():
            amount, price = self.trader.entry_full_short()
            self.slackcli.short_entry_notice(
                price, amount, round(price * amount, self.precision))
            self.posi = 'shor'

    def long_step(self):
        if not self.logic.close_long_judge(): return
        amount, price = self.trader.close_full_long()
        print(price, amount)
        self.slackcli.close_notice(
            price, amount, round(price * amount, self.precision))
        self.posi = 'none'

    def shor_step(self):
        if not self.logic.close_short_judge(): return
        amount, price = self.trader.close_full_short()
        print(price, amount)
        self.slackcli.close_notice(
            price, amount, round(price * amount, self.precision))
        self.posi = 'none'
