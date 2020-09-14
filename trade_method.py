import time
import math
from typing import Literal

from config import config as tconf
from api import WrapperAPI


class TradeMethod:
    def __init__(self, product_code="BTC_JPY"):
        self.wrap = WrapperAPI(product_code)

    def set_product_code(self, product_code):
        self.wrap.set_product_code(product_code)

    # possible return
    # COMPLETED, ACTIVE, CANCELED, EXPIRED, REJECTED, FAILED, UNKNOWN
    def is_completed(self, id):
        order = self.get_order(id)
        if order == None:
            return False

        return order[0] == "COMPLETED"

    def cancel_all_orders(self):
        count = 0
        while True:
            try:
                result = self.wrap.post_cancel_all_orders()
            except BaseException as e:
                print(type(e))
                print(e)
                time.sleep(tconf.check_sleep_time)
                # print("Failed to Cancel All Orders")
                count += 1
                if count > tconf.check_count:
                    m = "TradeMethod/cancel_all_orders : Failed to Cancel All Orders."
                    self.d_message(m)
                    raise Exception(m)
            else:
                if 'status' not in result or result["status"] == 200:
                    return True
                else:
                    time.sleep(tconf.check_sleep_time)
                    # print("Failed to Cancel All Orders")
                    count += 1
                    if count > tconf.check_count:
                        m = "TradeMethod/cancel_all_orders : Failed to Cancel All Orders."
                        self.d_message(m)
                        raise Exception(m)

    def __buy_signal(self, amount, price, buy_flag):
        if not buy_flag: return False, None

        result = self.wrap.post_send_childorder("MARKET", "BUY", amount)
        print("\t".join(map(str, result.values())))

        if 'status' in result and result["status"] != 200:
            return False, None

        buy_flag = False
        return True, result["child_order_acceptance_id"]

    def buy_signal(self, amount, price, buy_flag):
        count = 0
        while True:
            try:
                result = self.__buy_signal(amount, price, buy_flag)
                break
            except BaseException as e:
                print(type(e))
                print(e)
                time.sleep(tconf.buy_sleep_time)
                count += 1
                if count > tconf.buy_count:
                    m = "TradeController buy_jdg : Failed to send buy signal."
                    self.d_message(m)
                    raise Exception(m)
        return result

    def __sell_signal(self, amount, price, sell_flag):
        if not sell_flag: return False, None
        try:
            result = self.wrap.post_send_childorder("MARKET", "SELL", amount)

            print("\t".join(map(str, result.values())))
        except BaseException as e:
            print(type(e))
            print(e)
            # print("注文が失敗しました")
            return False, None

        if 'status' in result and result["status"] != 200:
            return False, None

        sell_flag = False
        return True, result["child_order_acceptance_id"]

    def sell_signal(self, amount, price, sell_flag):
        count = 0
        while True:
            try:
                result = self.__sell_signal(amount, price, sell_flag)
            except BaseException as e:
                print(type(e))
                print(e)
                time.sleep(tconf.sell_sleep_time)
                count += 1
                if count > tconf.sell_count:
                    m = "TradeMethod/sell_signal : Failed to send sell signal."
                    self.d_message(m)
                    raise Exception(m)
            else:
                return result

    def __close_position(self, amount, close_flag):
        if close_flag:
            try:
                result = self.wrap.post_send_childorder(
                    "MARKET", "SELL", None, amount)
            except BaseException as e:
                print(type(e))
                print(e)
                # print("注文が失敗しました")
                return False, None
            else:
                if result["status"] == 200:
                    close_flag = False
                    return True, result["child_order_acceptance_id"]
                else:
                    return False, None

    def close_position(self, amount, close_flag):
        count = 0
        while True:
            try:
                result = self.__close_position(amount, close_flag)
            except BaseException as e:
                print(type(e))
                print(e)
                time.sleep(tconf.close_sleep_time)
                count += 1
                if count > tconf.close_count:
                    m = "TradeMethod/close_Position : Failed to send close signal!!!!!!!!!"
                    self.d_message(m)
                    raise Exception(m)
            else:
                return result

    def check_orderable(self):
        return self.get_open_order() is None

    def safe_order(self, amount, method):
        while True:
            result = method(amount, 0, True)
            print(result)
            i = 20
            if not result[0]:
                amount *= 0.95
                time.sleep(3)
                i -= 1
                if i < 0:
                    raise Exception('limited retry count')
                continue
            time.sleep(3)
            if self.is_completed(result[1]):
                break
        return amount

    def safe_buy(self, amount):
        return self.safe_order(amount, self.buy_signal)

    def safe_sell(self, amount):
        return self.safe_order(amount, self.sell_signal)

    def entry_full_long(self):
        amount, price = self.calc_entry_amount_price()
        return self.safe_buy(amount), price

    def entry_full_short(self):
        amount, price = self.calc_entry_amount_price()
        return self.safe_sell(amount), price

    def close_full_long(self):
        amount = self.calc_close_amount_price()
        return self.safe_sell(amount)

    def close_full_short(self):
        amount = self.calc_close_amount_price()
        return self.safe_buy(amount)

    def get_open_order(self):
        query = "&child_order_state=ACTIVE"

        count = 0
        while True:
            try:
                r = self.wrap.get_my_childorders(query)
            except BaseException as e:
                print(type(e))
                print(e)
                time.sleep(tconf.check_sleep_time)
                count += 1
                if count > tconf.check_count:
                    m = "TradeMethod/get_open_order : Failed to check orders."
                    self.d_message(m)
                    raise Exception(m)
            else:
                break

        if len(r) == 0: return None
        elif len(r) == 1: return r[0]
        else:
            print(type(r))
            print(r)
            m = "TradeMethod/get_open_order: Multiple order."
            self.d_message(m)
            raise Exception(m)

    def get_position(self) -> Literal["none", "long", "shor"]:
        colsum = self.calc_close_amount_price()
        if colsum < 0.01: return 'none'
        col = self.wrap.get_my_positions()
        if len(col) == 0:
            return "none"
        return "shor" if col[0]["side"] == "SELL" else "long"

    def get_balance(self):
        count = 0
        while True:
            try:
                res = self.wrap.get_my_balance()
                JPY = res[0]
                BTC = res[1]
                if JPY["currency_code"] != "JPY":
                    raise Exception("Illegal balance")
                if BTC["currency_code"] != "BTC":
                    raise Exception("Illegal balance")
            except BaseException as e:
                print(type(e))
                print(e)
                time.sleep(tconf.check_sleep_time)
                # print("Failed to check balances")
                count += 1
                if count > tconf.check_count:
                    m = "TradeMethod/get_balance : Failed to check balances."
                    self.d_message(m)
                    raise Exception(m)

            else:
                myJPY = {
                    "amount": JPY["amount"],
                    "available": JPY["available"]
                }
                myBTC = {
                    "amount": BTC["amount"],
                    "available": BTC["available"]
                }
                return myJPY, myBTC

    def get_order(self, id):
        query = "&child_order_acceptance_id=" + id

        count = 0
        while True:
            try:
                r = self.wrap.get_my_childorders(query)
            except BaseException as e:
                print(type(e))
                print(e)
                time.sleep(tconf.check_sleep_time)
                count += 1
                if count > tconf.check_count:
                    m = "TradeMethod/get_order : Failed to check order ."
                    self.d_message(m)
                    raise Exception(m)
            else:
                break

        if not r:
            return None
        row = r[0]
        return row["child_order_state"], row["side"], row["price"], row["size"]

    def wait_ordarable(self):
        while not self.check_orderable():
            time.sleep(5)

    def calc_buy_amount_price(self):
        myJPY, _ = self.get_balance()
        count = 0
        while True:
            try:
                r = self.wrap.get_board("")
            except BaseException as e:
                print(type(e))
                print(e)
                time.sleep(tconf.get_board_time)
                count += 1
                if count > tconf.get_board_count:
                    m = "TradeMethod/calc_buy_amount_price : Failed to get board."
                    self.d_message(m)
                    raise Exception(m)
            else:
                break

        price = r["bids"][0]["price"] + 1
        amount = myJPY["available"] / price
        print(price, amount)

        return amount, price
        # return amount, price

    def calc_sell_amount_price(self):
        _, myBTC = self.get_balance()
        count = 0
        while True:
            try:
                r = self.wrap.get_board("")
            except BaseException as e:
                print(type(e))
                print(e)
                time.sleep(tconf.get_board_time)
                count += 1
                if count > tconf.get_board_count:
                    m = "TradeMethod/calc_buy_amount_price : Failed to get board."
                    self.d_message(m)
                    raise Exception(m)
            else:
                break

        price = r["bids"][0]["price"]
        amount = myBTC["available"]
        print(price, amount)

        return amount, price

    def get_board_price(self):
        for _ in range(tconf.get_board_count):
            try:
                r = self.wrap.get_board("")
            except BaseException as e:
                print(type(e))
                print(e)
                time.sleep(tconf.get_board_time)
            else:
                return r["bids"][0]["price"] + 1
        m = "TradeMethod/calc_buy_amount_price : Failed to get board."
        self.d_message(m)
        raise Exception(m)

    def calc_entry_amount_price(self):
        col = self.wrap.get_my_collateral()
        price = self.get_board_price()
        amount = col['collateral'] / price
        print(price, amount)
        if tconf.cycle_debug: amount = 0.01

        return amount, price

    def calc_close_amount_price(self):
        if tconf.cycle_debug: return 0.01
        pos = self.wrap.get_my_positions()
        return sum(map(lambda v: v['size'], pos))

    def shouldsellall(self, price):
        count = 0
        while True:
            try:
                r = self.wrap.get_board("")
            except BaseException as e:
                print(type(e))
                print(e)
                time.sleep(tconf.get_board_time)
                count += 1
                if count > tconf.get_board_count:
                    m = "TradeMethod/shouldsellall : Failed to get board."
                    self.d_message(m)
                    raise Exception(m)
            else:
                break
        price_board = r["mid_price"]
        if price * tconf.close_rate > price_board:
            return True
        else:
            return False

    def d_message(self, message):
        pass
        # Discordで発行したWebhookのURLを入れる
        # data = {"content": " " + message + " "}
        # requests.post(tconf.discord_webhook_url, data=data)
