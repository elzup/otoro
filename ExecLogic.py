import time
from datetime import datetime

import requests

from config import Tradeconfig
from TradeMethod import TradeMethod


class ExecLogic:

    def get_price(self, min, data_size):
        while True:
            try:
                response = requests.get("https://api.cryptowat.ch/markets/bitflyer/btcjpy/ohlc", params={"periods": min}, timeout=5)
                response.raise_for_status()
                data = response.json()
                s = []
                for i in range(-1 - data_size, -1):
                    s.append(data["result"][str(min)][i])
                # pprint(s)
                return s
            except requests.exceptions.RequestException as e:
                print("Cryptowatchの価格取得でエラー発生 : ", e)
                print("10秒待機してやり直します")
                time.sleep(10)
            except BaseException:
                t = TradeMethod()
                t.d_message(s)
                t.d_message("ExecLogic/get_price list index out of range?")
                print("ExecLogic/get_price")
                print("60秒待機してやり直します")
                time.sleep(60)

    def buy_judge(self, i=0, data=None):
        # return self.__buy_judge_candle(i=i, data=data)
        return self.__buy_judge_goldencross(i=i, data=data)

    def __buy_judge_candle(self, i, data=None):
        min_datasize = 3
        if data is None:
            data = self.get_price(Tradeconfig.size_candle, min_datasize)
            i = min_datasize - 1
        if i < min_datasize:
            return False

        # print(i)
        # print(data)
        d0 = data[i - 2][1] - data[i - 2][4]
        d1 = data[i - 1][1] - data[i - 1][4]
        d2 = data[i][1] - data[i][4]

        limit = Tradeconfig.buy_judge_limit

        if ((d0 > 0) and (d1 > 0) and (d2 > 0)) and (d0 / d2 > limit and d1 / d2 > limit):
            print(datetime.fromtimestamp(data[i][0]))
            return True
        else:
            return False

    def __buy_judge_goldencross(self, i, data=None):
        min_datasize = 11
        if data is None:
            data = self.get_price(Tradeconfig.size_candle, min_datasize)
            i = min_datasize - 1
        if i < min_datasize:
            return False

        sm_now = sm_post = wm_now = wm_post = 0  # sm means simplemean and wm means weightmean
        sum0 = 0
        for j in range(min_datasize - 1):
            sm_now += data[i - j][4]
            sm_post += data[i - j - 1][4]
            wm_now += data[i - j][4] * (min_datasize - 1 - j)
            wm_post += data[i - j - 1][4] * (min_datasize - 1 - j)
            sum0 += min_datasize - 1 - j

        sm_now /= min_datasize - 1
        sm_post /= min_datasize - 1

        wm_now /= sum0
        wm_post /= sum0

        if sm_post > wm_post and sm_now < wm_now and sm_now < sm_post:
            print(datetime.fromtimestamp(data[i][0]))
            return True
        else:
            return False
