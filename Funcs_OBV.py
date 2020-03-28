import pybithumb
import numpy as np
import pandas as pd
from datetime import datetime
import os
from scipy import stats
from asq.initiators import query


def realtime_transaction(Coin, display=5):
    Transaction_history = pybithumb.transaction_history(Coin)
    Realtime = query(Transaction_history['data'][-display:]).select(lambda item: item['transaction_date'].split(' ')[1]).to_list()
    Realtime_Price = list(map(float,query(Transaction_history['data'][-display:]).select(lambda item: item['price']).to_list()))
    Realtime_Volume = list(map(float,query(Transaction_history['data'][-display:]).select(lambda item: item['units_traded']).to_list()))

    print("##### 실시간 체결 #####")
    print("{:^10} {:^10} {:^20}".format('시간', '가격', '거래량'))
    for i in reversed(range(display)):
        print("%-10s %10.2f %20.3f" % (Realtime[i], Realtime_Price[i], Realtime_Volume[i]))
    return


def realtime_hogachart(Coin, display=3):
    Hogachart = pybithumb.get_orderbook(Coin)

    print("##### 실시간 호가창 #####")
    print("{:^10} {:^20}".format('가격', '거래량'))
    for i in reversed(range(display)):
        print("%10.2f %20.3f" % (Hogachart['asks'][i]['price'], Hogachart['asks'][i]['quantity']))
    print('-' * 30)
    for j in range(display):
        print("%10.2f %20.3f" % (Hogachart['bids'][j]['price'], Hogachart['bids'][j]['quantity']))


def realtime_volume(Coin):
    Transaction_history = pybithumb.transaction_history(Coin)
    Realtime_Volume = query(Transaction_history['data']).where(lambda item: item['type'] == 'bid').select(lambda item: item['units_traded']).to_list()
    Realtime_Volume = sum(list(map(float, Realtime_Volume)))
    return Realtime_Volume


def realtime_volume_ratio(Coin):
    Transaction_history = pybithumb.transaction_history(Coin)
    Realtime_bid = query(Transaction_history['data']).where(lambda item: item['type'] == 'bid').select(lambda item: item['units_traded']).to_list()
    Realtime_ask = query(Transaction_history['data']).where(lambda item: item['type'] == 'ask').select(lambda item: item['units_traded']).to_list()
    Realtime_bid = sum(list(map(float, Realtime_bid)))
    Realtime_ask = sum(list(map(float, Realtime_ask)))
    Realtime_Volume_Ratio = Realtime_bid / Realtime_ask
    return Realtime_Volume_Ratio


def topcoinlist(Date):
    temp = []
    dir = 'C:/Users/장재원/OneDrive/Hacking/CoinBot/ohlcv/'
    ohlcv_list = os.listdir(dir)

    for file in ohlcv_list:
        if file.find(Date) is not -1:  # 해당 파일이면 temp[i] 에 넣겠다.
            filename = os.path.splitext(file)
            temp.append(filename[0].split(" ")[1])
    return temp


# 상향 하향 매도 결정 함수 선언
def checkswitch(currentprice, price):

    if currentprice >= price:
        switch = 1
    else:
        switch = 0
    return switch


def get_ma_min(Coin):

    df = pybithumb.get_ohlcv(Coin, 'minute1')

    df['MA20'] = df['close'].rolling(20).mean()

    DatetimeIndex = df.axes[0]
    period = 20
    if inthour(DatetimeIndex[-1]) - inthour(DatetimeIndex[-period]) < 0:
        if 60 - (intmin(DatetimeIndex[-1]) - intmin(DatetimeIndex[-period])) > 30:
            return 0
    elif 60 * (inthour(DatetimeIndex[-1]) - inthour(DatetimeIndex[-period])) + intmin(DatetimeIndex[-1]) - intmin(
            DatetimeIndex[-period]) > 30:
        return 0
    slope, intercept, r_value, p_value, stderr = stats.linregress([i for i in range(period)], df.MA20[-period:])

    return slope


