## Bithumb_ordertool
using pybithumb, simply coded ordering GUI with PyQt5

## Intro
빗썸 페이지에서 거래만을 위한 페이지가 차트 페이지와 별개로 있어 주문시 불편함을 느낀다. 이를 해결하기 위해 PyQT GUI를 활용하였다. 실시간 체결량, 거래량, 호가창을 동일하게 제공한다.

## Description
거래창 제공과 더불어 개인이 지정한 알고리즘을 토대로 후보 종목(코인)이 선정된 경우 사용자에게 알림음을 주는 방식을 도입하였다. 

Real_PyQt.py : PyQT를 사용해 UI를 띄워주는 파일 / 자세한 설명은 코드 주석 확인
Funcs_OBV.py : 거래 알고리즘을 사용하기 위해 필요한 데이터를 실시간으로 bithumb으로부터 웹크롤링해 가져온다. 부가적인 함수들 (실시간 체결 데이터 함수, 거래량, 호가창, etc.) 또한 포함되어있다.


## Result
![image](https://user-images.githubusercontent.com/50652715/81031266-a6b88200-8ec6-11ea-9bcf-9637e74e6f22.png)
