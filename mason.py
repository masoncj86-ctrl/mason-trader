import yfinance as yf
import requests
import math
import pandas as pd
import os
from datetime import datetime, timedelta

# --- [1. 사령관 전용 하드코딩 설정] ---
# 시크릿을 거치지 않고 직접 통신망을 구축합니다.
TELEGRAM_TOKEN = "8278038145:AAFa9Y-RJhcW12SKtGOnqGNQW7w1q9ErPCY"
TELEGRAM_CHAT_ID = "5466858773"

# [핵심 자산 전략] 
# 총 예수금 8,000만 원에서 대출금 4,400만 원을 '상환 완료' 처리한 순수 원금으로만 운용!
TOTAL_SEED = 8000 
LOAN_REPAYMENT = 4400 
NET_SEED = TOTAL_SEED - LOAN_REPAYMENT # 실제 운용 기준점: 3,600만 원

# 보유 종목 및 분할 원칙
MY_HOLDINGS = ["TSLL", "FNGU"]
DIVISIONS = 40 # 강철의 1/40 분할 매수

# 분석 타겟 (3배 레버리지군 + 헤지용 SQQQ)
CANDIDATES = ["LABU", "TNA", "TSLL", "SOXL", "NRGU", "GDXU", "IONX", "FNGU", "SQQQ"]

# --- [2. 핵심 엔진 함수] ---
def get_exchange_rate():
    try:
        # 실시간 환율 정보 획득
        res = requests.get("https://open.er-api.com/v6/latest/USD", timeout=5).json()
        return float(res['rates']['KRW'])
    except: return 1450.0

def calculate_rsi(series, period=14):
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ma_up = up.ewm(com=period-1, adjust=False).mean()
    ma_down = down.ewm(com=period-1, adjust=False).mean()
    # 0 나누기 방지 로직 포함
    return 100 - (100 / (1 + (ma_up / ma_down.replace(0, 0.001))))

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        res = requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg}, timeout=10)
        print(f">>> 통신 상태: {res.status_code}") # GitHub 로그에서 성공 여부 확인용
    except Exception as e:
        print(f">>> 통신 에러: {e}")

# --- [3. 메인 분석 로직] ---
def main():
    try:
        rate = get_exchange_rate()
        
        # [화력 계산] 모든 매수 수량은 대출금을 제외한 '순수 원금(3,600만)' 기준
        # 1일 화력 = (순수 원금 / 3종목 분산 / 40분할) / 환율
        daily_budget_usd = ((NET_SEED * 10000) / 3 / DIVISIONS) / rate

        report = f"📅 {datetime.now().strftime('%Y-%m-%d')}\n🌅 [Mason Net-Asset Report]\n"
        report += f"총자산: {TOTAL_SEED}만 / 대출상환: -{LOAN_REPAYMENT}만\n"
        report += f"운용원금: {NET_SEED}만 (DIV: {DIVISIONS})\nRATE: {rate:.1f}원\n"
        
        found_cnt = 0
        for ticker in CANDIDATES:
            try:
                df = yf.download(ticker, period="3mo", progress=False)
                if df.empty: continue
                
                # 종가 데이터 추출 (멀티인덱스 대응)
                close = df['Close'].iloc[:, 0] if isinstance(df['Close'], pd.DataFrame) else df['Close']
                rsi = float(calculate_rsi(close).iloc[-1])
                last_price = float(close.iloc[-1])

                # [SQQQ 특수 전술] RSI 30 이하에서만 순수 원금 기준으로 정밀 타격
                if ticker == "SQQQ" and rsi <= 30:
                    qty = math.ceil(daily_budget_usd / last_price)
                    report += f"\n💀 [SQQQ SPECIAL] RSI: {rsi:.1f}\nPRICE: ${last_price:.2f} / QTY: {qty}\n"
                    found_cnt += 1
                
                # [일반 종목 전술] RSI 40 이하 시 진입
                elif ticker != "SQQQ" and rsi <= 40:
                    qty = math.ceil(daily_budget_usd / last_price)
                    report += f"\n🚀 [TARGET] {ticker} RSI: {rsi:.1f}\nPRICE: ${last_price:.2f} / QTY: {qty}\n"
                    found_cnt += 1
            except: continue

        if found_cnt == 0: report += "\n✅ 사거리 내 포착된 타겟 없음\n"

        # 현재 보유 종목 현황 브리핑
        report += "\n📦 [CURRENT HOLDINGS]"
        for ticker in MY_HOLDINGS:
            try:
                df = yf.download(ticker, period="1d", progress=False)
                last_price = float(df['Close'].iloc[-1])
                report += f"\n- {ticker}: ${last_price:.2f}"
            except: continue

        # 2억 달성 시뮬레이션 (순수 원금 5% 복리 가정)
        target = 20000
        months, temp_seed = 0, NET_SEED
        while temp_seed < target and months < 240:
            temp_seed *= 1.05
            months += 1
        expected_date = (datetime.now() + timedelta(days=months*30)).strftime('%Y-%m-%d')
        report += f"\n\n🎯 [2억 달성 시뮬레이션]\n도달 예상: {expected_date}\n(순수원금 월 5% 복리 가정)"
        
        report += "\n------------------\n사령관님, 지독하게 원칙 매수하십시오!"
        
        # 텔레그램 발송
        send_telegram(report)
        print(">>> SUCCESS: Strategic report sent to Commander.")

    except Exception as e:
        print(f">>> [CRITICAL ERROR] {e}")

if __name__ == "__main__":
    main()
