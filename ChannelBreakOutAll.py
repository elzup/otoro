#_*_ coding: utf-8 _*_

import pybitflyer
import json
import requests
import csv
import math
import pandas as pd
import time
import requests
import datetime
from tornado import gen
import threading
from collections import deque

class ChannelBreakOut:
    def __init__(self):
        #pubnubから取得した約定履歴を保存するリスト（基本的に不要．）
        self._executions = deque(maxlen=300)
        self._lot = 0.01
        self._product_code = "FX_BTC_JPY"
        #各パラメタ．
        self._entryTerm = 10
        self._closeTerm = 5
        self._rangeTerm = 15
        self._rangeTh = 5000
        self._waitTerm = 5
        self._waitTh = 20000
        self._candleTerm = "1T"
        #現在のポジション．1ならロング．-1ならショート．0ならポジションなし．
        self._pos = 0
        #注文執行コスト．遅延などでこの値幅を最初から取られていると仮定する
        self._cost = 3000
        self.order = Order()
        self.api = pybitflyer.API("your key", "your secret")

        #ラインに稼働状況を通知
        self.line_notify_token = 'your token'
        self.line_notify_api = 'https://notify-api.line.me/api/notify'

    @property
    def cost(self):
        return self._cost

    @cost.setter
    def cost(self, value):
        self._cost = value

    @property
    def candleTerm(self):
        return self._candleTerm
    @candleTerm.setter
    def candleTerm(self, val):
        """
        valは"5T"，"1H"などのString
        """
        self._candleTerm = val

    @property
    def waitTh(self):
        return self._waitTh
    @waitTh.setter
    def waitTh(self, val):
        self._waitTh = val

    @property
    def waitTerm(self):
        return self._waitTerm
    @waitTerm.setter
    def waitTerm(self, val):
        self._waitTerm = val

    @property
    def rangeTh(self):
        return self._rangeTh
    @rangeTh.setter
    def rangeTh(self,val):
        self._rangeTh = val

    @property
    def rangeTerm(self):
        return self._rangeTerm
    @rangeTerm.setter
    def rangeTerm(self,val):
        self._rangeTerm = val


    @property
    def executions(self):
        return self._executions
    @executions.setter
    def executions(self, val):
        self._executions = val

    @property
    def pos(self):
        return self._pos
    @pos.setter
    def pos(self, val):
        self._pos = int(val)

    @property
    def lot(self):
        return self._lot
    @lot.setter
    def lot(self, val):
        self._lot = round(val,3)

    @property
    def product_code(self):
        return self._product_code
    @product_code.setter
    def product_code(self, val):
        self._product_code = val

    @property
    def entryTerm(self):
        return self._entryTerm
    @entryTerm.setter
    def entryTerm(self, val):
        self._entryTerm = int(val)

    @property
    def closeTerm(self):
        return self._closeTerm
    @closeTerm.setter
    def closeTerm(self, val):
        self._closeTerm = int(val)

    def calculateLot(self, margin):
        """
        証拠金からロットを計算する関数．
        """
        lot = math.floor(margin*10**(-4))*10**(-2)
        return round(lot,2)

    def calculateLines(self, df_candleStick, term):
        """

        期間高値・安値を計算する．
        candleStickはcryptowatchのローソク足．termは安値，高値を計算する期間．（5ならローソク足5本文の安値，高値．)
        """
        lowLine = []
        highLine = []
        for i in range(len(df_candleStick.index)):
            if i < term:
                lowLine.append(df_candleStick["high"][i])
                highLine.append(df_candleStick["low"][i])
            else:
                low = min([price for price in df_candleStick["low"][i-term:i]])
                high = max([price for price in df_candleStick["high"][i-term:i]])
                lowLine.append(low)
                highLine.append(high)
        return (lowLine, highLine)

    def calculatePriceRange(self, df_candleStick, term):
        """
        termの期間の値幅を計算．
        """
        low = [min([df_candleStick["close"][i-term+1:i].min(),df_candleStick["open"][i-term+1:i].min()]) for i in range(len(df_candleStick.index))]
        high = [max([df_candleStick["close"][i-term+1:i].max(), df_candleStick["open"][i-term+1:i].max()]) for i in range(len(df_candleStick.index))]
        low = pd.Series(low)
        high = pd.Series(high)
        priceRange = [high.iloc[i]-low.iloc[i] for i in range(len(df_candleStick.index))]
        return priceRange

    def isRange(self,df_candleStick ,term, th):
        """
        レンジ相場かどうかをTrue,Falseの配列で返す．termは期間高値・安値の計算期間．thはレンジ判定閾値．
        """
        #値幅での判定．
        if th != None:
            priceRange = self.calculatePriceRange(df_candleStick, term)
            isRange = [th > i for i in priceRange]
        #終値の標準偏差の差分が正か負かでの判定．
        elif th == None and term != None:
            df_candleStick["std"] = [df_candleStick["close"][i-term+1:i].std() for i in range(len(df_candleStick.index))]
            df_candleStick["std_slope"] = [df_candleStick["std"][i]-df_candleStick["std"][i-1] for i in range(len(df_candleStick.index))]
            isRange = [i > 0 for i in df_candleStick["std_slope"]]
        else:
            isRange = [False for i in df_candleStick.index]
        return isRange

    def judge(self, df_candleStick, entryHighLine, entryLowLine, closeHighLine, closeLowLine, entryTerm):
        """
        売り買い判断．ローソク足の高値が期間高値を上抜けたら買いエントリー．（2）ローソク足の安値が期間安値を下抜けたら売りエントリー．judgementリストは[買いエントリー，売りエントリー，買いクローズ（売り），売りクローズ（買い）]のリストになっている．（二次元リスト）リスト内リストはの要素は，0（シグナルなし）,価格（シグナル点灯）を取る．
        """
        judgement = [[0,0,0,0] for i in range(len(df_candleStick.index))]
        for i in range(len(df_candleStick.index)):
            #上抜けでエントリー
            if df_candleStick["high"][i] > entryHighLine[i] and i >= entryTerm:
                judgement[i][0] = entryHighLine[i]
            #下抜けでエントリー
            if df_candleStick["low"][i] < entryLowLine[i] and i >= entryTerm:
                judgement[i][1] = entryLowLine[i]
            #下抜けでクローズ
            if df_candleStick["low"][i] < closeLowLine[i] and i >= entryTerm:
                judgement[i][2] = closeLowLine[i]
            #上抜けでクローズ
            if df_candleStick["high"][i] > closeHighLine[i] and i >= entryTerm:
                judgement[i][3] = closeHighLine[i]
            #
            else:
                pass
        return judgement

    def judgeForLoop(self, high, low, entryHighLine, entryLowLine, closeHighLine, closeLowLine):
        """
        売り買い判断．入力した価格が期間高値より高ければ買いエントリー，期間安値を下抜けたら売りエントリー．judgementリストは[買いエントリー，売りエントリー，買いクローズ（売り），売りクローズ（買い）]のリストになっている．（値は0or1）
        ローソク足は1分ごとに取得するのでインデックスが-1のもの（現在より1本前）をつかう．
        """
        judgement = [0,0,0,0]
        #上抜けでエントリー
        if high > entryHighLine[-1]:
            judgement[0] = 1
        #下抜けでエントリー
        if low < entryLowLine[-1]:
            judgement[1] = 1
        #下抜けでクローズ
        if low < closeLowLine[-1]:
            judgement[2] = 1
        #上抜けでクローズ
        if high > closeHighLine[-1]:
            judgement[3] = 1
        return judgement


    #エントリーラインおよびクローズラインで約定すると仮定する．
    def backtest(self, judgement, df_candleStick, lot, rangeTh, rangeTerm, originalWaitTerm=10, waitTh=10000, cost = 0):
        #エントリーポイント，クローズポイントを入れるリスト
        buyEntrySignals = []
        sellEntrySignals = []
        buyCloseSignals = []
        sellCloseSignals = []
        nOfTrade = 0
        pos = 0
        pl = []
        pl.append(0)
        #トレードごとの損益
        plPerTrade = []
        #取引時の価格を入れる配列．この価格でバックテストのplを計算する．（ので，どの価格で約定するかはテストのパフォーマンスに大きく影響を与える．）
        buy_entry = []
        buy_close = []
        sell_entry = []
        sell_close = []
        #各ローソク足について，レンジ相場かどうかの判定が入っている配列
        isRange =  self.isRange(df_candleStick, rangeTerm, rangeTh)
        #基本ロット．勝ちトレードの直後はロットを落とす．
        originalLot = lot
        #勝ちトレード後，何回のトレードでロットを落とすか．
        waitTerm = 0
        for i in range(len(judgement)):
            if i > 0:
                lastPL = pl[-1]
                pl.append(lastPL)
            #エントリーロジック
            if pos == 0 and not isRange[i]:
                #ロングエントリー
                if judgement[i][0] != 0:
                    pos += 1
                    buy_entry.append(judgement[i][0])
                    buyEntrySignals.append(df_candleStick.index[i])
                #ショートエントリー
                elif judgement[i][1] != 0:
                    pos -= 1
                    sell_entry.append(judgement[i][1])
                    sellEntrySignals.append(df_candleStick.index[i])
            #ロングクローズロジック
            elif pos == 1:
                #ロングクローズ
                if judgement[i][2] != 0:
                    nOfTrade += 1
                    pos -= 1
                    buy_close.append(judgement[i][2])
                    #値幅
                    plRange = buy_close[-1] - buy_entry[-1]
                    pl[-1] = pl[-2] + (plRange-self.cost) * lot
                    buyCloseSignals.append(df_candleStick.index[i])
                    plPerTrade.append((plRange-self.cost)*lot)
                    #waitTh円以上の値幅を取った場合，次の10トレードはロットを1/10に落とす．
                    if plRange > waitTh:
                        waitTerm = originalWaitTerm
                        lot = originalLot/10
                    elif waitTerm > 0:
                        waitTerm -= 1
                        lot = originalLot/10
                    if waitTerm == 0:
                        lot = originalLot
            #ショートクローズロジック
            elif pos == -1:
                #ショートクローズ
                if judgement[i][3] != 0:
                    nOfTrade += 1
                    pos += 1
                    sell_close.append(judgement[i][3])
                    plRange = sell_entry[-1] - sell_close[-1]
                    pl[-1] = pl[-2] + (plRange-self.cost) * lot
                    sellCloseSignals.append(df_candleStick.index[i])
                    plPerTrade.append((plRange-self.cost)*lot)
                    #waitTh円以上の値幅を取った場合，次の10トレードはロットを1/10に落とす．
                    if plRange > waitTh:
                        waitTerm = originalWaitTerm
                        lot = originalLot/10
                    elif waitTerm > 0:
                        waitTerm -= 1
                        lot = originalLot/10
                    if waitTerm == 0:
                        lot = originalLot

            #さらに，クローズしたと同時にエントリーシグナルが出ていた場合のロジック．
            if pos == 0 and not isRange[i]:
                #ロングエントリー
                if judgement[i][0] != 0:
                    pos += 1
                    buy_entry.append(judgement[i][0])
                    buyEntrySignals.append(df_candleStick.index[i])
                #ショートエントリー
                elif judgement[i][1] != 0:
                    pos -= 1
                    sell_entry.append(judgement[i][1])
                    sellEntrySignals.append(df_candleStick.index[i])
        #最後にポジションを持っていたら，期間最後のローソク足の終値で反対売買．
        if pos == 1:
            buy_close.append(df_candleStick["close"][-1])
            plRange = buy_close[-1] - buy_entry[-1]
            pl[-1] = pl[-2] + plRange * lot
            pos -= 1
            buyCloseSignals.append(df_candleStick.index[-1])
            nOfTrade += 1
            plPerTrade.append(plRange*lot)
        elif pos ==-1:
            sell_close.append(df_candleStick["close"][-1])
            plRange = sell_entry[-1] - sell_close[-1]
            pl[-1] = pl[-2] + plRange * lot
            pos +=1
            sellCloseSignals.append(df_candleStick.index[-1])
            nOfTrade += 1
            plPerTrade.append(plRange*lot)
        return (pl, buyEntrySignals, sellEntrySignals, buyCloseSignals, sellCloseSignals, nOfTrade, plPerTrade)

    def describeResult(self, entryTerm, closeTerm, fileName=None, candleTerm=None, rangeTh=5000, rangeTerm=15, originalWaitTerm=10, waitTh=10000, showFigure=True, cost=0):
        """
        signalsは買い，売り，中立が入った配列
        """
        import matplotlib.pyplot as plt
        if fileName == None:
            s_hour = 0
            s_min = 0
            e_hour = 23
            e_min = 59
            number = int((e_hour - s_hour)*60 + e_min - s_min)
            start_timestamp = datetime.datetime(2020, 1, 1, s_hour, s_min, 0, 0).timestamp()
            end_timestamp = datetime.datetime(2020, 7, 30, e_hour, e_min, 0, 0).timestamp()
            candleStick = self.getSpecifiedCandlestick(number, "14400", start_timestamp, end_timestamp)
        else:
            candleStick = self.readDataFromFile(fileName)

        if candleTerm != None:
            df_candleStick = self.processCandleStick(candleStick, candleTerm)
        else:
            df_candleStick = self.fromListToDF(candleStick)

        entryLowLine, entryHighLine = self.calculateLines(df_candleStick, entryTerm)
        closeLowLine, closeHighLine = self.calculateLines(df_candleStick, closeTerm)
        judgement = self.judge(df_candleStick, entryHighLine, entryLowLine, closeHighLine, closeLowLine, entryTerm)
        pl, buyEntrySignals, sellEntrySignals, buyCloseSignals, sellCloseSignals, nOfTrade, plPerTrade = self.backtest(judgement, df_candleStick, 1, rangeTh, rangeTerm, originalWaitTerm=originalWaitTerm, waitTh=waitTh, cost=cost)

        plt.figure()
        plt.subplot(211)
        plt.plot(df_candleStick.index, df_candleStick["high"])
        plt.plot(df_candleStick.index, df_candleStick["low"])
        plt.ylabel("Price(JPY)")
        ymin = min(df_candleStick["low"]) - 200
        ymax = max(df_candleStick["high"]) + 200
        plt.vlines(buyEntrySignals, ymin , ymax, "blue", linestyles='dashed', linewidth=1)
        plt.vlines(sellEntrySignals, ymin , ymax, "red", linestyles='dashed', linewidth=1)
        plt.vlines(buyCloseSignals, ymin , ymax, "black", linestyles='dashed', linewidth=1)
        plt.vlines(sellCloseSignals, ymin , ymax, "green", linestyles='dashed', linewidth=1)
        plt.subplot(212)
        plt.plot(df_candleStick.index, pl)
        plt.hlines(y=0, xmin=df_candleStick.index[0], xmax=df_candleStick.index[-1], colors='k', linestyles='dashed')
        plt.ylabel("PL(JPY)")

        #各統計量の計算および表示．
        winTrade = sum([1 for i in plPerTrade if i > 0])
        loseTrade = sum([1 for i in plPerTrade if i < 0])
        winPer = round(winTrade/(winTrade+loseTrade) * 100,2)

        winTotal = sum([i for i in plPerTrade if i > 0])
        loseTotal = sum([i for i in plPerTrade if i < 0])
        profitFactor = round(winTotal/-loseTotal, 3)

        maxProfit = max(plPerTrade)
        maxLoss = min(plPerTrade)

        print("Total pl: {}JPY".format(int(pl[-1])))
        print("The number of Trades: {}".format(nOfTrade))
        print("The Winning percentage: {}%".format(winPer))
        print("The profitFactor: {}".format(profitFactor))
        print("The maximum Profit and Loss: {}JPY, {}JPY".format(maxProfit, maxLoss))
        if showFigure:
            plt.show()
        else:
            plt.clf()
        return pl[-1], profitFactor

    def getCandlestick(self, number, period):
        """
        number:ローソク足の数．period:ローソク足の期間（文字列で秒数を指定，Ex:1分足なら"60"）．cryptowatchはときどきおかしなデータ（price=0）が含まれるのでそれを除く．
        """
        #ローソク足の時間を指定
        periods = [period]
        #クエリパラメータを指定
        query = {"periods":','.join(periods)}
        #ローソク足取得
        res = \
            json.loads(requests.get("https://api.cryptowat.ch/markets/bitflyer/btcfxjpy/ohlc", params=query).text)[
                "result"]
        # ローソク足のデータを入れる配列．
        data = []
        for i in periods:
            row = res[i]
            length = len(row)
            for column in row[:length - (number + 1):-1]:
                # dataへローソク足データを追加．
                if column[4] != 0:
                    column = column[0:6]
                    data.append(column)
        return data[::-1]


    def fromListToDF(self, candleStick):
        """
        Listのローソク足をpandasデータフレームへ．
        """
        date = [price[0] for price in candleStick]
        priceOpen = [int(price[1]) for price in candleStick]
        priceHigh = [int(price[2]) for price in candleStick]
        priceLow = [int(price[3]) for price in candleStick]
        priceClose = [int(price[4]) for price in candleStick]
        date_datetime = map(datetime.datetime.fromtimestamp, date)
        dti = pd.DatetimeIndex(date_datetime)
        df_candleStick = pd.DataFrame({"open" : priceOpen, "high" : priceHigh, "low": priceLow, "close" : priceClose}, index=dti)
        return df_candleStick

    def processCandleStick(self, candleStick, timeScale):
        """
        1分足データから各時間軸のデータを作成.timeScaleには5T（5分），H（1時間）などの文字列を入れる
        """
        df_candleStick = self.fromListToDF(candleStick)
        processed_candleStick = df_candleStick.resample(timeScale).agg({'open': 'first','high':'max','low': 'min','close': 'last'})
        processed_candleStick = processed_candleStick.dropna()
        return processed_candleStick

    #csvファイル（ヘッダなし）からohlcデータを作成．
    def readDataFromFile(self,filename):
        for i in range(1, 10, 1):
            with open(filename, 'r', encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader)
                for row in reader:
                    candleStick = [row for row in reader if row[4] != "0"]
        dtDate = [datetime.datetime.strptime(data[0], '%Y-%m-%d %H:%M:%S') for data in candleStick]
        dtTimeStamp = [dt.timestamp() for dt in dtDate]
        for i in range(len(candleStick)):
            candleStick[i][0] = dtTimeStamp[i]
        candleStick = [[float(i) for i in data] for data in candleStick]
        return candleStick

    def lineNotify(self, message, fileName=None):
        payload = {'message': message}
        headers = {'Authorization': 'Bearer ' + self.line_notify_token}
        if fileName == None:
            try:
                requests.post(self.line_notify_api, data=payload, headers=headers)
            except:
                pass
        else:
            try:
                files = {"imageFile": open(fileName, "rb")}
                requests.post(self.line_notify_api, data=payload, headers=headers, files = files)
            except:
                pass

    def describePLForNotification(self, pl, df_candleStick):
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        close = df_candleStick["close"]
        index = range(len(pl))
        # figure
        fig = plt.figure(figsize=(20,12))
        #for price
        ax = fig.add_subplot(2, 1, 1)
        ax.plot(df_candleStick.index, close)
        ax.set_xlabel('Time')
        # y axis
        ax.set_ylabel('The price[JPY]')
        #for PLcurve
        ax = fig.add_subplot(2, 1, 2)
        # plot
        ax.plot(index, pl, color='b', label='The PL curve')
        ax.plot(index, [0]*len(pl), color='b',)
        # x axis
        ax.set_xlabel('The number of Trade')
        # y axis
        ax.set_ylabel('The estimated Profit/Loss(JPY)')
        # legend and title
        ax.legend(loc='best')
        ax.set_title('The PL curve(Time span:{})'.format(self.candleTerm))
        # save as png
        today = datetime.datetime.now().strftime('%Y%m%d')
        number = "_" + str(len(pl))
        fileName = today + number + ".png"
        plt.savefig(fileName)
        plt.close()

        return fileName

    def loop(self,entryTerm, closeTerm, rangeTh, rangeTerm,originalWaitTerm, waitTh,candleTerm=None):
        """
        注文の実行ループを回す関数
        """
        pos = 0
        pl = []
        pl.append(0)
        lastPositionPrice = 0
        lot = self.lot
        originalLot = self.lot
        waitTerm = 0

        try:
            candleStick = self.getCandlestick(50, "60")
        except:
            print("Unknown error happend when you requested candleStick")
        if candleTerm == None:
            df_candleStick = self.fromListToDF(candleStick)
        else:
            df_candleStick = self.processCandleStick(candleStick, candleTerm)

        entryLowLine, entryHighLine = self.calculateLines(df_candleStick, entryTerm)
        closeLowLine, closeHighLine = self.calculateLines(df_candleStick, closeTerm)

        #直近約定件数30件の高値と安値
        high = max([self.executions[-1-i]["price"] for i in range(30)])
        low = min([self.executions[-1-i]["price"] for i in range(30)])

        while True:
            #1分ごとに基準ラインを更新
            if datetime.datetime.now().second < 2 :
                print("Renewing candleSticks")
                try:
                    candleStick = self.getCandlestick(50, "60")
                except:
                    print("Unknown error happend when you requested candleStick")
                if candleTerm == None:
                    df_candleStick = self.fromListToDF(candleStick)
                else:
                    df_candleStick = self.processCandleStick(candleStick, candleTerm)
                entryLowLine, entryHighLine = self.calculateLines(df_candleStick, entryTerm)
                closeLowLine, closeHighLine = self.calculateLines(df_candleStick, closeTerm)

            #直近約定件数30件の高値と安値
            high = max([self.executions[-1-i]["price"] for i in range(30)])
            low = min([self.executions[-1-i]["price"] for i in range(30)])

            judgement = self.judgeForLoop(high, low, entryHighLine, entryLowLine, closeHighLine, closeLowLine)
            #現在レンジ相場かどうか．
            isRange = self.isRange(df_candleStick, rangeTerm, rangeTh)

            try :
                ticker = self.api.ticker(product_code=self.product_code)
            except:
                print("Unknown error happend when you requested ticker.")
            finally:
                pass

            best_ask = ticker["best_ask"]
            best_bid = ticker["best_bid"]

            #ここからエントリー，クローズ処理
            if pos == 0 and not isRange[-1]:
                #ロングエントリー
                if judgement[0]:
                    print(datetime.datetime.now())
                    self.order.market(size=lot, side="BUY")
                    pos += 1
                    message = "Long entry. Lot:{}, Price:{}".format(lot, best_ask)
                    self.lineNotify(message)
                    lastPositionPrice = best_ask
                #ショートエントリー
                elif judgement[1]:
                    print(datetime.datetime.now())
                    self.order.market(size=lot,side="SELL")
                    pos -= 1
                    message = "Short entry. Lot:{}, Price:{}, ".format(lot, best_bid)
                    self.lineNotify(message)
                    lastPositionPrice = best_bid

            elif pos == 1:
                #ロングクローズ
                if judgement[2]:
                    print(datetime.datetime.now())
                    self.order.market(size=lot,side="SELL")
                    pos -= 1
                    plRange = best_bid - lastPositionPrice
                    pl.append(pl[-1] + plRange * lot)

                    message = "Long close. Lot:{}, Price:{}, pl:{}".format(lot, best_bid, pl[-1])
                    fileName = self.describePLForNotification(pl, df_candleStick)
                    self.lineNotify(message,fileName)

                    #一定以上の値幅を取った場合，次の10トレードはロットを1/10に落とす．
                    if plRange > waitTh:
                        waitTerm = originalWaitTerm
                        lot = round(originalLot/10,3)
                    elif waitTerm > 0:
                        waitTerm -= 1
                        lot = round(originalLot/10,3)
                    if waitTerm == 0:
                        lot = originalLot

            elif pos == -1:
                #ショートクローズ
                if judgement[3]:
                    print(datetime.datetime.now())
                    self.order.market(size=lot, side="BUY")
                    pos += 1
                    plRange = lastPositionPrice - best_ask
                    pl.append(pl[-1] + plRange * lot)

                    message = "Short close. Lot:{}, Price:{}, pl:{}".format(lot, best_ask, pl[-1])
                    fileName = self.describePLForNotification(pl, df_candleStick)
                    self.lineNotify(message,fileName)
                    #一定以上の値幅を取った場合，次の10トレードはロットを1/10に落とす．
                    if plRange > waitTh:
                        waitTerm = originalWaitTerm
                        lot = round(originalLot/10,3)
                    elif waitTerm > 0:
                        waitTerm -= 1
                        lot = round(originalLot/10,3)
                    if waitTerm == 0:
                        lot = originalLot

            time.sleep(0.5)
            message = "Waiting for channelbreaking."

            if datetime.datetime.now().minute % 5 == 0 and datetime.datetime.now().second < 1:
                print(message)
                self.lineNotify(message)

    def getSpecifiedCandlestick(self,number, period, start_timestamp, end_timestamp):
        """
        number:ローソク足の数．period:ローソク足の期間（文字列で秒数を指定，Ex:1分足なら"60"）．cryptowatchはときどきおかしなデータ（price=0）が含まれるのでそれを除く
        """
        # ローソク足の時間を指定
        periods = [period]
        # クエリパラメータを指定
        query = {"periods": ','.join(periods), "after": str(int(start_timestamp)), "before": str(int(end_timestamp))}
        # ローソク足取得
        try:
            res = json.loads(requests.get("https://api.cryptowat.ch/markets/bitflyer/btcfxjpy/ohlc", params=query).text)
            res = res["result"]
        except:
            print(res)
        # ローソク足のデータを入れる配列．
        data = []
        for i in periods:
            row = res[i]
            length = len(row)
            for column in row[:length - (number + 1):-1]:
                # dataへローソク足データを追加．
                if column[4] != 0:
                    column = column[0:6]
                    data.append(column)
        return data[::-1]

