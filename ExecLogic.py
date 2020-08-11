import time
from datetime import datetime
# from pprint import pprint
import numpy as np

import requests

from config import Tradeconfig as tconf
from TradeMethod import TradeMethod


def fstr(n):
    return str(int(n)).rjust(8, ' ')


def timestamp():
    return datetime.now().strftime('%Y-%m-%dT%H:%M:%S')


class ExecLogic:

    def get_price(self, periods, data_size):
        after = int(datetime.now().timestamp() - (periods * (data_size + 100)))
        while True:
            try:
                response = requests.get(
                    "https://api.cryptowat.ch/markets/bitflyer/btcjpy/ohlc",
                    params={"periods": periods, "after": after}, timeout=5)
                response.raise_for_status()
                data = response.json()
                s = []
                for i in range(-data_size, 0):
                    s.append(data["result"][str(periods)][i])
                return np.array(s)
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

    def buy_judge(self, i=0, data=None, size=tconf.channel_breakout_size):
        return self.__buy_judge_channelbreakout(i=i, data=data, size=size)

    def sell_judge(self, i=0, data=None, size=tconf.channel_breakout_size):
        return self.__sell_judge_channelbreakout(i=i, data=data, size=size)

    def __buy_judge_candle(self, i, data=None):
        min_datasize = 3
        if data is None:
            data = self.get_price(tconf.size_candle, min_datasize)
            i = min_datasize - 1
        if i < min_datasize:
            return False

        # print(i)
        # print(data)
        d0 = data[i - 2][1] - data[i - 2][4]
        d1 = data[i - 1][1] - data[i - 1][4]
        d2 = data[i][1] - data[i][4]

        limit = tconf.buy_judge_limit

        if ((d0 > 0) and (d1 > 0) and (d2 > 0)) and (d0 / d2 > limit and d1 / d2 > limit):
            # print(datetime.fromtimestamp(data[i][0]))
            return True
        else:
            return False

    def __buy_judge_goldencross(self, i, data=None):
        min_datasize = 11
        if data is None:
            data = self.get_price(tconf.size_candle, min_datasize)
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

        return sm_post > wm_post and sm_now < wm_now and sm_now < sm_post

    def __sell_judge_channelbreakout(self, i, size, data=None):
        if data is None:
            data = self.get_price(tconf.size_candle, size)
            if size == 0:
                return False
            i = size - 1
        elif i < size:
            return False
        max_v = max(data[i - size + 1:i, 4])
        min_v = min(data[i - size + 1:i, 4])
        if tconf.logic_print:
            print(f"{timestamp()}|{fstr(max_v)}|{fstr(min_v)}|{fstr(data[i][4])}")
        return max_v != min_v and min_v >= data[i][4]

    def __buy_judge_channelbreakout(self, i, size, data=None):
        if data is None:
            data = self.get_price(tconf.size_candle, size)
            if size == 0:
                return False
            i = size - 1
        elif i < size:
            return False
        max_v = max(data[i - size + 1:i, 4])
        min_v = min(data[i - size + 1:i, 4])

        if tconf.logic_print:
            print(f"{timestamp()}|{fstr(max_v)}|{fstr(min_v)}|{fstr(data[i][4])}")
        return max_v != min_v and max_v <= data[i][4]
