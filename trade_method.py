import time
from typing import Literal

from config import config as tconf
from services.api_abs import WrapperAPI


class TradeMethod:
    def __init__(self, wrapper: WrapperAPI, leverage=1):
        self.wrap = wrapper
        self.leverage = leverage

    def __buy_signal(self, amount, price):
        return self.wrap.buy_order(amount)

    def buy_signal(self, amount, price):
        count = 0
        while True:
            try:
                result = self.__buy_signal(amount, price)
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

    def __sell_signal(self, amount, price):
        return self.wrap.sell_order(amount)

    def sell_signal(self, amount, price):
        count = 0
        while True:
            try:
                result = self.__sell_signal(amount, price)
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

    def check_orderable(self):
        return len(self.wrap.get_open_orders()) == 0

    def safe_order(self, amount, method):
        while True:
            [result, order_id] = method(amount, 0)
            i = 20
            if not result:
                amount *= 0.95
                time.sleep(3)
                i -= 1
                if i < 0:
                    raise Exception('limited retry count')
                continue
            while True:
                time.sleep(2)
                st = self.wrap.get_order_status(order_id)
                if st != "NEW": break

            if st == "COMP":
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
        amount, price = self.calc_close_amount_price()
        return self.safe_sell(amount), price

    def close_full_short(self):
        amount, price = self.calc_close_amount_price()
        return self.safe_buy(amount), price

    def get_position(self) -> Literal["none", "long", "shor"]:
        return self.wrap.get_position()

    def wait_ordarable(self):
        while not self.check_orderable():
            time.sleep(5)

    def calc_entry_amount_price(self):
        coin = self.wrap.get_mycoin()
        price = self.wrap.get_ask()
        amount = coin * self.leverage / price

        print(price, amount)
        if tconf.cycle_debug: amount = 0.01
        return amount, price

    def calc_close_amount_price(self):
        bid = self.wrap.get_bid()
        if tconf.cycle_debug: return 0.01, bid
        return self.wrap.get_balance_interest(), bid

    def d_message(self, message):
        pass
        # Discordで発行したWebhookのURLを入れる
        # data = {"content": " " + message + " "}
        # requests.post(tconf.discord_webhook_url, data=data)
