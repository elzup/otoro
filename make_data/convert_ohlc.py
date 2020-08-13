import csv
import datetime

# 設定値
#   from https://api.bitcoincharts.com/v1/csv/
# output_file_name = "./data/btcjpn_skippedrange.csv"
input_file_name1 = "./data/bitflyerJPY.csv"
input_file_name2 = "./data/coincheckJPY.csv"
output_file_name = "./data/btcjpn_2017_2020_5m_full.csv"
# 集計を開始する日付＋時刻
# 2017/07/04 17:01:38

iter_date = datetime.datetime.strptime('2017-01-00 00:00:00', '%Y-%m-%d %H:%M:%S')
diff_date = datetime.timedelta(minutes=1)


def read_csv(path):
    csv_file = open(path, "r", encoding="ms932", errors="", newline="")
    return csv.reader(csv_file, delimiter=",", doublequote=True, lineterminator="\r\n", quotechar='"', skipinitialspace=True)


f1 = read_csv(input_file_name1)
f2 = read_csv(input_file_name2)


def merge_iter(f1, f2):
    row1 = next(f1, None)
    row2 = next(f2, None)
    t1 = datetime.datetime.fromtimestamp(int(row1[0]))
    t2 = datetime.datetime.fromtimestamp(int(row2[0]))
    while row1 and row2:
        if t1 < t2:
            yield [t1, row1]
            row1 = next(f1, None)
            t1 = row1 and datetime.datetime.fromtimestamp(int(row1[0]))
        else:
            yield [t2, row2]
            row2 = next(f2, None)
            t2 = row2 and datetime.datetime.fromtimestamp(int(row2[0]))


datalist = []
priceO = 0
priceH = 0
priceL = 0
priceC = 0
priceV = 0
pre_datafull_date = None

for [time, row] in merge_iter(f1, f2):
    # forLoopで読み込まれたタイムスタンプに対応するローカルな日付 < 基準日 + ○分足
    if (datetime.datetime.fromtimestamp(int(row[0])) < iter_date + diff_date):
        v = int(row[1].replace('.000000000000', ''))
        # Openにレートが入っているか。
        if v < 10000:
            continue
        if priceO == 0:
            priceO = v
            priceH = v
            priceL = v
            priceC = v
            priceV = float(row[2])
        else:
            priceH = max(priceH, v)
            priceL = min(priceL, v)
            # Closeのレートを更新
            priceC = v
            priceV += float(row[2])
    else:
        # ○分足で取引がなかった場合
        if priceV == 0:
            priceH = priceO
            priceL = priceO
            priceC = priceO
        # datalist_new = '{0:%Y%m%d %H:%M:%S}'.format(iter_date + diff_date), priceO, priceH, priceL, priceC, priceV
        datalist_new = int((iter_date + diff_date).timestamp()), priceO, priceH, priceL, priceC, priceV
        datalist.append(datalist_new)
        # 次ループの下処理
        iter_date = iter_date + diff_date
        priceO = priceC
        priceH = 0
        priceL = 0
        priceC = 0
        priceV = 0

# CSVファイルに出力する
csv_file = open(output_file_name, 'w', encoding='UTF-8')
csv_writer = csv.writer(csv_file, lineterminator='\n')
for j in range(len(datalist)):
    csv_writer.writerow(datalist[j])
csv_file.close()
