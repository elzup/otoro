import hmac
import json
import math
from datetime import datetime
from time import time
from typing import Literal
import hmac
from util import find


import requests

from binance.client import Client
from config import keys


roundt = lambda v: "{:0.0{}f}".format(v, 3)


class BinanceWrapperAPI:

    # (n) means that parameter is necessary

    def __init__(self, product_code="BTC_JPY"):
        self.product_code = product_code
        self.pair = product_code
        self.client = Client(keys.binance_api_key, keys.binance_api_secret)

    def set_product_code(self, product_code):
        self.product_code = product_code

    def get_board(self, market=None):
        return self.get(f"/markets/{market or self.product_code}")

    def sell_amount(self, market=None):
        return self.get_board(market)['result']['ask']

    def get_bid(self):
        return float(self.client.get_ticker(symbol=self.pair)['bidPrice'])

    def get_ask(self):
        return float(self.client.get_ticker(symbol=self.pair)['askPrice'])

    def get_ticker(self, query):
        pc = "?product_code=" + self.product_code
        return self.get("/v1/getticker" + pc + query)

    # count, before, after
    def get_executions(self, query):
        pc = "?product_code=" + self.product_code
        return self.get("/v1/getexecutions" + pc + query)

    def get_health(self, query):
        pc = "?product_code=" + self.product_code
        return self.get("/v1/gethealth" + pc + query)

    def get_my_balance(self):
        return self.get("/wallet/balances")

    def get_my_balance_coin(self, coin):
        balances = self.client.futures_account_balance()
        balance = find(lambda v: v['asset'] == coin, balances)
        return float(balance['withdrawAvailable']) if balance else 0

    def get_my_main(self):
        return self.get_my_balance_coin('USDT')

    def get_my_target(self):
        return self.get_my_balance_coin('YFI')

    def get_my_positions(self):
        pc = "?product_code=" + self.product_code
        return self.get("/v1/me/getpositions" + pc)

    def get_my_permissions(self):
        return self.get("/v1/me/getpermissions")

    # count, before, after, child_order_state, child_order_id, child_order_acceptance_id, parent_order_id

    def get_open_orders(self):
        return self.client.get_open_orders(symbol=self.pair)

    def get_my_childorders(self, query):
        pc = "?product_code=" + self.product_code
        return self.get("/v1/me/getchildorders" + pc + query)

    # count, before, after, parent_order_state
    def get_my_parentorders(self, query):
        pc = "?product_code=" + self.product_code
        return self.get("/v1/me/getparentorders" + pc + query)

    # parent_order_id or parent_order_acceptance_id
    def get_my_parentorder(self, query):
        if query is not None & query[0] == "&":
            query = query.replace("&", "?", 1)
        return self.get("/v1/me/getparentorder" + query)

    # count, before, after, child_order_id, child_order_acceptance_id
    def get_my_executions(self, query):
        pc = "?product_code=" + self.product_code
        return self.get("/v1/me/getexecutions" + pc + query)

    def get_my_tradingcommission(self):
        pc = "?product_code=" + self.product_code
        return self.get("/v1/me/gettradingcommission" + pc)["commission_rate"]

    # child_order_type(n), side(n), price(n), size(n), minute_to_expire, time_in_force
    def get_markets(self):
        return self.get("/markets")

    def post_order_limit(self, side, size, price, market=None):
        return self.post_order(side, size, "limit", price, market)

    def post_order_market(self, side, size):
        print(roundt(size))
        return self.client.futures_create_order(
            symbol=self.pair,
            side=side,
            type="MARKET",
            # positionSide=pside,
            quantity=roundt(size)
        )

    def post_order(self, side: Literal["sell", "buy"], size, mtype: Literal["market", "limit"], price, market=None):
        body = {
            "market": market,
            "side": side,
            "price": price,
            "type": mtype,
            "size": roundt(size)
        }
        return self.post("/orders", body)

    def post_cancel_childorder(self, child_order_id):
        return self.post("/v1/me/cancelchildorder", {
            "product_code": self.product_code,
            "child_order_id": child_order_id
        })

    def post_cancel_childorder_by_acceptance(self, acceptance_id):
        return self.post("/v1/me/cancelchildorder", {
            "product_code": self.product_code,
            "acceptance_id": acceptance_id
        })

    # order_method,minute_to_expire, time_in_force, parameters(see API
    # reference)

    def post_send_parentorder(
            self,
            order_method,
            parameters,
            minute_to_expire=43200,
            time_in_force="GTC"):
        body = {
            "order_method": order_method,
            "minute_to_expire": minute_to_expire,
            "time_in_force": time_in_force,
            "parameters": [parameters]
        }

        return self.post("/v1/me/sendparentorder", body)

    # parent_order_id or parent_order_acceptance_id
    def post_cancel_parentorder(self, parent_order_id):
        return self.post("/v1/me/cancelparentorder", {
            "product_code": self.product_code,
            "parent_order_id": parent_order_id
        })

    def post_cancel_parentorder_by_acceptance(self, acceptance_id):
        return self.post("/v1/me/cancelparentorder", {
            "product_code": self.product_code,
            "parent_order_acceptance_id": acceptance_id
        })

    def post_cancel_all_orders(self):
        body = {
            "product_code": self.product_code
        }
        return self.post("/v1/me/cancelallchildorders", body)

    def get(self, path_url):
        return self.__mywrapper(path_url, "GET", {})

    def post(self, path_url, body):
        return self.__mywrapper(path_url, "POST", body or {})

    def __mywrapper(self, path_url, method, body):

        base_url = 'https://ftx.com/api'
        url = base_url + path_url

        data = None
        if method == "POST":
            data = json.dumps(body)

        request = requests.Request(method, url, data=data)
        ts = int(time() * 1000)
        prepared = request.prepare()
        if prepared.body:
            signature_payload = f'{ts}{prepared.method}{prepared.path_url}{prepared.body}'.encode(
            )
        else:
            signature_payload = f'{ts}{prepared.method}{prepared.path_url}'.encode(
            )
        signature = hmac.new(keys.binance_api_key.encode(),
                             signature_payload, 'sha256').hexdigest()

        headers = {
            'X-MBX-APIKEY': keys.binance_api_secret,
            'FTX-SIGN': signature,
            'FTX-TS': str(ts),
        }

        if method == "GET":
            response = requests.get(url, headers=headers)
        else:
            assert(data)
            response = requests.post(url, data=data, headers=headers)

        return response.json()