def get_ma2_min(Coin):

    df = pybithumb.get_ohlcv(Coin, 'minute1')

    df['MA20'] = df['close'].rolling(20).mean()

    period = 5
    slope, intercept, r_value, p_value, stderr = stats.linregress([i for i in range(period)], df.MA20[-period:])

    return slope


def get_obv_min(Coin):

    df = pybithumb.get_ohlcv(Coin, interval="minute1")

    obv = [0] * len(df.index)
    for m in range(1, len(df.index)):
        if df['close'].iloc[m] > df['close'].iloc[m - 1]:
            obv[m] = obv[m - 1] + df['volume'].iloc[m]
        elif df['close'].iloc[m] == df['close'].iloc[m - 1]:
            obv[m] = obv[m - 1]
        else:
            obv[m] = obv[m - 1] - df['volume'].iloc[m]
    df['OBV'] = obv

    # 24시간의 obv를 잘라서 box 높이를 만들어주어야한다.
    DatetimeIndex = df.axes[0]
    boxheight = [0] * len(df.index)
    whaleincome = [0] * len(df.index)
    for m in range(len(df.index)):
        # 24시간 시작행 찾기, obv 데이터가 없으면 stop
        n = m
        while True:
            n -= 1
            if n < 0:
                n = 0
                break
            if inthour(DatetimeIndex[m]) - inthour(DatetimeIndex[n]) < 0:
                if 60 - (intmin(DatetimeIndex[m]) - intmin(DatetimeIndex[n])) >= 60 * 24:
                    break
            elif 60 * (inthour(DatetimeIndex[m]) - inthour(DatetimeIndex[n])) + intmin(DatetimeIndex[m]) - intmin(
                    DatetimeIndex[n]) >= 60 * 24:
                break
        obv_trim = obv[n:m]
        if len(obv_trim) != 0:
            boxheight[m] = max(obv_trim) - min(obv_trim)
            if obv[m] - min(obv_trim) != 0:
                whaleincome[m] = abs(max(obv_trim) - obv[m]) / abs(obv[m] - min(obv_trim))

    df['BoxHeight'] = boxheight
    df['Whaleincome'] = whaleincome

    period = 0
    while True:
        period += 1
        if period >= len(DatetimeIndex):
            break
        if inthour(DatetimeIndex[-1]) - inthour(DatetimeIndex[-period]) < 0:
            if 60 - (intmin(DatetimeIndex[-1]) - intmin(DatetimeIndex[-period])) >= 10:
                break
        elif 60 * (inthour(DatetimeIndex[-1]) - inthour(DatetimeIndex[-period])) + intmin(DatetimeIndex[-1]) - intmin(
                DatetimeIndex[-period]) >= 10:
            break

    slope, intercept, r_value, p_value, stderr = stats.linregress([i for i in range(period)], df.OBV[-period:])
    if period < 3:
        df['Whaleincome'].iloc[-1], slope = 0, 0
    else:
        slope = slope / df['BoxHeight'].iloc[-1]

    return df['Whaleincome'].iloc[-1], slope


# def get_ohlcv_min_proxy(Coin):
#
#     df = pybithumb.get_ohlcv_proxy(Coin, "minute1")
#
#     obv = [0] * len(df.index)
#     for m in range(1, len(df.index)):
#         if df['close'].iloc[m] > df['close'].iloc[m - 1]:
#             obv[m] = obv[m - 1] + df['volume'].iloc[m]
#         elif df['close'].iloc[m] == df['close'].iloc[m - 1]:
#             obv[m] = obv[m - 1]
#         else:
#             obv[m] = obv[m - 1] - df['volume'].iloc[m]
#     df['OBV'] = obv
#
#     # 24시간의 obv를 잘라서 box 높이를 만들어주어야한다.
#     DatetimeIndex = df.axes[0]
#     boxheight = [0] * len(df.index)
#     whaleincome = [0] * len(df.index)
#     for m in range(len(df.index)):
#         # 24시간 시작행 찾기, obv 데이터가 없으면 stop
#         n = m
#         while True:
#             n -= 1
#             if n < 0:
#                 n = 0
#                 break
#             if 60 * (inthour(DatetimeIndex[m]) - inthour(DatetimeIndex[n])) + intmin(DatetimeIndex[m]) - intmin(
#                     DatetimeIndex[n]) >= 60 * 24:
#                 break
#         obv_trim = obv[n:m]
#         if len(obv_trim) != 0:
#             boxheight[m] = max(obv_trim) - min(obv_trim)
#             if obv[m] - min(obv_trim) != 0:
#                 whaleincome[m] = (max(obv_trim) - obv[m]) / (obv[m] - min(obv_trim))
#
#     df['BoxHeight'] = boxheight
#     df['Whaleincome'] = whaleincome
#     df['OBVGap'] = np.where(df['Whaleincome'] > 3, (df['OBV'] - df['OBV'].shift(1)) / df['BoxHeight'], np.nan)
#
#     return df['OBVGap']


