import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic
# from PyQt5.QtGui import *
from pandas import Series
import pybithumb
from asq.initiators import query
import Funcs_OBV
import os
import wave
import pygame
import time
import random
# from selenium import webdriver
import webbrowser


# ------ MUSIC LIST ------#
dir = './Music/'
Musiclist = os.listdir(dir)

# ----------- KEY SETTING -----------#
with open("Keys.txt") as f:
    lines = f.readlines()
    key = lines[0].strip()
    secret = lines[1].strip()
    bithumb = pybithumb.Bithumb(key, secret)

# ----------- UI SETTING -----------#
form = uic.loadUiType("Orderwindow.ui")[0]


class OrderWindow(QMainWindow, form):

    # Default Parameter
    Coin = 'BTC'
    display = 7
    Orderinfo = None
    krw = bithumb.get_balance(Coin)[2]
    buyunit_order = None
    Check = 0

    def __init__(self, candis, ratio):
        super().__init__()
        self.candis = candis
        self.ratio = ratio
        self.setupUi(self)
        self.setGeometry(10, 100, 715, 630)

        # 매수, 매도시 실시간 체결 출력
        self.timer_buy = QTimer(self)
        self.timer_sell = QTimer(self)

        # 후보 코인 출력
        self.candidates(self.candis, self.ratio)

        # Button
        self.pushButton_cancel.clicked.connect(lambda: self.cancel_clicked(self.Coin, self.Orderinfo))

        # 입력값 # 문자열 입력에 대한 에러처리를 해주어야한다.
        self.lineEdit_buy.returnPressed.connect(lambda: self.buy_clicked(self.Coin, self.display))
        self.lineEdit_sell.returnPressed.connect(lambda: self.sell_clicked(self.Coin, self.display))
        self.lineEdit_coin.returnPressed.connect(lambda: self.coin_clicked(self.candis, self.display))

    def buy_clicked(self, Coin, display):  # 엔터치면 매수 동작하는 걸로 가능? = returnPressed()
        print("매수 동작")

        # 매수 동작
        try:
            self.timer_buy.stop()
            self.timer_buy.start(1000)
            self.timer_buy.timeout.connect(lambda: self.hogachart(Coin))

            limit_buy_price = float(self.lineEdit_buy.text())
            Hogaunit = Funcs_OBV.GetHogaunit(limit_buy_price)
            limit_buy_price = Funcs_OBV.clearance(Hogaunit, limit_buy_price)

            # --------------- 매수 등록 ---------------#
            # 사용할 원화, 매수량
            if self.krw < 1000:
                print("거래 가능 원화가 부족합니다. %s KRW" % self.krw)
                self.lineEdit_status.setText("거래 가능 원화가 부족합니다.")
                print()
            buyunit = int((2000 / limit_buy_price) * 10000) / 10000.0

            # 매수 등록
            BuyOrder = bithumb.buy_limit_order(self.Coin, limit_buy_price, buyunit)
            print("##### 지정가 매수 등록 #####")
            self.lineEdit_status.setText("%s KRW에 매수 등록" % limit_buy_price)
            print(BuyOrder)
            self.buyunit_order = buyunit
            self.Check = 1

            # ----------------- 매수 에러 처리 -----------------#
            if type(BuyOrder) != tuple:
                if type(BuyOrder) == dict:
                    self.lineEdit_status.setText(BuyOrder['message'])
                else:
                    self.lineEdit_status.setText("BuyOrder == None")
                print()
            else:
                self.Orderinfo = BuyOrder
                # 실시간 매수, 체결량 확인
                self.timer_buy.timeout.connect(lambda: self.buy_check(Coin, display, BuyOrder))

        except Exception as e:
            self.lineEdit_status.setText(str(e))
            print(e)
            print()

    def sell_clicked(self, Coin, display):
        print("매도 동작")

        try:
            self.timer_buy.stop()
            self.timer_sell.stop()
            self.timer_sell.start(1000)
            self.timer_sell.timeout.connect(lambda: self.hogachart(Coin))

            # ---------------- 매도 등록 ----------------#
            limit_sell_price = float(self.lineEdit_sell.text())
            Hogaunit = Funcs_OBV.GetHogaunit(limit_sell_price)
            limit_sell_price = Funcs_OBV.clearance(Hogaunit, limit_sell_price)

            balance = bithumb.get_balance(Coin)
            sellunit = int((balance[0]) * 10000) / 10000.0
            SellOrder = bithumb.sell_limit_order(Coin, limit_sell_price, sellunit)
            print("##### 지정가 매도 등록 #####")
            print(SellOrder)
            self.Check = 1

            # ----------------- 매도 에러 처리 -----------------#
            if type(SellOrder) == tuple:
                self.lineEdit_status.setText("%s KRW에 매도 등록" % limit_sell_price)
                self.Orderinfo = SellOrder
                # 실시간 매도, 체결량 확인
                self.timer_sell.timeout.connect(lambda: self.sell_check(Coin, display, balance))

            else:  # dictionary or SellOrder = None
                if type(SellOrder) == dict:
                    self.lineEdit_status.setText(SellOrder['message'])
                else:
                    self.lineEdit_status.setText("SellOrder is None")

        except Exception as e:
            print("매도 등록 중 에러 발생!")
            self.lineEdit_status.setText(str(e))
            print(e)
            print()

    def buy_check(self, Coin, display, BuyOrder):

        # 실시간 체결량
        self.transaction_history(Coin, display)

        if self.Check == 1:

            try:
                # ------------ 매수 취소 또는 체결완료, 체결량 확인 ------------#
                balance = bithumb.get_balance(Coin)

                # 0.95 이상 체결되면 체결된거야
                if balance[0] / self.buyunit_order >= 0.95:
                    print("##### 매수 체결 #####")
                    message = "%.2f" % (self.buyunit_order / balance[0] * 100) + "% 매수 체결!"
                    self.lineEdit_status.setText(message)
                    CancelOrder = bithumb.cancel_order(BuyOrder)
                    print("부분 매수 체결 : ", CancelOrder)
                    print("체결량 : ", (self.buyunit_order / balance[0]), '%')
                    self.Check = 0
                    print()

                else:
                    # ------------ 매도 취소, 재등록 의사 확인 ------------#
                    print("체결량 %.2f" % ((balance[0] / self.buyunit_order) * 100), "% 입니다.")
                    message = "체결량 %.2f " % ((balance[0] / self.buyunit_order) * 100) + "% 입니다."
                    self.lineEdit_status.setText(message)

            except Exception as e:
                print('매수 체결 여부 확인중 에러 발생!')
                self.lineEdit_status.setText(str(e))
                print(e)
                print()

    def sell_check(self, Coin, display, balance):

        # 실시간 체결량
        self.transaction_history(Coin, display)

        if self.Check == 1:

            try:
                # 체결 여부 확인 로직
                ordersucceed = bithumb.get_balance(Coin)
                if ordersucceed[0] != balance[0] and ordersucceed[1] == 0.0:
                    print("##### 매도 체결 #####")
                    message = "매도 체결 Profits = %.6f" % (bithumb.get_balance(Coin)[2] / self.krw)
                    self.lineEdit_status.setText(message)
                    self.timer_sell.stop()
                    self.Check = 0
                else:
                    print("체결량 %.2f" % ((1 - ordersucceed[0] / balance[0]) * 100), "% 입니다.")
                    message = "체결량 %.2f " % ((1 - ordersucceed[0] / balance[0]) * 100) + "% 입니다."
                    self.lineEdit_status.setText(message)
                    print("매도 체결 대기중입니다.\n")

            except Exception as e:
                print('체결 여부 확인 중 에러 발생!\n')
                self.lineEdit_status.setText(str(e))
                print(e)
                print()

    def cancel_clicked(self, Coin, Orderinfo):
        print("주문 취소 동작")

        # 미체결, 체결 완료 정보를 받아서 매수/매도 주문 잔량을 모두 취소한다.
        try:
            CancelOrder = bithumb.cancel_order(Orderinfo)
            self.Check = 0
            print("주문 취소 : ", CancelOrder)

            remain = self.krw - bithumb.get_balance(Coin)[2]
            if remain <= 0:
                self.lineEdit_status.setText("주문 취소 | 거래해야할 원화 없음")
            else:
                self.lineEdit_status.setText("주문 취소 | 거래해야할 원화 : %.f KRW" % remain)
            print()

        except Exception as e:
            print("Error in cancel")
            self.lineEdit_status.setText(str(e))
            print(e)
            print()

    def coin_clicked(self, candis, display):
        print("코인 입력 동작")
        try:
            Coin_number = int(self.lineEdit_coin.text())
            self.Coin = candis[Coin_number - 1]
            self.lineEdit_status.setText("%s 코인 선택" % self.Coin)

            # 실시간 체결량 표시
            self.timer_buy.stop()
            self.timer_sell.stop()
            self.timer_buy.start(1000)
            self.timer_buy.timeout.connect(lambda: self.hogachart(self.Coin))
            self.timer_buy.timeout.connect(lambda: self.transaction_history(self.Coin, display))

        except Exception as e:
            self.lineEdit_status.setText(str(e))
            print("입력 오류!")
            print(e)
            print()

    def candidates(self, candis, ratio):

        try:
            for i in range(len(candis)):
                self.tableWidget_candis.setItem(i, 0, QTableWidgetItem(candis[i]))
                self.tableWidget_candis.setItem(i, 1, QTableWidgetItem(str(ratio[i])))

        except Exception as e:
            print("Error in candidates")
            print(e)
            print()

    def hogachart(self, Coin):

        try:
            display = 3
            Hogachart = pybithumb.get_orderbook(Coin)

            Realtime_asks_price = query(Hogachart['asks'][0:display]).select(lambda item: item['price']).to_list()
            Realtime_asks_volume = query(Hogachart['asks'][0:display]).select(lambda item: item['quantity']).to_list()
            Realtime_bids_price = query(Hogachart['bids'][0:display]).select(lambda item: item['price']).to_list()
            Realtime_bids_volume = query(Hogachart['bids'][0:display]).select(lambda item: item['quantity']).to_list()

            for i in range(display):
                self.tableWidget_hoga_ask.setItem(i, 0, QTableWidgetItem(str(Realtime_asks_price[display - 1 - i])))
                self.tableWidget_hoga_ask.setItem(i, 1, QTableWidgetItem(str(Realtime_asks_volume[display - 1 - i])))
                self.tableWidget_hoga_ask.setItem(i + 3, 0, QTableWidgetItem(str(Realtime_bids_price[i])))
                self.tableWidget_hoga_ask.setItem(i + 3, 1, QTableWidgetItem(str(Realtime_bids_volume[i])))

        except Exception as e:
            print("Error in hogachart")
            print(e)
            print()

    def transaction_history(self, Coin, display):

        try:
            # 상태 표시줄에 체결가 찍는 시간 표시하기
            current = QTime.currentTime()
            start = current.toString("hh:mm:ss")
            self.statusBar().showMessage(start)

            # lineEdit 에 표시할 체결 정보
            Transaction_history = pybithumb.transaction_history(Coin)
            Realtime = query(Transaction_history['data'][-display:]).select(lambda item: item['transaction_date'].split(' ')[1]).to_list()
            Realtime_Price = query(Transaction_history['data'][-display:]).select(lambda item: item['price']).to_list()
            Realtime_Volume = query(Transaction_history['data'][-display:]).select(lambda item: item['units_traded']).to_list()

            for i in range(display):
                self.tableWidget.setItem(i, 0, QTableWidgetItem(Realtime[display - 1 - i]))
                self.tableWidget.setItem(i, 1, QTableWidgetItem(Realtime_Price[display - 1 - i]))
                self.tableWidget.setItem(i, 2, QTableWidgetItem(Realtime_Volume[display - 1 - i]))

        except Exception as e:
            print("Error in t_history")
            print(e)
            print()


