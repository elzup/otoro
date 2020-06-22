import time

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
            except BaseException:
                time.sleep(Tradeconfig.check_sleep_time)
                count += 1
                if count > Tradeconfig.check_count:
                    self.d_message(
                        "TradeMethod/isCompleted : Failed to check that order has completed or not.")
                    raise Exception(
                        "TradeMethod/isCompleted : Failed to check that order has completed or not.")
            else:
                break

        if r["child_order_state"] == "COMPLETED":
            return True, r["side"], r["price"], r["size"]
        else:
            return False, None

    def cancel_all_orders(self):
        count = 0
        while True:
            try:
                result = self.wrap.post_cancel_all_orders()
            except BaseException:
                time.sleep(Tradeconfig.check_sleep_time)
                # print("Failed to Cancel All Orders")
                count += 1
                if count > Tradeconfig.check_count:
                    self.d_message(
                        "TradeMethod/cancel_all_orders : Failed to Cancel All Orders.")
                    raise Exception(
                        "TradeMethod/cancel_all_orders : Failed to Cancel All Orders.")
            else:
                if result["status_code"] == 200:
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
        if buy_flag:
            try:
                result = self.wrap.post_send_childorder(
                    "LIMIT", "BUY", price, amount)
            except BaseException:
                # print("注文が失敗しました")
                return False, None
            else:
                if result["status_code"] == 200:
                    buy_flag = False
                    return True, result["child_order_acceptance_id"]
                else:
                    return False, None

    def buy_signal(self, amount, price, buy_flag):
        count = 0
        while True:
            try:
                result = self.__buy_signal(amount, price, buy_flag)
            except BaseException:
                time.sleep(Tradeconfig.buy_sleep_time)
                count += 1
                if count > Tradeconfig.buy_count:
                    self.d_message(
                        "TradeController buy_jdg : Failed to send buy signal.")
                    raise Exception(
                        "TradeController buy_jdg : Failed to send buy signal.")
            else:
                return result

    def __sell_signal(self, amount, price, sell_flag):
        if sell_flag:
            try:
                result = self.wrap.post_send_childorder(
                    "LIMIT", "SELL", price, amount)
            except BaseException:
                # print("注文が失敗しました")
                return False, None
            else:
                if result["status_code"] == 200:
                    sell_flag = False
                    return True, result["child_order_acceptance_id"]
                else:
                    return False, None

    def sell_signal(self, amount, price, sell_flag):
        count = 0
        while True:
            try:
                result = self.__sell_signal(amount, price, sell_flag)
            except BaseException:
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
            except BaseException:
                # print("注文が失敗しました")
                return False, None
            else:
                if result["status_code"] == 200:
                    close_flag = False
                    return True, result["child_order_acceptance_id"]
                else:
                    return False, None

    def close_position(self, amount, close_flag):
        count = 0
        while True:
            try:
                result = self.__close_position(amount, close_flag)
            except BaseException:
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
            except BaseException:
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
            except BaseException:
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
            except BaseException:
                time.sleep(Tradeconfig.check_sleep_time)
                count += 1
                if count > Tradeconfig.check_count:
                    self.d_message(
                        "TradeMethod/get_order : Failed to check order .")
                    raise Exception(
                        "TradeMethod/get_order : Failed to check order.")
            else:
                break

        return r["child_order_state"], r["side"], r["price"], r["amount"]

    def calc_buy_amount_price(self):
        myJPY, _ = self.get_balance()
        count = 0
        while True:
            try:
                r = self.wrap.get_board("")
            except BaseException:
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

        return amount, price

    def shouldsellall(self, price):
        count = 0
        while True:
            try:
                r = self.wrap.get_board("")
            except BaseException:
                time.sleep(Tradeconfig.get_board_time)
                count += 1
                if count > Tradeconfig.get_board_count:
                    self.d_message(
                        "TradeMethod/calc_buy_amount_price : Failed to get board.")
                    raise Exception(
                        "TradeMethod/calc_buy_amount_price : Failed to get board.")
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
