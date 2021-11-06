import pyupbit
import datetime
import time

access = "FalkzhtP5xxwmqIm3xnnInSQWelQOR2xml6g48xf"
secret = "Y3nwdG4s0ONwq0KWKsnHBInzW8qoN3kk7cXxkROV"


def print_log(message):
    """로그 출력 함수"""
    print(datetime.datetime.now().strftime("[%m/%d %H:%M:%S]"), message)


def get_current_cash():
    """주문 가능 금액 반환"""
    available_balance = round(float(upbit.get_balances()[0]["balance"]), 0)
    return available_balance


def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    start_time = df.index[0]
    return start_time


def get_target_price(ticker, k=0.5):
    """매수 목표가 반환"""
    try:
        ohlcv = pyupbit.get_ohlcv(ticker)
        yesterday = ohlcv.iloc[-2]
        today_open = yesterday["close"]
        yesterday_high = yesterday["high"]
        yesterday_low = yesterday["low"]
        target_price = today_open + (yesterday_high - yesterday_low) * k
        return target_price
    except Exception as ex:
        print("get_target_price() -> 예외발생! " + str(ex))
        return None


def get_yesterday_volatility(ticker):
    """전일 변동성 반환"""
    yesterday_ohlcv = pyupbit.get_ohlcv(ticker, count=2).iloc[-2]
    return (yesterday_ohlcv["high"] - yesterday_ohlcv["low"]) / yesterday_ohlcv["open"] * 100


def get_movingaverage(ticker, window):
    """전일 이동평균값 반환"""
    try:
        ohlcv = pyupbit.get_ohlcv(ticker)
        close = ohlcv["close"]
        ma = close.rolling(window=window).mean()
        return ma[-2]
    except Exception as ex:
        print(f"get_movingaverage() -> 예외발생! {str(ex)}")
        return None


def init_ticker_list():
    """관찰 종목 리스트 초기화"""
    my_tickers = []
    tickers = pyupbit.get_tickers("KRW")
    for ticker in tickers:
        try:
            print(ticker)
            current_price = pyupbit.get_current_price(ticker)
            moving_3, moving_5, moving_10, moving_20 = get_movingaverage(ticker, 3), get_movingaverage(ticker, 5), \
                                                       get_movingaverage(ticker, 10), get_movingaverage(ticker, 20)
            if current_price > moving_3 and current_price > moving_5 and current_price > moving_10 and current_price > moving_20:
                my_tickers.append(ticker)
            time.sleep(0.2)
        except Exception as ex:
            print_log(f"init_ticker_list() -> 예외 발생! {ex}")
    return my_tickers


def get_buy_percentage():
    """투자 비율 리턴"""
    yesterday_volatility = get_yesterday_volatility(ticker)
    if len(target_list) < limit_amount:
        buy_percentage = target_volatility / yesterday_volatility / limit_amount
    else:
        buy_percentage = target_volatility / yesterday_volatility / len(target_list)
    return buy_percentage


def buy_coin(ticker):
    """매수 주문 함수"""
    try:
        if ticker in bought_list:
            print(f"티커 {ticker}은/는 이미 매수했습니다.")
            return False

        target_price = get_target_price(ticker)  # 목표가
        current_price = pyupbit.get_current_price(ticker)  # 현재가
        # ma5_price = get_movingaverage(ticker, window=5)  # 5일 이동평균가

        # 매수 조건 확인
        # if current_price > target_price and current_price > ma5_price:
        if current_price > target_price:
            print(f"{ticker} 매수 조건 통과!")

            # 투자 금액 => 자산 * ((목표 변동성 / 전일 변동성) / 투자 대상 코인 수)
            buy_percentage = get_buy_percentage()
            buy_price = int(buy_percentage * available_balance)

            # 지정가 주문
            buy_result = upbit.buy_market_order(ticker, buy_price * 0.9995)  # (티커, 주문 가격, 수량)
            print(buy_result)
            print_log(f"시장가 매수 -> 티커: {ticker}, 주문 금액: {buy_price}({buy_percentage * 100:.2f}%)")
            bought_list.append(ticker)
    except Exception as ex:
        print_log(f"buy_etf({ticker}) -> 예외발생! {str(ex)}")


def sell_all():
    """모든 코인 전량 매도"""
    try:
        tickers = upbit.get_balances()
        for ticker_dict in tickers:
            if ticker_dict["currency"] == "KRW":
                continue

            ticker = "KRW-" + ticker_dict["currency"]
            balance = ticker_dict["balance"]

            sell_result = upbit.sell_market_order(ticker, balance)
            print(sell_result)
            print_log(f"시장가 매도 -> 티커: {ticker}, 매도수량: {balance}")
    except Exception as ex:
        print_log(f"sell_all() -> 예외발생! {str(ex)}")


if __name__ == "__main__":
    try:
        # upbit API 접속
        upbit = pyupbit.Upbit(access, secret)
        print_log("업비트 자동매매 접속")

        ##### 변수 #####
        # target_list = ["BTC", "ETH", "XRP", "BTG", "BCH", "ETC"]  # 후보 리스트
        target_list = init_ticker_list()  # 후보 리스트 초기화
        target_volatility = 2  # 목표 변동성(%)
        limit_amount = 5  # 매수할 최소 종목 수
        ###############

        bought_list = []  # 매수 완료 리스트
        available_balance = get_current_cash()  # 주문 가능 금액
        print(f"주문 가능 금액: {available_balance}")
        print()

        while True:
            now = datetime.datetime.now()
            start_time = get_start_time("KRW-BTC")
            end_time = start_time + datetime.timedelta(days=1)

            if start_time < now < end_time - datetime.timedelta(seconds=10):  # 9:00 ~ 다음날 9:00 - 10초
                for ticker in target_list:
                    buy_coin("KRW-" + ticker)
                    time.sleep(1)
            elif now.minute == 0:
                print_log(f"주문 가능 금액: {available_balance} | 보유 코인: {bought_list}")
            else:
                print("루틴 종료 => 초기화")
                sell_all()
                available_balance = get_current_cash()  # 주문 가능 금액 재설정
                print(f"주문 가능 금액: {available_balance}")
                print()
                bought_list = []  # 매수 완료 리스트 초기화
            time.sleep(3)

    except Exception as ex:
        print(f"main -> 예외 발생! {str(ex)}")
        time.sleep(1)