def clearance(Hogaunit, price):

    Htype = type(Hogaunit)
    if Hogaunit == 0.1:
        price2 = int(price * 10) / 10.0
    elif Hogaunit == 0.01:
        price2 = round(price * 100, 0) / 100.0
        print(price2)
    else:
        return int(price) // Hogaunit * Hogaunit
    return Htype(price2)


def GetHogaunit(Hoga):

    if Hoga >= 1 and Hoga < 10:
        Hogaunit = 0.01
    elif Hoga >= 10 and Hoga < 100:
        Hogaunit = 0.1
    elif Hoga >= 100 and Hoga < 1000:
        Hogaunit = 1
    elif Hoga >= 1000 and Hoga < 5000:
        Hogaunit = 1
    elif Hoga >= 5000 and Hoga < 10000:
        Hogaunit = 5
    elif Hoga >= 10000 and Hoga < 50000:
        Hogaunit = 10
    elif Hoga >= 50000 and Hoga < 100000:
        Hogaunit = 50
    elif Hoga >= 100000 and Hoga < 500000:
        Hogaunit = 100
    elif Hoga >= 500000 and Hoga < 1000000:
        Hogaunit = 500
    else:
        Hogaunit = 1000
    return Hogaunit


def inthour(date):
    date = str(date)
    date = date.split(' ')
    hour = int(date[1].split(':')[0]) # 시
    return hour


def intmin(date):
    date = str(date)
    date = date.split(' ')
    min = int(date[1].split(':')[1]) # 분
    return min