#注文処理をまとめている
class Order:
    def __init__(self):
        self.product_code = "FX_BTC_JPY"
        self.key = "your key"
        self.secret = "your secret"
        # self.api = pybitflyer.API(self.key, self.secret)

    def limit(self, side, price, size, minute_to_expire=None):
        print("Order: Limit. Side : {}".format(side))
        response = {"status":"internalError in order.py"}
        try:
            response = self.api.sendchildorder(product_code=self.product_code, child_order_type="LIMIT", side=side, price=price, size=size, minute_to_expire = minute_to_expire)
        except:
            pass
        while "status" in response:
            try:
                response = self.api.sendchildorder(product_code=self.product_code, child_order_type="LIMIT", side=side, price=price, size=size, minute_to_expire = minute_to_expire)
            except:
                pass
            time.sleep(3)
        return response

    def market(self, side, size, minute_to_expire= None):
        print("Order: Market. Side : {}".format(side))
        response = {"status": "internalError in order.py"}
        try:
            response = self.api.sendchildorder(product_code=self.product_code, child_order_type="MARKET", side=side, size=size, minute_to_expire = minute_to_expire)
        except:
            pass
        while "status" in response:
            try:
                response = self.api.sendchildorder(product_code=self.product_code, child_order_type="MARKET", side=side, size=size, minute_to_expire = minute_to_expire)
            except:
                pass
            time.sleep(3)
        return response

    def stop(self, side, size, trigger_price, minute_to_expire=None):
        print("Order: Stop. Side : {}".format(side))
        response = {"status": "internalError in order.py"}
        try:
            response = self.api.sendparentorder(order_method="SIMPLE", parameters=[{"product_code": self.product_code, "condition_type": "STOP", "side": side, "size": size,"trigger_price": trigger_price, "minute_to_expire": minute_to_expire}])
        except:
            pass
        while "status" in response:
            try:
                response = self.api.sendparentorder(order_method="SIMPLE", parameters=[{"product_code": self.product_code, "condition_type": "STOP", "side": side, "size": size,"trigger_price": trigger_price, "minute_to_expire": minute_to_expire}])
            except:
                pass
            time.sleep(3)
        return response

    def stop_limit(self, side, size, trigger_price, price, minute_to_expire=None):
        print("Side : {}".format(side))
        response = {"status": "internalError in order.py"}
        try:
            response = self.api.sendparentorder(order_method="SIMPLE", parameters=[{"product_code": self.product_code, "condition_type": "STOP_LIMIT", "side": side, "size": size,"trigger_price": trigger_price, "price": price, "minute_to_expire": minute_to_expire}])
        except:
            pass
        while "status" in response:
            try:
                response = self.api.sendparentorder(order_method="SIMPLE", parameters=[{"product_code": self.product_code, "condition_type": "STOP_LIMIT", "side": side, "size": size,"trigger_price": trigger_price, "price": price, "minute_to_expire": minute_to_expire}])
            except:
                pass
        return response

    def trailing(self, side, size, offset, minute_to_expire=None):
        print("Side : {}".format(side))
        response = {"status": "internalError in order.py"}
        try:
            response = self.api.sendparentorder(order_method="SIMPLE", parameters=[{"product_code": self.product_code, "condition_type": "TRAIL", "side": side, "size": size, "offset": offset, "minute_to_expire": minute_to_expire}])
        except:
            pass
        while "status" in response:
            try:
                response = self.api.sendparentorder(order_method="SIMPLE", parameters=[{"product_code": self.product_code, "condition_type": "TRAIL", "side": side, "size": size, "offset": offset, "minute_to_expire": minute_to_expire}])
            except:
                pass
        return response


