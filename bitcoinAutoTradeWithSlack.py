import time
import pyupbit
import datetime
import requests

access = "FalkzhtP5xxwmqIm3xnnInSQWelQOR2xml6g48xf"
secret = "Y3nwdG4s0ONwq0KWKsnHBInzW8qoN3kk7cXxkROV"
myToken = "xoxb-2658800286528-2658805939328-rg9gUA3fprXGWzBYvvGqunhl"


def post_message(token, channel, text):
    """슬랙 메시지 전송"""
    response = requests.post("https://slack.com/api/chat.postMessage",
        headers={"Authorization": "Bearer "+token},
        data={"channel": channel,"text": text}
    )


def get_target_price(ticker, k):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
    return target_price


def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    start_time = df.index[0]
    return start_time


def get_ma5(ticker):
    """5일 이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=15)
    ma5 = df['close'].rolling(5).mean().iloc[-1]
    return ma5


def get_balance(ticker):
    """잔고 조회"""
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0
    return 0


def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(ticker=ticker)["orderbook_units"][0]["ask_price"]


def get_yesterday_volatility(ticker):
    """전일 변동성 구하기"""
    yes_df = pyupbit.get_ohlcv("KRW-" + ticker, count=2).iloc[-2]
    return round((yes_df["high"] - yes_df["low"]) / yes_df["open"] * 100, 2)


def buy_coin(ticker):
    """코인 매수 로직"""
    if ticker in bought_tickers:
        return

    target_price = get_target_price("KRW-" + ticker, 0.5)  # 목표가 구하기
    ma5 = get_ma5("KRW-" + ticker)  # 이동평균 구하기
    current_price = get_current_price("KRW-" + ticker)  # 현재가 구하기

    if target_price < current_price and ma5 < current_price:  # 매수 조건 확인
        yesterday_volatility = get_yesterday_volatility(ticker)  # 전일 변동성

        # 투자비중: (목표 변동성 / 전일 변동성) / 투자 대상 가상화폐 수
        buy_rate = (target_volatility / yesterday_volatility) / to_buy_amount

        # 투자금액: 자산 * 투자비중
        buy_krw = int(balance * buy_rate)

        if buy_krw > 5000:
            print(f"{ticker} => {buy_krw}원({buy_rate * 100:.2f}%) 매수 주문!")
            buy_result = upbit.buy_market_order("KRW-" + ticker, buy_krw * 0.9995)
            post_message(myToken, "#coin", "BTC buy : " + str(buy_result))
            bought_tickers.append(ticker)


def sell_all():
    """보유 코인 전량 매도"""
    for ticker in bought_tickers:
        amount = get_balance(ticker)
        sell_result = upbit.sell_market_order("KRW-" + ticker, amount)
        post_message(myToken, "#coin", "BTC buy : " + str(sell_result))


# 로그인
upbit = pyupbit.Upbit(access, secret)
print("autotrade start")
# 시작 메세지 슬랙 전송
post_message(myToken, "#coin", "autotrade start")

# 변수 설정
to_buy_tickers = ["BTC", "ETH", "XRP", "BCH", "BTG"]
to_buy_amount = len(to_buy_tickers)
bought_tickers = []
fee = 0.0005  # 수수료
target_volatility = 2  # 타깃 변동성(%)
balance = int(upbit.get_balance("KRW"))  # 주문 가능 금액(보유 자산)
print("주문 가능 금액:", balance)
print()

# 자동매매 시작
while True:
    try:
        now = datetime.datetime.now()
        start_time = get_start_time("KRW-BTC")  # 9:00
        end_time = start_time + datetime.timedelta(days=1)  # 9:00 + 1일

        if start_time < now < end_time - datetime.timedelta(seconds=10):
            for ticker in to_buy_tickers:
                buy_coin(ticker)
                time.sleep(1)
        else:
            sell_all()
            balance = int(upbit.get_balance("KRW"))
        time.sleep(1)
    except Exception as e:
        print(e)
        post_message(myToken, "#crypto", e)
        time.sleep(1)