# def profitage(Coin, Range1, Range2, Spk, VR, Slope1=0.01, Slope2=0.05, Date ='2019-09-25', excel=0, capturemin=3):
#
#     df = pd.read_excel('C:/Users/Lenovo/OneDrive/Hacking/CoinBot/ohlcv/%s %s ohlcv.xlsx' % (Date, Coin))
#     # df = pd.read_excel('C:/Users/Lenovo/OneDrive/Hacking/CoinBot/ohlcv_trim/%s %s ohlcv.xlsx' % (Date, Coin))
#     df = df.set_index(Coin)  # 엑셀로 인한 인덱스 재배열 제거
#
#     df['MA3'] = df['close'].rolling(3).mean()
#
#     obv = [0] * len(df.index)
#     for m in range(1, len(df.index)):
#         if df['close'].iloc[m] > df['close'].iloc[m - 1]:
#             obv[m] = obv[m - 1] + df['volume'].iloc[m]
#         elif df['close'].iloc[m] == df['close'].iloc[m - 1]:
#             obv[m] = obv[m - 1]
#         else:
#             obv[m] = obv[m - 1] - df['volume'].iloc[m]
#     df['OBV'] = obv
#
#     vr = [None] * len(df.index)
#     vrterm = 25
#     up, down = 0, 0
#     for m in range((vrterm - 1), len(df.index)):
#         for n in range(m - (vrterm - 1), m + 1):
#             if df['close'].iloc[n] > df['close'].iloc[n - 1]:
#                 up += df['volume'].iloc[m]
#             elif df['close'].iloc[n] == df['close'].iloc[n - 1]:
#                 up += df['volume'].iloc[m]
#                 down += df['volume'].iloc[m]
#             else:
#                 down += df['volume'].iloc[m]
#         vr[m] = up / down * 100
#     df['VR'] = vr
#
#     # 24시간의 obv를 잘라서 box 높이를 만들어주어야한다.
#     DatetimeIndex = df.axes[0]
#     boxheight = [0] * len(df.index)
#     for m in range(len(df.index)):
#         # 24시간 시작행 찾기, obv 데이터가 없으면 stop
#         n = m
#         while True:
#             n -= 1
#             if n < 0:
#                 n = 0
#                 break
#             if 60 * (inthour(DatetimeIndex[m]) - inthour(DatetimeIndex[n])) + intmin(DatetimeIndex[m]) - intmin(DatetimeIndex[n]) >= 60 * 24:
#                 break
#         obv_trim = obv[n:m]
#         if len(obv_trim) != 0:
#             boxheight[m] = max(obv_trim) - min(obv_trim)
#     df['BoxHeight'] = boxheight
#
#     df['OBVGap'] = (df['OBV'] - df['OBV'].shift(2)) / df['BoxHeight']
#
#     # 날짜로 자르기
#     df = df[Date]
#
#     # 매수선
#     df['BuyPrice'] = np.where((df['OBVGap'].shift(2) < Range1) & (df['OBVGap'].shift(1) >= Range2) & (df['VR'].shift(1) <= VR), df['currentMA2'], np.nan)
#
#     # 거래 수수료
#     fee = 0.005
#
#     DatetimeIndex = df.axes[0]
#     # ------------------- 여기까지 df 완성 -------------------#
#
#     # ------------------- 상향 / 하향 매도 여부와 이익률 계산 -------------------#
#
#     # high 가 SPP 를 건드리거나, low 가 SPM 을 건드리면 매도 체결 [ 매도 체결될 때까지 SPP 와 SPM 은 유지 !! ]
#     length = len(df.index) - 1  # 데이터 갯수 = 1, m = 0  >> 데이터 갯수가 100 개면 m 번호는 99 까지 ( 1 - 100 )
#
#     # 병합할 dataframe 초기화
#     dfsp = pd.DataFrame(index=DatetimeIndex, columns=['SPP'])
#     dfsm = pd.DataFrame(index=DatetimeIndex, columns=['SPM'])
#     condition = pd.DataFrame(index=DatetimeIndex, columns=["Condition"])
#     Profits = pd.DataFrame(index=DatetimeIndex, columns=["Profits"])
#     # rgrelay = pd.DataFrame(index=DatetimeIndex, columns=['rgrelay'])
#     bprelay = pd.DataFrame(index=DatetimeIndex, columns=['bprelay'])
#
#     Profits.Profits = 1.0
#
#     # 오더라인과 매수가가 정해진 곳에서부터 일정시간까지 오더라인과 매수가를 만족할 때까지 대기  >> 일정시간,
#     m = 0
#     while m <= length:
#         df2 = df.iloc[m]
#         while True:  # bp 찾기
#             if pd.notnull(df2['BuyPrice']):
#                 break
#             m += 1
#             if m > length:
#                 break
#
#             df2 = df.iloc[m]
#
#         if (m > length) or pd.isnull(df2['BuyPrice']):
#             break
#
#         # 어떤 매수가를 사용하냐에 따라 호가단위를 써서는 안되는경우가 존재한다.
#         Hogaunit = GetHogaunit(df2['BuyPrice'])
#         bp = df2['BuyPrice'] // Hogaunit * Hogaunit
#
#         # Regression
#         period = 10
#         if m >= period:
#             if pd.isnull(df.VR[m - period]):
#                 m += 1
#                 continue
#             slope, intercept, r_value, p_value, stderr = stats.linregress([i for i in range(period)], df.VR[m - period:m])
#             if slope < Slope1:
#                 m += 1
#                 continue
#
#         # 매수 신호 포착 완료 -----------------------------#
#
#         starthour, startmin = inthour(DatetimeIndex[m]), intmin(DatetimeIndex[m])
#         Smk = 0
#         while True:
#             bprelay["bprelay"].iloc[m] = bp
#
#             if df['low'].iloc[m] - 0.001 <= (bprelay["bprelay"].iloc[m]):
#                 Hogaunit = GetHogaunit(bp * Spk)
#                 dfsp.iloc[m] = bp * Spk // Hogaunit * Hogaunit
#                 Hogaunit = GetHogaunit(bp * Smk)
#                 dfsm.iloc[m] = bp * Smk // Hogaunit * Hogaunit
#                 m += 1
#                 break
#             else:
#                 m += 1
#                 if m > length or 60 * (inthour(DatetimeIndex[m]) - starthour) + intmin(
#                         DatetimeIndex[m]) - startmin >= capturemin:
#                     break
#                 dfsp.iloc[m] = 'capturing..'
#                 dfsm.iloc[m] = 'capturing..'
#                 bprelay["bprelay"].iloc[m] = bprelay["bprelay"].iloc[m - 1]
#                 if (df['low'].iloc[m] - 0.001 > (bprelay["bprelay"].iloc[m])) and (df['high'].iloc[m - 1] < bprelay["bprelay"].iloc[m]):
#                     Hogaunit = GetHogaunit(bp * Spk)
#                     dfsp.iloc[m] = bp * Spk // Hogaunit * Hogaunit
#                     Hogaunit = GetHogaunit(bp * Smk)
#                     dfsm.iloc[m] = bp * Smk // Hogaunit * Hogaunit
#                     m += 1
#                     break
#
#     # df = pd.merge(df, bprelay, how='outer', left_index=True, right_index=True)
#     df = pd.merge(df, dfsp, how='outer', left_index=True, right_index=True)
#     df = pd.merge(df, dfsm, how='outer', left_index=True, right_index=True)
#
#     # if excel == 1:
#     #     df.to_excel("./Check/%s Check_%s.xlsx" % (Date, Coin))
# # ----------------------- 매수가 체결되면 sp, sm 가 형성됨 ---------------------------------------------#
#
# # ----------------------- 제 2 장, 수익 검사 실시 ---------------------------------------------#
#
#     m = 0
#     while m <= length:  # 초반 시작포인트 찾기
#         wait = 0
#         df2 = df.iloc[m]
#         while True: # SPP 와 SPM 찾긴
#             if pd.notnull(df2['SPP']) and type(df2['SPP']) != str: # null 이 아니라는 건 오더라인과 매수가로 캡쳐했다는 거
#                 break
#             m += 1
#             if m > length: # 차트가 끊나는 경우, 만족하는 spp, spm 이 없는 경우
#                 break
#
#             df2 = df.iloc[m]
#         if (m > length) or pd.isnull(df2['SPP']):
#             break
#         spp, spm = df2['SPP'], df2['SPM']
#         # 존재하는 SPP, SPM, 추출 완료 -----------------------------#
#
#         # Detailed Profitage ------------------- 매도 체결 종류 --------------------------#
#         try:
#             if ((spp - 0.001) <= df2['high']) or (spm > df2['low']):
#                 # 시가가 spp 이상일 때
#                 if df2['open'] >= spp:
#                     if df2['open'] < df2['close']:  # 양봉인 경우
#                         if df2['low'] < spm:
#                             condition.iloc[m] = "하향 매도"
#                             Profits.iloc[m] = df.iloc[m].low / bprelay["bprelay"].iloc[m] - fee
#                         else:
#                             condition.iloc[m] = "상향 매도"
#                             Profits.iloc[m] = spp / bprelay["bprelay"].iloc[m] - fee
#
#                     else: # 음봉인 경우
#                         if df2['close'] >= spp:
#                             if df2['low'] < spm:
#                                 condition.iloc[m] = "하향 매도"
#                                 Profits.iloc[m] = df.iloc[m].low / bprelay["bprelay"].iloc[m] - fee
#                             else:
#                                 condition.iloc[m] = "상향 매도"
#                                 Profits.iloc[m] = spp / bprelay["bprelay"].iloc[m] - fee
#                         else: # waiting
#                             if df2['low'] < spm:
#                                 condition.iloc[m] = "하향 매도"
#                                 Profits.iloc[m] = df.iloc[m].low / bprelay["bprelay"].iloc[m] - fee
#                             else:
#                                 m += 1
#                                 if m > length:
#                                     break
#                                 condition.iloc[m] = 'waiting..'
#                                 bprelay["bprelay"].iloc[m] = bprelay["bprelay"].iloc[m - 1]
#                                 df2 = df.iloc[m]
#                                 wait = 1 # while 로 돌아갈때 영향을 주니까
#
#                 # 시가가 bp 초과 spp 미만
#                 elif (df2['open'] < spp) & (df2['open'] > bprelay['bprelay'].iloc[m]):
#                     if df2['open'] < df2['close']:  # 양봉인 경우]
#                         if df2['low'] < spm:
#                             condition.iloc[m] = "하향 매도"
#                             Profits.iloc[m] = df.iloc[m].low / bprelay["bprelay"].iloc[m] - fee
#                         else:
#                             condition.iloc[m] = "상향 매도"
#                             Profits.iloc[m] = spp / bprelay["bprelay"].iloc[m] - fee
#
#                     else: # 음봉인 경우
#                         if df2['low'] < spm:
#                             condition.iloc[m] = "하향 매도"
#                             Profits.iloc[m] = df.iloc[m].low / bprelay["bprelay"].iloc[m] - fee
#                         else:
#                             m += 1
#                             if m > length:
#                                 break
#                             condition.iloc[m] = 'waiting..'
#                             bprelay["bprelay"].iloc[m] = bprelay["bprelay"].iloc[m - 1]
#                             df2 = df.iloc[m]
#                             wait = 1 # while 로 돌아갈때 영향을 주니까
#
#                 # 시가가 bp 이하 spm 이상
#                 elif (df2['open'] <= (bprelay["bprelay"].iloc[m])) & (df2['open'] >= spm):
#                     if df2['open'] < df2['close']:  # 양봉인 경우
#                         if df2['high'] >= spp:
#                             condition.iloc[m] = "상향 매도"
#                             Profits.iloc[m] = spp / bprelay["bprelay"].iloc[m] - fee
#                         else:
#                             m += 1
#                             if m > length:
#                                 break
#                             condition.iloc[m] = 'waiting..'
#                             bprelay["bprelay"].iloc[m] = bprelay["bprelay"].iloc[m - 1]
#                             df2 = df.iloc[m]
#                             wait = 1  # while 로 돌아갈때 영향을 주니까
#
#                     else:  # 음봉인 경우
#                         if df2['low'] < spm:
#                             if df2['high'] >= spp:
#                                 condition.iloc[m] = "상향 매도"
#                                 Profits.iloc[m] = spp / bprelay["bprelay"].iloc[m] - fee
#                             else:
#                                 condition.iloc[m] = "하향 매도"
#                                 Profits.iloc[m] = df.iloc[m].low / bprelay["bprelay"].iloc[m] - fee
#
#                         else:
#                             condition.iloc[m] = "상향 매도"
#                             Profits.iloc[m] = spp / bprelay["bprelay"].iloc[m] - fee
#
#                 # 시가가 spm 미만
#                 else:
#                     if df2['open'] < df2['close']:  # 양봉인 경우
#                         if df2['close'] < spm:
#                             if df2['high'] >= spp:
#                                 condition.iloc[m] = "상향 매도"
#                                 Profits.iloc[m] = spp / bprelay["bprelay"].iloc[m] - fee
#                             else:
#                                 condition.iloc[m] = "하향 매도"
#                                 Profits.iloc[m] = df.iloc[m].low / bprelay["bprelay"].iloc[m] - fee
#
#                         else:
#                             if df2['high'] >= spp:
#                                 condition.iloc[m] = "상향 매도"
#                                 Profits.iloc[m] = spp / bprelay["bprelay"].iloc[m] - fee
#                             else:
#                                 m += 1
#                                 if m > length:
#                                     break
#                                 condition.iloc[m] = 'waiting..'
#                                 bprelay["bprelay"].iloc[m] = bprelay["bprelay"].iloc[m - 1]
#                                 df2 = df.iloc[m]
#                                 wait = 1 # while 로 돌아갈때 영향을 주니까\
#
#                     else:  # 음봉인 경우
#                         if df2['high'] >= spp:
#                             condition.iloc[m] = "상향 매도"
#                             Profits.iloc[m] = spp / bprelay["bprelay"].iloc[m] - fee
#                         else:
#                             condition.iloc[m] = "하향 매도"
#                             Profits.iloc[m] = df.iloc[m].low / bprelay["bprelay"].iloc[m] - fee
#
#             else:
#                 m += 1
#                 if m > length:
#                     break
#                 condition.iloc[m] = 'waiting..'
#                 bprelay["bprelay"].iloc[m] = bprelay["bprelay"].iloc[m - 1]
#                 df2 = df.iloc[m]
#                 wait = 1
#
#         except Exception as e:
#             print("매도 분별중 에러발생 %s %s " % (m, bprelay["bprelay"].iloc[m]))
#             pass
#
#         if float(Profits.iloc[m]) < 1.0:
#             print(Coin, Date, Profits.iloc[m])
#
#         if wait != 1: # 체결된 것들은 처음으로 / waiting 하는 봉들만 계속 진행
#             m += 1
#             continue
#
#         while True:
#
#             # 매도 체결 조건
#
#             # Regression
#             period = 10
#             if m >= period:
#                 if pd.isnull(df.VR[m - period]):
#                     m += 1
#                     continue
#                 slope, intercept, r_value, p_value, stderr = stats.linregress([i for i in range(period)], df.VR[m - period:m])
#                 if slope < Slope2:
#                     break
#
#             # 상향 매도 조건
#             if (spp - 0.001) <= df2['high']:
#                 break
#
#             m += 1
#             if m > length:
#                 break
#             # m 값과 df2 값을 모은다음에 또 다른 dateframe 에 붙이고 모든 과정이 끝나면 원본에 삽입.
#             condition.iloc[m] = 'waiting..'
#             if m == length:
#                 print(Coin, Date, 'wait until the end')
#             bprelay["bprelay"].iloc[m] = bprelay["bprelay"].iloc[m - 1]
#             df2 = df.iloc[m]  # while 로 돌아갈때 영향을 주니까
#
#         if m > length:
#             break
#
#         if (spp - 0.001) <= df2['high']:
#             condition.iloc[m] = "상향 매도"
#             Profits.iloc[m] = spp / bprelay["bprelay"].iloc[m - 1] - fee
#
#         if slope < Slope2:
#             condition.iloc[m] = "VR 매도"
#             Profits.iloc[m] = df['open'].iloc[m] / bprelay["bprelay"].iloc[m - 1] - fee
#
#             if float(Profits.iloc[m]) < 1.0:
#                 print(Coin, Date, Profits.iloc[m])
#
#         # 체결시 재시작
#         m += 1
#
#     df = pd.merge(df, bprelay, how='outer', left_index=True, right_index=True)
#     df = pd.merge(df, condition, how='outer', left_index=True, right_index=True)
#     df = pd.merge(df, Profits, how='outer', left_index=True, right_index=True)
#
#     # del df['volume']
#     del df['MA2']
#     del df['OBV']
#     del df['BoxHeight']
#     # del df['currentMA2']
#
#     if excel == 1:
#         df.to_excel("./Check/%s Check_%s.xlsx" % (Date, Coin))
#
#     profits = Profits.cumprod()  # 해당 열까지의 누적 곱!
#     return profits.iloc[-1]
#
#
# if __name__=="__main__":
#     # Best Value #########################################################
#     Date = '2019-11-19'  # Checkpoint # Checkpoint# Checkpoint# Checkpoint# Checkpoint
#     Coin = 'FCT'
#     get_ohlcv_min(Coin)
#     Range1, Range2, Spk, VR, Slope1, Slope2 = 0.05, 0.1, 1.015, 110, 0.3, -0.05
#     ######################################################################
#     print(profitage(Coin, Range1, Range2, Spk, VR, Slope1, Slope2, Date, 1))