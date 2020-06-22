import hashlib
import hmac
import sqlite3
import time
from datetime import datetime
from pprint import pprint

import requests

from config import Apikey
from ExecLogic import ExecLogic
from WrapperAPI import WrapperAPI


def position():
    api_key = Apikey.api_key
    api_secret = Apikey.api_secret

    base_url = "https://api.bitflyer.jp"
    path_url = "/v1/me/getchildorders?product_code=BTC_JPY&child_order_state=COMPLETED"
    method = "GET"

    timestamp = str(datetime.today())
    message = timestamp + method + path_url

    signature = hmac.new(bytearray(api_secret.encode('utf-8')), message.encode('utf-8'), digestmod=hashlib.sha256).hexdigest()

    headers = {
        'ACCESS-KEY': api_key,
        'ACCESS-TIMESTAMP': timestamp,
        'ACCESS-SIGN': signature,
        'Content-Type': 'application/json'
    }

    response = requests.get(base_url + path_url, headers=headers)
    pprint(response.json()[0]["id"])
    return response.json()

# def check_open_orders(bitflyer):
#     try:
#         orders = bitflyer.fetch_open_orders(
#             symbol = "BTC/JPY",
#             params = { "product_code" : "BTC_JPY" })
#         pprint(orders)

#     except ccxt.BaseError as e:
#         print("BitflyerのAPIで問題発生 : ",e)
#     else:
#         return orders


def jsontest():
    aaa = "hi"
    bbb = None
    ccc = 120
    m = {
        "aaa": aaa,
        "bbb": bbb
    }
    n = {
        "ccc": ccc,
        "ddd": [m]
    }

    pprint(n)


def wraptest():
    wr = WrapperAPI()
    pprint(wr.get_my_balance())
    res = wr.get_my_balance()
    JPY = res[0]
    BTC = res[1]
    if JPY["currency_code"] != "JPY":
        raise Exception("Illegal balance")
    if BTC["currency_code"] != "BTC":
        raise Exception("Illegal balance")
    pprint(JPY)
    pprint(BTC)


def logictest():
    ExecLogic().get_price(900, 4)


def request_candle():
    pair = "btcfxjpy"
    response = requests.get("https://api.cryptowat.ch/markets/bitflyer/" + pair + "/ohlc", params={"periods": 60, "after": int(time.time()) - 60 * 10})
    response.raise_for_status()
    response = response.json()
    response_data = []
    for i in range(10):
        response_data.append(tuple(response["result"]["60"][i]))

    return response_data


def sqltest(data):
    con = sqlite3.connect("test.db")

    create = "CREATE TABLE IF NOT EXISTS btcfxjpy (CloseTime integer, OpenPrice integer, HighPrice integer, LowPrice integer, ClosePrice integer, BTCVolume real, JPYVolume real)"
    con.execute(create)

    unique = "CREATE UNIQUE INDEX IF NOT EXISTS time ON btcfxjpy(CloseTime)"
    con.execute(unique)

    for i in range(len(data)):
        try:
            con.execute("INSERT INTO btcfxjpy values (?,?,?,?,?,?,?)", data[i])
        except sqlite3.IntegrityError:
            print(i)

    con.commit()
    con.close()


if __name__ == "__main__":
    data1 = request_candle()
    sqltest(data1)

    time.sleep(120)

    data2 = request_candle()
    sqltest(data2)

    con = sqlite3.connect("test.db")
    cur = con.cursor()
    cur.execute("SELECT * from btcfxjpy")
    for row in cur:
        print(row)

    con.close()
