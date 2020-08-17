import time

from config import Tradeconfig
from ExecLogic import ExecLogic
# from pprint import pprint
from TradeMethod import TradeMethod
from slack_webhook.SlackClient import buy_notice, sell_notice, start_notice

# フラグ設定
buy_jdg = "buy_jdg"
sell_jdg = "sell_jdg"
close_sold_check = "close_sold_check"


# 取引ペア
product_code = Tradeconfig.product_code

# 実行クラス
trader = TradeMethod()
logic = ExecLogic()

thread_flag = ""
comm_res = trader.wrap.get_my_tradingcommission()
print(comm_res)
comm = 1 - comm_res["commission_rate"]
trade_id = [False, ""]
start_notice()

# trader.cancel_all_orders()

r = trader.get_open_order()
if r is not None:
    trade_id[0] = True
    trade_id[1] = r["child_order_acceptance_id"]
    if r["side"] == "BUY":
        thread_flag = sell_jdg
    else:
        thread_flag = close_sold_check
else:
    trade_id[0] = False
    myJPY, myBTC = trader.get_balance()
    if myJPY["amount"] == myJPY["available"] and myBTC["amount"] == myBTC["available"]:
        if myBTC["amount"] > 0.01:
            thread_flag = sell_jdg
            # raise Exception(
            #     "TradeController initialize : You have much BTCs but you dont sell them.")
        else:
            thread_flag = buy_jdg
    else:
        raise Exception(
            "TradeController initialize: There are no open order but balance does not match")

result = None


print("Initialize conpleted")


def buy_step():
    global thread_flag
    # データを取得して買い判定か調べる
    if not logic.buy_judge():
        return
    amount, price = trader.calc_buy_amount_price()
    buy_notice(price, amount)
    result = trader.buy_signal(amount, price, True)

    if not result[0]:
        msg = "TradeController buy_jdg : Failed to send buy signal."
        trader.d_message(msg)
        raise Exception(msg)
    trade_id[0] = True
    trade_id[1] = result[1]
    thread_flag = sell_jdg
    trader.d_message("Send buy order\nsize: " + str(amount) + "\nprice: " + str(price))


def sell_step():
    global thread_flag
    if not logic.sell_judge():
        return
    amount, price = trader.calc_sell_amount_price()
    sell_notice(price, amount)

    result = trader.sell_signal(amount, price, True)

    if not result[0]:
        msg = "TradeController sell_jdg : Failed to send sell signal."
        trader.d_message(msg)
        raise Exception(msg)
    trade_id[0] = True
    trade_id[1] = result[1]
    thread_flag = close_sold_check
    trader.d_message(
        "You bought BTC successfully and sent sell order\nsize: " +
        str(amount) +
        "\nprice: " +
        str(price))


def sell_comp_step():
    global thread_flag
    if not trade_id[0]:
        raise Exception("TradeController close_sold_check : Something strange.")
    res = trader.get_order(trade_id[1])
    if res[0] == "COMPLETED":
        trade_id[0] = False
        thread_flag = buy_jdg
        trader.d_message("You sold BTC successfully.")
        return
    amount = res[3] * comm
    price = res[2] / Tradeconfig.sell_rate
    if not trader.shouldsellall(price):
        return
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
            "!!!!!!!!TradeController close_sold_check : Failed to retreat!!!!!!!!!!!.")
        trader.d_message(
            "!!!!!!!!!TradeController close_sold_check : Failed to retreat!!!!!!!!!!!.")
        raise Exception(
            "TradeController close_sold_check : Failed to retreat!!!!!!!!!!!.")


while True:
    print(thread_flag)

    if thread_flag == buy_jdg:
        buy_step()
    elif thread_flag == sell_jdg:
        sell_step()
    elif thread_flag == close_sold_check:
        sell_comp_step()
    time.sleep(Tradeconfig.sleep_time)
