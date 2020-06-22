import time

from config import Tradeconfig
from ExecLogic import ExecLogic
from TradeMethod import TradeMethod

# フラグ設定
buy_jdg = "buy_jdg"
buy_order_check = "buy_order_check"
close_sold_check = "close_sold_check"


# 取引ペア
product_code = Tradeconfig.product_code

# 実行クラス
trader = TradeMethod()
logic = ExecLogic()

thread_flag = ""
comm = 1 - trader.wrap.get_my_tradingcommission()["commission_rate"]
trade_id = [False, ""]


r = trader.get_open_order()
if r is not None:
    trade_id[0] = True
    trade_id[1] = r["child_order_acceptance_id"]
    if r["side"] == "BUY":
        thread_flag = buy_order_check
    else:
        thread_flag = close_sold_check
else:
    trade_id[0] = False
    myJPY, myBTC = trader.get_balance()
    if myJPY["amount"] == myJPY["available"] and myBTC["amount"] == myBTC["available"]:
        if myBTC["amount"] > 0.01:
            raise Exception(
                "TradeController initialize : You have much BTCs but you dont sell them.")
        else:
            thread_flag = buy_jdg
    else:
        raise Exception(
            "TradeController initialize: There are no open order but balance does not match")

result = None


print("Initialize conpleted")
while True:
    time.sleep(Tradeconfig.sleep_time)
    # print("Running..."+thread_flag)

    if thread_flag == buy_jdg:
        # データを取得して買い判定か調べる
        if logic.buy_judge():
            amount, price = trader.calc_buy_amount_price()

            result = trader.buy_signal(amount, price, True)

            if result[0]:
                trade_id[0] = True
                trade_id[1] = result[1]
                thread_flag = buy_order_check
                trader.d_message(
                    "Send buy order\nsize: " +
                    str(amount) +
                    "\nprice: " +
                    str(price))
            else:
                trader.d_message(
                    "TradeController buy_jdg : Failed to send buy signal.")
                raise Exception(
                    "TradeController buy_jdg : Failed to send buy signal.")

    elif thread_flag == buy_order_check:
        if trade_id[0]:
            res = trader.isCompleted(trade_id[1])
            if res[0]:
                trade_id[0] = False
                if res[1] == "SELL":
                    trader.d_message(
                        "TradeController/buy_order_check : Something strange.")
                    raise Exception(
                        "TradeController/buy_order_check : Something strange.")
                elif res[1] == "BUY":
                    amount = res[3] * comm
                    price = res[2] * Tradeconfig.sell_rate

                    result = trader.sell_signal(amount, price, True)

                    if result[0]:
                        trade_id[0] = True
                        trade_id[1] = result[1]
                        thread_flag = close_sold_check
                        trader.d_message(
                            "You bought BTC successfully and sent sell order\nsize: " +
                            str(amount) +
                            "\nprice: " +
                            str(price))
                    else:
                        trader.d_message(
                            "TradeController buy_order_check : Failed to send sell signal.")
                        raise Exception(
                            "TradeController buy_order_check : Failed to send sell signal.")
        else:
            trader.d_message(
                "TradeController buy_order_check : Something strange.")
            raise Exception(
                "TradeController buy_order_check : Something strange.")

    elif thread_flag == close_sold_check:
        if trade_id[0]:
            res = trader.get_order(trade_id[1])
            if res[0] == "COMPLETED":
                trade_id[0] = False
                thread_flag = buy_jdg
                trader.d_message("You sold BTC successfully.")
                continue
            amount = res[3] * comm
            price = res[2] / Tradeconfig.sell_rate
            if trader.shouldsellall(price):
                trader.cancel_all_orders()
                result_close = trader.close_position(amount, True)
                if result_close[0]:
                    trade_id[0] = False
                    thread_flag = buy_jdg
                    trader.d_message("やばいので撤退しますた")
                else:
                    trader.d_message(
                        "!!!!!!!TradeController close_sold_check : Failed to retreat!!!!!!!!!!!.")
                    trader.d_message(
                        "!!!!!!!!!!TradeController close_sold_check : Failed to retreat!!!!!!!!!!!.")
                    trader.d_message(
                        "!!!!!!!!!TradeController close_sold_check : Failed to retreat!!!!!!!!!!!.")
                    raise Exception(
                        "TradeController close_sold_check : Failed to retreat!!!!!!!!!!!.")
        else:
            raise Exception(
                "TradeController close_sold_check : Something strange.")
