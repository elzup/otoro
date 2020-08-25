import time
import math

from config import Tradeconfig
from WrapperAPI import WrapperAPI


class TradeMethod:
    def __init__(self):
        self.wrap = WrapperAPI()

    def set_product_code(self, product_code):
        self.wrap.set_product_code(product_code)

    # possible return
    # COMPLETED, ACTIVE, CANCELED, EXPIRED, REJECTED, FAILED, UNKNOWN
    def isCompleted(self, id):
        query = "&child_order_acceptance_id=" + id

        count = 0
        while True:
            try:
                r = self.wrap.get_my_childorders(query)
            except BaseException as e:
                print(type(e))
                print(e)
                time.sleep(Tradeconfig.check_sleep_time)
                count += 1
                if count > Tradeconfig.check_count:
                    self.d_message(
                        "TradeMethod/isCompleted : Failed to check that order has completed or not.")
                    raise Exception(
                        "TradeMethod/isCompleted : Failed to check that order has completed or not.")
            else:
                break
        row = r[0]
        if not r or not row or row["child_order_state"] == "COMPLETED":
            return False, None
        return True, row["side"], row["price"], row["size"]

    def cancel_all_orders(self):
        count = 0
        while True:
            try:
                result = self.wrap.post_cancel_all_orders()
            except BaseException as e:
                print(type(e))
                print(e)
                time.sleep(Tradeconfig.check_sleep_time)
                # print("Failed to Cancel All Orders")
                count += 1
                if count > Tradeconfig.check_count:
                    self.d_message(
                        "TradeMethod/cancel_all_orders : Failed to Cancel All Orders.")
                    raise Exception(
                        "TradeMethod/cancel_all_orders : Failed to Cancel All Orders.")
            else:
                if 'status' not in result or result["status"] == 200:
                    return True
                else:
                    time.sleep(Tradeconfig.check_sleep_time)
                    # print("Failed to Cancel All Orders")
                    count += 1
                    if count > Tradeconfig.check_count:
                        self.d_message(
                            "TradeMethod/cancel_all_orders : Failed to Cancel All Orders.")
                        raise Exception(
                            "TradeMethod/cancel_all_orders : Failed to Cancel All Orders.")

    def __buy_signal(self, amount, price, buy_flag):
        if not buy_flag:
            return False, None

        try:
            result = self.wrap.post_send_childorder("LIMIT", "BUY", price, amount)
        except BaseException as e:
            # print("注文が失敗しました")
            print(type(e))
            print(e)
            return False, None

        if 'status' in result and result["status"] != 200:
            return False, None

        buy_flag = False
        return True, result["child_order_acceptance_id"]

    def buy_signal(self, amount, price, buy_flag):
        count = 0
        while True:
            try:
                result = self.__buy_signal(amount, price, buy_flag)
                print(result)
                break
            except BaseException as e:
                print(type(e))
                print(e)
                time.sleep(Tradeconfig.buy_sleep_time)
                count += 1
                if count > Tradeconfig.buy_count:
                    self.d_message(
                        "TradeController buy_jdg : Failed to send buy signal.")
                    raise Exception(
                        "TradeController buy_jdg : Failed to send buy signal.")
        return result

    def __sell_signal(self, amount, price, sell_flag):
        if not sell_flag:
            return False, None
        try:
            result = self.wrap.post_send_childorder("LIMIT", "SELL", price, amount)
            print(result)
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
                time.sleep(Tradeconfig.sell_sleep_time)
                count += 1
                if count > Tradeconfig.sell_count:
                    self.d_message(
                        "TradeMethod/sell_signal : Failed to send sell signal.")
                    raise Exception(
                        "TradeMethod/sell_signal : Failed to send sell signal.")
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
                time.sleep(Tradeconfig.close_sleep_time)
                count += 1
                if count > Tradeconfig.close_count:
                    self.d_message(
                        "TradeMethod/close_Position : Failed to send close signal!!!!!!!!!")
                    self.d_message(
                        "TradeMethod/close_Position : Failed to send close signal!!!!!!!!!")
                    self.d_message(
                        "TradeMethod/close_Position : Failed to send close signal!!!!!!!!!")
                    raise Exception(
                        "TradeMethod/sell_signal : Failed to send sell signal.")
            else:
                return result

    def get_open_order(self):
        query = "&child_order_state=ACTIVE"

        count = 0
        while True:
            try:
                r = self.wrap.get_my_childorders(query)
            except BaseException as e:
                print(type(e))
                print(e)
                time.sleep(Tradeconfig.check_sleep_time)
                count += 1
                if count > Tradeconfig.check_count:
                    self.d_message(
                        "TradeMethod/get_open_order : Failed to check orders.")
                    raise Exception(
                        "TradeMethod/get_open_order  : Failed to check orders.")
            else:
                break

        if len(r) == 0:
            return None
        elif len(r) == 1:
            return r[0]
        else:
            print(type(r))
            print(r)
            self.d_message(
                "TradeMethod/get_open_order : Failed to check orders.")
            raise Exception(
                "TradeMethod/get_open_order  : Failed to check orders.")

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
                time.sleep(Tradeconfig.check_sleep_time)
                # print("Failed to check balances")
                count += 1
                if count > Tradeconfig.check_count:
                    self.d_message(
                        "TradeMethod/get_balance : Failed to check balances.")
                    raise Exception(
                        "TradeMethod/get_balance : Failed to check balances.")

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
                time.sleep(Tradeconfig.check_sleep_time)
                count += 1
                if count > Tradeconfig.check_count:
                    self.d_message(
                        "TradeMethod/get_order : Failed to check order .")
                    raise Exception(
                        "TradeMethod/get_order : Failed to check order.")
            else:
                break

        row = r[0]
        return row["child_order_state"], row["side"], row["price"], row["size"]

    def calc_buy_amount_price(self):
        myJPY, _ = self.get_balance()
        count = 0
        while True:
            try:
                r = self.wrap.get_board("")
            except BaseException as e:
                print(type(e))
                print(e)
                time.sleep(Tradeconfig.get_board_time)
                count += 1
                if count > Tradeconfig.get_board_count:
                    self.d_message(
                        "TradeMethod/calc_buy_amount_price : Failed to get board.")
                    raise Exception(
                        "TradeMethod/calc_buy_amount_price : Failed to get board.")
            else:
                break

        price = r["bids"][0]["price"] + 1
        amount = myJPY["available"] / price
        amount = math.floor(amount * 10 ** 8) / 10 ** 8
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
                time.sleep(Tradeconfig.get_board_time)
                count += 1
                if count > Tradeconfig.get_board_count:
                    self.d_message(
                        "TradeMethod/calc_buy_amount_price : Failed to get board.")
                    raise Exception(
                        "TradeMethod/calc_buy_amount_price : Failed to get board.")
            else:
                break

        price = r["bids"][0]["price"]
        amount = myBTC["available"]
        amount = math.floor(amount * 10 ** 8) / 10 ** 8
        print(price, amount)

        return amount, price

    def shouldsellall(self, price):
        count = 0
        while True:
            try:
                r = self.wrap.get_board("")
            except BaseException as e:
                print(type(e))
                print(e)
                time.sleep(Tradeconfig.get_board_time)
                count += 1
                if count > Tradeconfig.get_board_count:
                    message = "TradeMethod/shouldsellall : Failed to get board."
                    self.d_message(message)
                    raise Exception(message)
            else:
                break
        price_board = r["mid_price"]
        if price * Tradeconfig.close_rate > price_board:
            return True
        else:
            return False

    def d_message(self, message):
        pass
        # Discordで発行したWebhookのURLを入れる
        # data = {"content": " " + message + " "}
        # requests.post(Tradeconfig.discord_webhook_url, data=data)
