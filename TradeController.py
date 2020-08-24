import time

from config import Tradeconfig
from ExecLogic import ExecLogic
# from pprint import pprint
from TradeMethod import TradeMethod
from services.slackcli import buy_notice, sell_notice, start_notice

# フラグ設定
buy_jdg = "buy_jdg"
sell_jdg = "sell_jdg"
close_sold_check = "close_sold_check"


# 実行クラス
trader = TradeMethod()
logic = ExecLogic()

TRADE_FEE = 1 - trader.wrap.get_my_tradingcommission()

# trader.cancel_all_orders()


class TradeController:
    def __init__(self):
        self.thread_flag = buy_jdg
        self.trade_id = [False, ""]
        r = trader.get_open_order()
        if r is not None:
            self.trade_id[0] = True
            self.trade_id[1] = r["child_order_acceptance_id"]
            if r["side"] == "BUY":
                self.thread_flag = sell_jdg
            else:
                self.thread_flag = close_sold_check
        else:
            self.trade_id[0] = False
            myJPY, myBTC = trader.get_balance()
            if myJPY["amount"] == myJPY["available"] and myBTC["amount"] == myBTC["available"]:
                if myBTC["amount"] > 0.01:
                    self.thread_flag = sell_jdg
                    # raise Exception(
                    #     "TradeController initialize : You have much BTCs but you dont sell them.")
                else:
                    self.thread_flag = buy_jdg
            else:
                raise Exception(
                    "TradeController initialize: There are no open order but balance does not match")
        print("Initialize completed")

    def run(self):
        while True:
            print(self.thread_flag)

            if self.thread_flag == buy_jdg:
                self.buy_step()
            elif self.thread_flag == sell_jdg:
                self.sell_step()
            elif self.thread_flag == close_sold_check:
                self.sell_comp_step()
            time.sleep(Tradeconfig.sleep_time)

    def buy_step(self):
        # データを取得して買い判定か調べる
        if not logic.buy_judge():
            return
        amount, price = trader.calc_buy_amount_price()
        amount *= TRADE_FEE
        buy_notice(price, amount)
        result = trader.buy_signal(amount, price, True)

        if not result[0]:
            msg = "TradeController buy_jdg : Failed to send buy signal."
            trader.d_message(msg)
            raise Exception(msg)
        self.trade_id[0] = True
        self.trade_id[1] = result[1]
        self.thread_flag = sell_jdg
        trader.d_message("Send buy order\nsize: " + str(amount) + "\nprice: " + str(price))

    def sell_step(self):
        if not logic.sell_judge():
            return
        amount, price = trader.calc_sell_amount_price()
        amount *= TRADE_FEE
        sell_notice(price, amount)
        result = trader.sell_signal(amount, price, True)
        if not result[0]:
            msg = "TradeController sell_jdg : Failed to send sell signal."
            trader.d_message(msg)
            raise Exception(msg)
        self.trade_id[0] = True
        self.trade_id[1] = result[1]
        self.thread_flag = close_sold_check
        trader.d_message(
            "You bought BTC successfully and sent sell order\nsize: " +
            str(amount) +
            "\nprice: " +
            str(price))

    def sell_comp_step(self):
        if not self.trade_id[0]:
            raise Exception("TradeController close_sold_check : Something strange.")
        res = trader.get_order(self.trade_id[1])
        if res[0] == "COMPLETED":
            self.trade_id[0] = False
            self.thread_flag = buy_jdg
            trader.d_message("You sold BTC successfully.")
            return


def main():
    tc = TradeController()
    start_notice()
    tc.run()


if __name__ == "__main__":
    main()
