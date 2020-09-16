import time
from util import next_sleep

from config import config as tconf
from logic import ExecLogic
# from pprint import pprint
from trade_method_old import TradeMethod
from services.slackcli import buy_notice, sell_notice, start_notice

# フラグ設定
buy_jdg = "buy_jdg"
sell_jdg = "sell_jdg"


# 実行クラス
trader = TradeMethod()
logic = ExecLogic()


# trader.cancel_all_orders()


class TradeController:
    def __init__(self):
        self.thread_flag = buy_jdg
        self.trade_comp()
        while trader.get_open_order() is not None:
            time.sleep(5)
        r = trader.get_open_order()
        if r is not None:
            self.set_trade(r["child_order_acceptance_id"])
            if r["side"] == "BUY":
                self.thread_flag = sell_jdg
        else:
            myJPY, myBTC = trader.get_balance()
            if myJPY["amount"] == myJPY["available"] and myBTC["amount"] == myBTC["available"]:
                if myBTC["amount"] > 0.01:
                    self.thread_flag = sell_jdg
                else:
                    self.thread_flag = buy_jdg
        print("Initialize completed")

    def trade_comp(self):
        self.trade_id = [False, ""]

    def set_trade(self, id):
        self.trade_id = [True, id]

    def run(self):
        print(self.thread_flag)
        while True:
            if self.thread_flag == buy_jdg:
                self.buy_step()
            elif self.thread_flag == sell_jdg:
                self.sell_step()
            time.sleep(next_sleep())

    def buy_step(self):
        self.wait_comp()
        # データを取得して買い判定か調べる
        if not logic.buy_judge(): return
        amount, price = trader.calc_buy_amount_price()
        fee = trader.wrap.get_my_tradingcommission()
        amount *= (1 - fee)
        if tconf.cycle_debug:
            amount = 0.001
        buy_notice(price, amount)
        result = trader.buy_signal(amount, price, True)

        if not result[0]:
            m = "TradeController buy_jdg : Failed to send buy signal."
            print(m)
            raise Exception(m)
        self.set_trade(result[1])
        self.thread_flag = sell_jdg
        trader.d_message(f"Send buy order\nsize: {amount}\nprice: {price}")

    def sell_step(self):
        self.wait_comp()
        if not logic.sell_judge(): return
        amount, price = trader.calc_sell_amount_price()
        fee = trader.wrap.get_my_tradingcommission()
        amount *= (1 - fee)
        if tconf.cycle_debug:
            amount = 0.001
        sell_notice(price, amount)
        result = trader.sell_signal(amount, price, True)
        if not result[0]:
            m = "TradeController sell_jdg : Failed to send sell signal."
            trader.d_message(m)
            raise Exception(m)
        self.thread_flag = buy_jdg
        self.set_trade(result[1])
        m = f"You bought BTC successfully and sent sell order\nsize: {amount}\nprice: {price}"
        trader.d_message(m)

    def wait_comp(self):
        while self.trade_id[0]:
            time.sleep(10)
            if trader.is_completed(self.trade_id[1]):
                self.trade_comp()


def main():
    tc = TradeController()
    start_notice()
    tc.run()


if __name__ == "__main__":
    main()
