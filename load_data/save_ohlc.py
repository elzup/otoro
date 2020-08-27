from coinapi_rest_v1 import CoinAPIv1
import os
import re

# import datetime
import keys as conf
import datetime


test_key = conf.coin_api_key
api = CoinAPIv1(test_key)
period_id = '5MIN'

regex_ts = r'\d\d\d\d-\d\d-\d\d.\d\d:\d\d:\d\d'
p1 = re.compile(regex_ts)


def write(path, fileName, filemode, Msg):

    try:
        path = os.path.join(path, fileName)
        with open(path, mode=filemode, encoding="utf-8") as f:
            f.write(Msg)

    except Exception as e:
        print(str(TimeCurrent()), " Exception => Output Write: ", fileName, str(e))


def row_to_line(row):
    timeVal = row['time_period_start']
    # timeStr = timeRegex(timeVal)

    _O = row['price_open']
    _H = row['price_high']
    _L = row['price_low']
    _C = row['price_close']

    return ",".join([timeVal, str(_O), str(_H), str(_L), str(_C)])


def convert2csv(res):
    return "\n".join(map(row_to_line, res))


def writeFile(text, path, filename):
    try:
        write(path, filename, "a", text)

    except Exception as e:
        print("Exception => writeFile: " + str(e))


def timeRegex(timeVal):

    try:
        m1 = p1.match(timeVal)
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
    start_of = datetime.date(2019, 5, 28).isoformat()

    # 例
    # hist = api.ohlcv_historical_data('BITFINEX_SPOT_BTC_USD', {'period_id': '1MIN', 'time_start': start_of, 'limit': 10000})

    hist = api.ohlcv_historical_data(conf.simbpl_id, {'period_id': period_id, 'time_start': start_of, 'limit': 100000})
    print("len: ", len(hist))

    # 保存
    PATH = "./data"
    FILE_NAME = "{0}_.csv".format(period_id)

    text = convert2csv(hist)

    writeFile(text, PATH, FILE_NAME)

    print(str(TimeCurrent()), "Complete")
