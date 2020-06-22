import requests
import time
import sqlite3
from TradeMethod import TradeMethod
import sys

list_size = 6000
period = 60
trader = TradeMethod()
dbname = "sample.db"
pair = "btcfxjpy"


def request_candle():
    while True:
        try:
            response = requests.get("https://api.cryptowat.ch/markets/bitflyer/" + pair + "/ohlc", params={"periods": period, "after": 1})
            response.raise_for_status()
            response = response.json()
            response_data = []
            for i in range(list_size - 1):
                response_data.append(tuple(response["result"][str(period)][i]))
        except BaseException:
            trader.d_message("Failed to get candle")
            time.sleep(3600)
        else:
            break

    return response_data


def insert_database(response_data):
    try:
        con = sqlite3.connect(dbname)
        create_table = "CREATE TABLE IF NOT EXISTS" + pair + "(CloseTime integer, OpenPrice integer, HighPrice integer, LowPrice integer, ClosePrice integer, BTCVolume real, JPYVolume real)"
        con.execute(create_table)

        unique = "CREATE UNIQUE INDEX IF NOT EXISTS time ON" + pair + "(CloseTime)"
        con.execute(unique)

        for i in range(list_size / 2 - 20, len(response_data)):
            try:
                con.execute("INSERT INTO " + pair + " values (?,?,?,?)", response_data[i])
            except sqlite3.IntegrityError:
                pass

        con.commit()
        con.close()

        trader.d_message("Successfully inserted " + pair + " data")
    except Exception as e:
        print(e)
        trader.d_message(e)
        sys.exit(1)


if __name__ == "__main__":
    while True:
        insert_database(request_candle())
        time.sleep(period * list_size / 2)
