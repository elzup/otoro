import os

# import datetime
from config import Apikey as conf
import datetime

from load_data.coinapi_rest_v1 import CoinAPIv1

test_key = conf.coin_api_key
api = CoinAPIv1(test_key)


def write(path, fileName, filemode, Msg):

    try:
        path = os.path.join(path, fileName)
        with open(path, mode=filemode, encoding="utf-8") as f:
            f.write(Msg)

    except Exception as e:
        print(str(TimeCurrent()), " Exception => Output Write: ", fileName, str(e))


def writeFile(res, path, file_Name):

    try:
        for i in range(len(res)):

            timeVal = res[i]['time_period_start']
            timestmp = timeRegex(timeVal)

            _O = res[i]['price_open']
            _H = res[i]['price_high']
            _L = res[i]['price_low']
            _C = res[i]['price_close']

            val = "{0};{1};{2};{3};{4}{5}".format(timestmp, str(_O), str(_H), str(_L), str(_C), "\n")

            write(path, file_Name, "a", val)

        print(str(TimeCurrent()), "作業中")

    except Exception as e:
        print("Exception => writeFile: " + str(e))


def timeRegex(timeVal):
    import re
    regex_1 = r'\d\d\d\d-\d\d-\d\d.\d\d:\d\d:\d\d'

    try:
        p1 = re.compile(regex_1)
        text = timeVal
        m1 = p1.match(text)
        src = m1.group()
        dst = src.replace('T', ' ')
        return dst

    except Exception as e:
        print("Exception => timeRegex: " + str(e))
        return "0000-00-00 00:00:00"


def TimeCurrent():
    now = datetime.datetime.now()
    return now


if __name__ == '__main__':

    # 日付を指定する
    start_of = datetime.date(2014, 11, 17).isoformat()
    # 例
    # ohlcv_historical = api.ohlcv_historical_data('BITFINEX_SPOT_BTC_USD', {'period_id': '1MIN', 'time_start': start_of, 'limit': 10000})

    ohlcv_historical = api.ohlcv_historical_data(conf.simbpl_id, {'period_id': '1MIN', 'time_start': start_of, 'limit': 10000})
    print("len: ", len(ohlcv_historical))

    # 保存
    PATH = "./"
    FILE_NAME = "HistData_1.csv"  # ファイル名

    writeFile(ohlcv_historical, PATH, FILE_NAME)

    print(str(TimeCurrent()), "作業完了")
