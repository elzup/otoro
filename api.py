import hashlib
import hmac
import json
import math
from datetime import datetime
from typing import Literal

import requests

from config import keys


round = lambda v: math.floor(v * 10 ** 8) / 10 ** 8


class WrapperAPI:
    # query = ?product_code=BTC_JPY&child_order_state=COMPLETED
    # query sould be like this
    # therefore argument query should be like
    # &child_order_state=COMPLETED

    # (n) means that parameter is necessary

    def __init__(self, product_code="BTC_JPY"):
        self.product_code = product_code

    def set_product_code(self, product_code):
        self.product_code = product_code

    def get_board(self, query):
        pc = "?product_code=" + self.product_code
        return self.get("/v1/getboard" + pc + query)

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
        return self.get("/v1/me/getbalance")

    def get_my_collateral(self):
        return self.get("/v1/me/getcollateral")

    def get_my_positions(self):
        pc = "?product_code=" + self.product_code
        return self.get("/v1/me/getpositions" + pc)

    def get_my_permissions(self):
        return self.get("/v1/me/getpermissions")

    # count, before, after, child_order_state, child_order_id, child_order_acceptance_id, parent_order_id

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

    def post_send_childorder(
            self,
            child_order_type: Literal["LIMIT", "MARKET"],
            side,
            size,
            product_code=None,
            price=0,
            minute_to_expire=43200,
            time_in_force="GTC"):
        if product_code == None:
            product_code = self.product_code
        if child_order_type == "LIMIT":
            body = {
                "product_code": product_code,
                "child_order_type": child_order_type,
                "side": side,
                "price": price,
                "size": round(size),
                "minute_to_expire": minute_to_expire,
                "time_in_force": time_in_force
            }
        else:  # MARKET
            body = {
                "product_code": self.product_code,
                "child_order_type": child_order_type,
                "side": side,
                "size": round(size),
                "minute_to_expire": minute_to_expire,
                "time_in_force": time_in_force
            }
            print(body)

        return self.post("/v1/me/sendchildorder", body)

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
        method = "GET"
        body = {}
        return self.__mywrapper(path_url, method, body)

    def post(self, path_url, body):
        method = "POST"
        return self.__mywrapper(path_url, method, body)

    def __mywrapper(self, path_url, method, body):
        api_key = keys.api_key
        api_secret = keys.api_secret

        base_url = "https://api.bitflyer.jp"

        timestamp = str(datetime.today())

        data = None
        if method == "GET":
            message = timestamp + method + path_url
        elif method == "POST":
            data = json.dumps(body)
            message = timestamp + method + path_url + data
        else:
            raise Exception("WrapperAPI/__mywrapper")

        signature = hmac.new(
            bytearray(
                api_secret.encode('utf-8')),
            message.encode('utf-8'),
            digestmod=hashlib.sha256).hexdigest()

        headers = {
            'ACCESS-KEY': api_key,
            'ACCESS-TIMESTAMP': timestamp,
            'ACCESS-SIGN': signature,
            'Content-Type': 'application/json'
        }

        if method == "GET":
            response = requests.get(base_url + path_url, headers=headers)
        else:
            assert(data)
            response = requests.post(
                base_url + path_url, data=data, headers=headers)
        return response.json()