# ------ VALUE SET ------#
Volume_Ratio = 5
CoinVolume = 20
Resetcnt = 1
Coins = None

# ----- GUI SET ------#
app = QApplication(sys.argv)

while True:

    # ------- INPUT COIN -------#
    if Resetcnt == 1:
        Coinlist = pybithumb.get_tickers()  # 새로 찍어줘야함 ( 새로운 코인 탄생 )
        Fluclist = []  # 새로 찍을때만 초기화

        while True:
            try:
                for Coin in Coinlist:
                    tickerinfo = pybithumb.get_market_detail(Coin)
                    data = tickerinfo['data']
                    fluctate = data['fluctate_rate_24H']
                    Fluclist.append(fluctate)
                    time.sleep(1 / 90)
                break
            except Exception as e:
                Fluclist.append(None)
                print(e)

        Fluclist = list(map(float, Fluclist))
        series = Series(Fluclist, Coinlist)
        series = series.sort_values(ascending=False)

        # 선별할 코인 개수 : 상승장에 있는 코인들을 선별할 줄 알아야한다.
        series = series[0:CoinVolume]
        print(series)
        print()
        FamousCoin = list(series.index)

        # 한자리 미만 코인 처리
        for Coin in FamousCoin:
            try:
                if pybithumb.get_current_price(Coin) < 1:
                    FamousCoin.remove(Coin)

            except Exception as e:
                FamousCoin.remove(Coin)
                print(e)

        Coins = FamousCoin

    # ------------------ 상승률 좋은 인기 코인 추출 ------------------#

    # ------------------ 세력이 올라탄 코인 찾기 in Realtime ------------------#
    while True:
        try:
            candis, ratio = [], []

            start = time.time()
            while True:
                # 거래 조건 만족하는지 확인
                for Coin in Coins:
                    try:
                        temp = time.time()
                        Ratio = Funcs_OBV.realtime_volume_ratio(Coin)
                        print('%.2f seconds' % (time.time() - temp), Ratio)

                        if Ratio > Volume_Ratio:
                            candis.append(Coin)
                            ratio.append(Ratio)

                    # 보통 Devision by Zero
                    except Exception as e:
                        pass

                # 후보 코인 추출
                if len(candis) != 0:
                    break

                # TIMEOUT
                if time.time() - start > 60 * 30:
                    break
            Resetcnt = 1
            break

        except Exception as e:
            print("세력이 진입한 코인 찾는 중 에러 발생!")
            print(e)

    # 후보가 존재하면
    if len(candis) != 0:

        # ------ ALARM SET ------#
        SoundFile = './Music/{}.wav'.format(random.randrange(1, len(Musiclist) + 1))
        Wave = wave.open(SoundFile)
        frequency = Wave.getframerate()
        pygame.mixer.init(frequency=frequency)
        audio_volume = 1
        sound = pygame.mixer.Sound(SoundFile)
        sound.set_volume(audio_volume)
        sound.play()
        print()

        # ------ COIN STATUS CHART ------#
        i = 1
        print("##### 후보 코인 #####")
        for Coin in candis:
            CoinStatus = 'https://www.bithumb.com/trade/status/{}_KRW'.format(Coin)
            webbrowser.open(CoinStatus)
            print("%s. %s %.2f" % (i, Coin, ratio[i - 1]))
            i += 1
        print()
        ratio = list(map(lambda x: int(x * 10000) / 10000.0, ratio))

        window = OrderWindow(candis, ratio)
        window.show()
        app.exec_()

        # 거래 포기 / 매도 체결시
        sound.stop()
        for Coin in candis:
            Coins.remove(Coin)
        Resetcnt += 1
        if Resetcnt > 5:
            Resetcnt = 1




