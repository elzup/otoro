import time
from typing import Literal
from util import next_sleep

from config import config as tconf
from logic import SnakeLogic
from services.slackcli import (
    close_notice, error_notice, long_entry_notice, short_entry_notice, start_notice)
# from pprint import pprint
from trade_method_old import TradeMethod

# 実行クラス
trader = TradeMethod("FX_BTC_JPY")
logic = SnakeLogic(tconf.snake_size, market='bitflyer', pair="btcfxjpy")


class TradeController:
    def __init__(self):
        self.posi: Literal["none", "shor", "long"] = "none"
        trader.wait_ordarable()

        self.posi = trader.get_position()
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
            time.sleep(next_sleep())

    def none_step(self):
        # データを取得して買い判定か調べる
        if logic.entry_long_judge():
            amount, price = trader.entry_full_long()
            long_entry_notice(price, amount)
            self.posi = 'long'
        elif logic.entry_short_judge():
            amount, price = trader.entry_full_short()
            short_entry_notice(price, amount)
            self.posi = 'shor'

    def long_step(self):
        if not logic.close_long_judge(): return
        amount, price = trader.close_full_long()
        print(price, amount)
        close_notice(price, amount)
        self.posi = 'none'

    def shor_step(self):
        if not logic.close_short_judge(): return
        amount, price = trader.close_full_short()
        print(price, amount)
        close_notice(price, amount)
        self.posi = 'none'


def main():
    tc = TradeController()
    start_notice()
    tc.run()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        error_notice(str(e))
