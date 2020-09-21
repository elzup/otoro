import hmac
import json
import math
from datetime import datetime
from services.api_abs import WrapperAPI
from time import time
from typing import Literal, Tuple
import hmac
from util import find


import requests

from binance.client import Client
from binance.exceptions import BinanceAPIException
import binance
from config import keys


roundt = lambda v, pres: "{:0.0{}f}".format(float(v), pres)


class BinanceWrapperAPI(WrapperAPI):

    # (n) means that parameter is necessary

    def __init__(self, pair, target, precision):
        self.pair = pair
        self.precision = precision
        self.target = target
        self.client = Client(keys.binance_api_key, keys.binance_api_secret)

    def get_my_balance_coin(self, coin):
        balances = self.client.futures_account_balance()
        balance = find(lambda v: v['asset'] == coin, balances)
        return float(balance['withdrawAvailable']) if balance else 0

    def get_mycoin(self):
        return self.get_my_balance_coin('USDT')

    def get_position_targ(self) -> Tuple[float, bool]:
        risks = self.client.futures_position_information(symbol=self.target)
        position = find(lambda v: v['symbol'] == self.pair, risks)
        amt = float(position['positionAmt'])
        return abs(amt), amt >= 0

    def get_balance_interest(self):
        amount, _ = self.get_position_targ()
        return amount

    def buy_order(self, amount: float):
        return self.post_order_market("BUY", amount)

    def sell_order(self, amount: float):
        return self.post_order_market("SELL", amount)

    def post_order_market(self, side: str, quantity: float):
        try:
            res = self.client.futures_create_order(
                symbol=self.pair,
                side=side,
                type="MARKET",
                # positionSide=pside,
                quantity=roundt(quantity, self.precision)
            )
            return [True, res['orderId']]
        except BinanceAPIException as e:
            raise(e)
            return [False, e]

    def get_open_orders(self):
        return self.client.get_open_orders(symbol=self.pair)

    def get_position(self) -> Literal["none", "long", "shor"]:
        amount, posi = self.get_position_targ()
        if amount == 0:
            return 'none'
        return "long" if posi else "shor"

    def get_ask(self):
        return float(self.client.get_ticker(symbol=self.pair)['askPrice'])

    def get_bid(self):
        return float(self.client.get_ticker(symbol=self.pair)['bidPrice'])

    def get_order_status(self, id) -> Literal["COMP", "NEW", "EXPIRE"]:
        try:
            res = self.client.futures_get_order(symbol=self.pair, orderId=id)
            if res['status'] == "FILLED":
                return "COMP"
            # other: CANCELED, PARTIALLY_FILLED
            return "NEW"

        except BinanceAPIException as e:
            return "EXPIRE"
