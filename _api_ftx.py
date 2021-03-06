import hmac
import json
import math
from datetime import datetime
from time import time
from typing import Literal
import hmac


import requests

from config import keys


round = lambda v: math.floor(v * 10 ** 8) / 10 ** 8


class FtxWrapperAPI:
    # query = ?product_code=BTC_JPY&child_order_state=COMPLETED
    # query sould be like this
    # therefore argument query should be like
    # &child_order_state=COMPLETED

    # (n) means that parameter is necessary

    def __init__(self, product_code="BTC_JPY"):
        self.product_code = product_code

    def set_product_code(self, product_code):
        self.product_code = product_code

    def get_board(self, market=None):
        return self.get(f"/markets/{market or self.product_code}")

    def sell_amount(self, market=None):
        return self.get_board(market)['result']['ask']

    def buy_amount(self, market=None):
        return self.get_board(market)['result']['bid']

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
        balances = self.get("/wallet/balances")
        return next(filter(lambda v: v['coin'] == coin, balances['result']))

    def get_my_usd(self):
        return self.get_my_balance_coin('USD')

    def get_my_yfi(self):
        return self.get_my_balance_coin('YFI')

    def get_my_positions(self):
        pc = "?product_code=" + self.product_code
        return self.get("/v1/me/getpositions" + pc)

    def get_my_permissions(self):
        return self.get("/v1/me/getpermissions")

    # count, before, after, child_order_state, child_order_id, child_order_acceptance_id, parent_order_id

    def get_open_orders(self):
        return self.get(f'/orders?market={self.product_code}')

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

    def post_order_market(self, side, size, market):
        return self.post_order(side, size, "market", None, market)

    def post_order(self, side: Literal["sell", "buy"], size, mtype: Literal["market", "limit"], price, market=None):
        body = {
            "market": market,
            "side": side,
            "price": price,
            "type": mtype,
            "size": round(size)
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
        signature = hmac.new(keys.ftx_api_secret.encode(),
                             signature_payload, 'sha256').hexdigest()

        headers = {
            'FTX-KEY': keys.ftx_api_key,
            'FTX-SIGN': signature,
            'FTX-TS': str(ts),
        }

        if method == "GET":
            response = requests.get(url, headers=headers)
        else:
            assert(data)
            response = requests.post(url, data=data, headers=headers)

        return response.json()
