

from collections import defaultdict


output_file_name = "./data/btcjpn_2015_2020_5m_cc.csv"


def parse_csv_line(line):
    return list(map(float, line.split(",")))


def get_local_data():
    f = open(output_file_name)
    txt = f.read()
    f.close()
    csvarr = list(map(parse_csv_line, txt.strip().split("\n")))

    return list(csvarr)


if __name__ == "__main__":
    counts = defaultdict(list)
    data = get_local_data()
    for row in data:
        v = (row[1] + row[4]) / 2
        d = row[2] - row[3]
        pv = int(v / 1000)
        counts[pv].append(d)
    result = {}
    for key, val in counts.items():
        result[key] = sum(val) / len(val)
    for key, val in result.items():
        print(f"{key}\t{val}")
