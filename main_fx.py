import time
from typing import Literal

from config import config as tconf
from logic import ExecLogic
from main import TradeController
from services.slackcli import (
    close_notice, long_entry_notice, short_entry_notice, start_notice)
# from pprint import pprint
from trade_method import TradeMethod

# 実行クラス
trader = TradeMethod("FX_BTC_JPY")
logic = ExecLogic()


# trader.cancel_all_orders()


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
            time.sleep(tconf.sleep_time)

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
        amount = trader.close_full_long()
        price = trader.get_board_price()
        print(price, amount)
        close_notice(price, amount)
        self.posi = 'none'

    def shor_step(self):
        if not logic.close_short_judge(): return
        amount = trader.close_full_short()
        price = trader.get_board_price()
        print(price, amount)
        close_notice(price, amount)
        self.posi = 'none'


def main():
    tc = TradeController()
    start_notice()
    tc.run()


if __name__ == "__main__":
    main()
