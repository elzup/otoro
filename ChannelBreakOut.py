from datetime import datetime, timedelta

import pandas as pd
import requests


def tstr(d): return str(d)[:10]

# OHLCデータ取得関数


def get_data(period, before=0, after=0):

    # パラメータ設定する
    params = {"periods": period}
    if before != 0:
        params["before"] = before
    if after != 0:
        params["after"] = after

    # リクエスト送信
    response = requests.get("https://api.cryptowat.ch/markets/bitflyer/btcjpy/ohlc", params)
    data = response.json()
    return data

# 過去20日分の高値と安値を算出する関数


def judge_high_and_low(df, ref_date, period_day):
    for j in range(len(df)):
        if tstr(df['Time'][j]) == tstr(ref_date):  # DataFrameの中に「基準日」を見つけた！
            print("hit")
            s_idx = j - (period_day - 1)  # 20日前の日のインデックス ※基準日を含むため-1
            if s_idx >= 0:  # DataFrameの範囲内（最低限の判定）
                return df[s_idx:j]['high'].max(), df[s_idx:j]['low'].min()  # 過去20日分の高値と安値
            break

# 終値を算出する関数


def get_close_price(df, ref_date):
    for j in range(len(df)):
        if tstr(df['Time'][j]) == tstr(ref_date):  # DataFrameの中に「基準日」を見つけた！
            return df['close'][j]  # 終値を返す


# main処理
period = 86400  # 1日（86400秒）
after = datetime(2020, 1, 1).strftime('%s')  # OHLCの取得開始日
before = datetime(2020, 7, 31).strftime('%s')  # OHLCの取得終了日
ref_date = datetime(2020, 1, 20)  # 判定開始日
period_day = 20  # チャネルブレイクのレンジ
close_price_work = 0  # 終値の処理用変数

# 過去のOHLCデータの取得
out_data = get_data(period, before, after)
Time_Data, Open_price, High_price, Low_price, Close_price = [], [], [], [], []
for ohlc in out_data["result"][str(period)]:
    Time_Data.append(datetime.fromtimestamp(ohlc[0]))
    Open_price.append(ohlc[1])
    High_price.append(ohlc[2])
    Low_price.append(ohlc[3])
    Close_price.append(ohlc[4])
df = pd.DataFrame({'Time': Time_Data, 'open': Open_price, 'high': High_price, 'low': Low_price, 'close': Close_price})

# ループ開始
while ref_date <= datetime(2020, 7, 31):
    high_val, low_val = judge_high_and_low(df, ref_date, period_day)  # 過去20日間の高値と安値を取得
    close_price_work = get_close_price(df, ref_date)  # 基準日の終値を取得
    print(str(ref_date) + " ： 過去" + str(period_day) + "日間の高値：" + str(high_val) + " 安値：" + str(low_val))
    if high_val < close_price_work:
        print("終値が過去20日間の高値を上抜け。終値は：" + str(close_price_work))
    elif low_val > close_price_work:
        print("終値が過去20日間の安値を下抜け。終値は：" + str(close_price_work))
    ref_date = ref_date + timedelta(days=1)  # 次の日