def optimization():
    entryAndCloseTerm = [(5,3),(5,5),(10,10),(20,10)]
    rangeThAndrangeTerm = [(5000,5),(5000,15),(10000,15),(None,15),(None,20),(None,15)]
    waitTermAndwaitTh = [(10,10000),(10,20000),(5,10000)]

    paramList = []
    for i in entryAndCloseTerm:
        for j in rangeThAndrangeTerm:
            for k in waitTermAndwaitTh:
                channelBreakOut = ChannelBreakOut()
                channelBreakOut.entryTerm = i[0]
                channelBreakOut.closeTerm = i[1]
                channelBreakOut.rangeTh = j[0]
                channelBreakOut.rangeTerm = j[1]
                channelBreakOut.waitTerm = k[0]
                channelBreakOut.waitTh = k[1]
                channelBreakOut.candleTerm = "1T"
                #テスト
                pl, profitFactor =  channelBreakOut.describeResult(entryTerm=channelBreakOut.entryTerm, closeTerm=channelBreakOut.closeTerm, rangeTh=channelBreakOut.rangeTh, rangeTerm=channelBreakOut.rangeTerm,  originalWaitTerm=channelBreakOut.waitTerm, waitTh=channelBreakOut.waitTh, candleTerm=channelBreakOut.candleTerm,fileName="20180221_0310.csv", showFigure=False)
                paramList.append([pl,profitFactor, i,j,k])
    pF = [i[1] for i in paramList]
    pL = [i[0] for i in paramList]
    print("ProfitFactor max:")
    print(paramList[pF.index(max(pF))])
    print("PL max:")
    print(paramList[pL.index(max(pL))])

if __name__ == '__main__':
    #とりあえず5分足，5期間安値・高値でエントリー，クローズする設定
    channelBreakOut = ChannelBreakOut()
    channelBreakOut.entryTerm = 5
    channelBreakOut.closeTerm = 5
    channelBreakOut.rangeTh = None
    channelBreakOut.rangeTerm = None
    channelBreakOut.waitTerm = 0
    channelBreakOut.waitTh = 10000
    channelBreakOut.candleTerm = "5T"
    channelBreakOut.cost = 0

    #実働
    # channelBreakOut.loop(channelBreakOut.entryTerm, channelBreakOut.closeTerm, channelBreakOut.rangeTh, channelBreakOut.rangeTerm, channelBreakOut.waitTerm, channelBreakOut.waitTh)
    #バックテスト
    channelBreakOut.describeResult(entryTerm=channelBreakOut.entryTerm, closeTerm=channelBreakOut.closeTerm, rangeTh=channelBreakOut.rangeTh, rangeTerm=channelBreakOut.rangeTerm,  originalWaitTerm=channelBreakOut.waitTerm, waitTh=channelBreakOut.waitTh, candleTerm=channelBreakOut.candleTerm,showFigure=True, cost=channelBreakOut.cost)
    #最適化
    #optimization()