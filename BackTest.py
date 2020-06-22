from pprint import pprint

import numpy as np
import pandas as pd
import requests
from matplotlib import pyplot as plt

# -----------------------------------------------------------------
# 取引所関係のmethod

# bitFlyerのAPIを読み込んで終値のデータをpandasのSeriesにして返す関数


def get_price_data():
    response = requests.get(
        "https://api.cryptowat.ch/markets/bitflyer/btcfxjpy/ohlc",
        params={
            "periods": period,
            "after": 1})
    response = response.json()
    close_data = []
    for i in range(6000):
        close_data.append(response["result"][str(period)][i][4])
    arr = np.array(close_data)
    return pd.Series(arr)

# --------------------------------------------------------------------
# テクニカル指標実装系method

# EMA
# EMA_periodは期間、nはろうそく何本分前の値か


def EMA(EMA_period, n):
    EMA_data = []
    for i in range(2 * EMA_period):
        EMA_data.insert(0, close[data_n - 1 - i])
    if n == 0:
        arr = np.array(EMA_data)[-EMA_period:]
    else:
        arr = np.array(EMA_data)[-n - EMA_period:-n]
    # print(arr)
    EMA = pd.Series(arr).ewm(span=EMA_period).mean()
    # print(EMA)

    return EMA[EMA_period - 1]


# MACD
# a=短期EMA_period,b=長期EMA_period,s=シグナル期間
def MACD_and_signal(a, b, s):
    MACD = []
    for i in range(a):
        MACD.insert(0, EMA(a, i) - EMA(b, i))
    arr = np.array(MACD)[-s:]
    Signal = pd.Series(arr).rolling(s).mean()

    return MACD, Signal


# ATR
# nは期間、n=14が普通
def ATR(n):
    data = []
    for i in range(2 * n - 1):
        p1 = response[data_n - i - 1][2] - \
            response[data_n - i - 1][3]  # 当日高値-当日安値
        p2 = response[data_n - i - 1][2] - \
            response[data_n - i - 2][4]  # 当日高値-前日終値
        p3 = response[data_n - i - 1][3] - \
            response[data_n - i - 2][4]  # 当日安値-前日終値
        tr = max(abs(p1), abs(p2), abs(p3))
        data.insert(0, tr)
    arr = np.array(data)[-n:]
    # print(arr)
    ATR = pd.Series(arr).ewm(span=n).mean()
    # print(ATR)
    return ATR[n - 1]


# RSI
# pは期間
def RSI(p):
    RSI_period = p
    # RSI_data =
    diff = close.diff(1)
    positive = diff.clip_lower(0).ewm(alpha=1.0 / RSI_period).mean()
    negative = diff.clip_upper(0).ewm(alpha=1.0 / RSI_period).mean()
    RSI = 100 - 100 / (1 - positive / negative)
    return RSI


# --------------------------------------------------------------------
# 評価値系

# RSIとMACDによる売りサイン
def sell_signal(response, i):
    if True:
        return True
    else:
        return False


# RSIとMACDによる買いサイン
def buy_signal(response):
    if RSI:
        print("pass")
        return True
    else:
        return False

# --------------------------------------------------------------
# ここからアルゴリズム


# 設定
upper_limit = 1.008
lower_limit = 0.2
comm = 0.0015
comm2 = comm * 2
# 何秒足
period = 60
# 終値配列の長さ
data_n = 100
# flag
flag = {
    "check": True,
    "buy_position": False
}
close_data = get_price_data()
response_data = requests.get(
    "https://api.cryptowat.ch/markets/bitflyer/btcfxjpy/ohlc",
    params={
        "periods": period,
        "after": 1})
response_data = response_data.json()
i = profit = loss = count1 = count2 = drawdown = start = 0
price2 = 0
RSI1 = 50

myjpy = 100000
mybtc = 0

asset_list = [myjpy]

pprint(len(response_data["result"][str(period)]))

while i < 5500:
    while(flag["check"]):

        if i > 5500:
            break

        response = []
        closelist = []
        for j in range(data_n):
            response.append(response_data["result"]
                            [str(period)][i + j + start])
            closelist.append(close_data[i + j + start])
        arr = np.array(closelist)
        close = pd.Series(arr)
        # print(response[data_n-1][0])

        if buy_signal(response):
            print("Send buy order")
            price = close[data_n - 1]
            price2 = close[data_n - 1]
            mybtc = myjpy / price * (1 - comm)
            myjpy = 0
            flag["buy_position"] = True
            flag["check"] = False
        # else:print("買い注文しません")

        i += 1

    while(flag["buy_position"]):
        response = []
        closelist = []
        for j in range(data_n):
            response.append(response_data["result"]
                            [str(period)][i + j + start])
            closelist.append(close_data[i + j + start])
        arr = np.array(closelist)
        close = pd.Series(arr)
        price2 = close[data_n - 1]
        # print(i)
        if response[data_n - 1][2] > price * upper_limit:
            print("rikaku:")
            count1 += 1
            profit += price * (upper_limit - 1 - comm2)
            myjpy = mybtc * close[data_n - 1] * (1 - comm)
            mybtc = 0
            flag["buy_position"] = False
            flag["check"] = True
        if response[data_n - 1][3] < price * lower_limit:
            print("sonkiri:")
            count2 += 1
            loss += price * (1 - lower_limit + comm2)
            myjpy = mybtc * close[data_n - 1] * (1 - comm)
            mybtc = 0
            flag["buy_position"] = False
            flag["check"] = True
        i += 1
        if i > 5500:
            break

    asset_list.append(myjpy + mybtc * price2)

    if drawdown > profit - loss:
        drawdown = profit - loss


print("profit:" + str(profit))
print("loss:" + str(loss))
if myjpy != 0:
    print("earn:" + str(myjpy))
else:
    print("earn:" + str(mybtc * price))
print("count1:" + str(count1))
print("count2:" + str(count2))
ts = pd.Series(np.array(asset_list))
ts.plot()
plt.show()
