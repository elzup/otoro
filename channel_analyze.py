import numpy as np
# from config import Tradeconfig as tconf


def parse_csv_line(line):
    return list(map(float, line.split(",")))


def get_local_data():
    f = open("./data/btcjpn_2017_2020_5m.csv")
    txt = f.read()
    f.close()
    csvarr = list(map(parse_csv_line, txt.strip().split("\n")))

    # print(len(list(csvarr)))
    return np.array(list(csvarr)[:1000])


data = get_local_data()

for row in data:
    row[4]
