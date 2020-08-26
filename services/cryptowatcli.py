from datetime import datetime
from typing import Literal, get_args
import time
import requests
import numpy as np


def cryptowat_request(periods: int, after: int):
    response = requests.get(
        "https://api.cryptowat.ch/markets/bitflyer/btcjpy/ohlc",
        params={"periods": periods, "after": after}, timeout=5)
    response.raise_for_status()
    data = response.json()
    return list(data["result"][str(periods)]), data["allowance"]


PERIOD = Literal[60, 180, 300, 900, 1800, 3600, 7200, 14400, 21600, 43200, 86400, 259200, 604800]
period_list = get_args(PERIOD)


def get_ohlc(periods, data_size):
    assert periods in period_list, 'invalid periods arg'

    after = int(datetime.now().timestamp() - (periods * data_size))
    while True:
        try:
            data, allo = cryptowat_request(periods, after)
            return np.array(data), allo
        except requests.exceptions.RequestException as e:
            print("Cryptowatchの価格取得でエラー発生 : ", e)
            print("10秒待機してやり直します")
            time.sleep(10)
        except BaseException as e:
            print(e)
            print("Retry in 1 minute")
            time.sleep(60)
