import csv
import datetime

# 設定値
#   from https://api.bitcoincharts.com/v1/csv/
input_file_name = "./data/bitflyerJPY.csv"
output_file_name = "./data/btcjpn_skippedrange.csv"
# 集計を開始する日付＋時刻
# 2017/07/04 17:01:38
kijyun_date = datetime.datetime.strptime('2017-07-04 17:15:00', '%Y-%m-%d %H:%M:%S')
kizami_date = datetime.timedelta(minutes=1)


# CSV読み込み
csv_file = open(input_file_name, "r", encoding="ms932", errors="", newline="")
f = csv.reader(csv_file, delimiter=",", doublequote=True, lineterminator="\r\n", quotechar='"', skipinitialspace=True)

# 4本値を計算
datalist = []
priceO = 0
priceH = 0
priceL = 0
priceC = 0
priceV = 0
pre_datafull_date = None

for row in f:
    # forLoopで読み込まれたタイムスタンプに対応するローカルな日付 < 基準日 + ○分足
    if (datetime.datetime.fromtimestamp(int(row[0])) < kijyun_date + kizami_date):
        # Openにレートが入っているか。
        if priceO == 0:
            priceO = int(row[1].replace('.000000000000', ''))
            priceH = int(row[1].replace('.000000000000', ''))
            priceL = int(row[1].replace('.000000000000', ''))
            priceC = int(row[1].replace('.000000000000', ''))
            priceV = float(row[2])
        else:
            priceH = priceO
            priceL = priceO
            # Highのレートより大きいかどうか
            if priceH < int(row[1].replace('.000000000000', '')):
                priceH = int(row[1].replace('.000000000000', ''))
            # Lowのレートより小さいかどうか
            if priceL > int(row[1].replace('.000000000000', '')):
                priceL = int(row[1].replace('.000000000000', ''))
            # Closeのレートを更新
            priceC = int(row[1].replace('.000000000000', ''))
            priceV += float(row[2])
    else:
        # ○分足で取引がなかった場合
        if priceV == 0:
            priceH = priceO
            priceL = priceO
            priceC = priceO
            if pre_datafull_date is None:
                pre_datafull_date = kijyun_date

        elif pre_datafull_date is not None:
            diff = (kijyun_date - pre_datafull_date).total_seconds()
            if int(diff) > 30 * 60:
                datalist_new = str(pre_datafull_date), str(kijyun_date), diff
                datalist.append(datalist_new)
            pre_datafull_date = None

        # datalist_new = '{0:%Y%m%d %H:%M:%S}'.format(kijyun_date + kizami_date), priceO, priceH, priceL, priceC, priceV
        # datalist_new = int((kijyun_date + kizami_date).timestamp()), priceO, priceH, priceL, priceC, priceV
        # datalist.append(datalist_new)
        # 次ループの下処理
        kijyun_date = kijyun_date + kizami_date
        priceO = priceC
        priceH = 0
        priceL = 0
        priceC = 0
        priceV = 0

# CSVファイルに出力する
open(output_file_name)
csv_file = open(output_file_name, 'w', encoding='UTF-8')
csv_writer = csv.writer(csv_file, lineterminator='\n')
for j in range(len(datalist)):
    csv_writer.writerow(datalist[j])
csv_file.close()
