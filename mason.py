import yfinance as yf
import requests
import math
import pandas as pd
import os
from datetime import datetime, timedelta

# --- [1. 환경 변수 및 사령관 지침 설정] ---
def get_env_safe(key, default):
    val = os.environ.get(key, "").strip()
    return val if val and val.upper() != "NONE" else str(default)

TOKEN = get_env_safe("TELEGRAM_TOKEN", "8278038145:AAFa9Y-RJhcW12SKtGOnqGNQW7w1q9ErPCY")
CHAT_ID = get_env_safe("TELEGRAM_CHAT_ID", "5466858773")

# [사령관 지침] 현재 총 예수금 8,000만 원 가정
TOTAL_SEED = float(get_env_safe("MY_SEED", "8000").replace(',', ''))
# [핵심] 대출금 4,400만 원을 미리 갚았다고 가정하고 제외 (순수 원금 운용)
LOAN_REPAYMENT = 4400 
NET_SEED = TOTAL_SEED - LOAN_REPAYMENT # 실제 운용 시드 (예: 3,600만)

RAW_HOLDINGS = get_env_safe("MY_HOLDINGS", "TSLL,FNGU")
DIVISIONS = 40 # 강철의 1/40 원칙

CANDIDATES = ["LABU", "TNA", "TSLL", "SOXL", "NRGU", "GDXU", "IONX", "FNGU", "SQQQ"]

# --- [2. 핵심 엔진 함수] ---
def get_exchange_rate():
    try:
        res = requests.get("https://open.er-api.com/v6/latest/USD", timeout=5).json()
        return float(res['rates']['KRW'])
    except: return 1450.0

def calculate_rsi(series, period=14):
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ma_up = up.ewm(com=period-1, adjust=False).mean()
    ma_down = down.ewm(com=period-1, adjust=False).mean()
    return 100 - (100 / (1 + (ma_up / ma_down.replace(0, 0.001))))

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, timeout=10)
    except: pass

# --- [3. 메인 분석 로직] ---
def main():
    try:
        rate = get_exchange_rate()
        my_holdings = [t.strip().upper() for t in RAW_HOLDINGS.split(',') if t.strip()]

        # [수정] 모든 화력은 대출금을 제외한 '순수 원금(NET_SEED)' 기준으로 계산
        # 1일 화력 = (순수 원금 / 3종목 분산 / 40분할) / 환율
        daily_budget_usd = ((NET_SEED * 10000) / 3 / DIVISIONS) / rate

        report = f"📅 {datetime.now().strftime('%Y-%m-%d')}\n🌅 [Mason Net-Asset Report]\n"
        report += f"TOTAL: {TOTAL_SEED:,.0f}만 / LOAN: -{LOAN_REPAYMENT}만\n"
        report += f"운용원금: {NET_SEED:,.0f}만 (DIV: {DIVISIONS})\nRATE: {rate:.1f}원\n"
        
        found_cnt = 0
        for ticker in CANDIDATES:
            try:
                df = yf.download(ticker, period="3mo", progress=False)
                if df.empty: continue
                close = df['Close'].iloc[:, 0] if isinstance(df['Close'], pd.DataFrame) else df['Close']
                rsi = float(calculate_rsi(close).iloc[-1])
                last_price = float(close.iloc[-1])

                # SQQQ 전용 (RSI 30 이하)
                if ticker == "SQQQ" and rsi <= 30:
                    qty = math.ceil(daily_budget_usd / last_price)
                    report += f"\n💀 [SQQQ SPECIAL] RSI: {rsi:.1f}\nPRICE: ${last_price:.2f} / QTY: {qty}\n"
                    found_cnt += 1
                
                # 일반 종목 (RSI 40 이하)
                elif ticker != "SQQQ" and rsi <= 40:
                    qty = math.ceil(daily_budget_usd / last_price)
                    report += f"\n🚀 [NEW] {ticker} RSI: {rsi:.1f}\nPRICE: ${last_price:.2f} / QTY: {qty}\n"
                    found_cnt += 1
            except: continue

        if found_cnt == 0: report += "\n✅ 사거리 내 타겟 없음\n"

        # 2억 달성 시뮬레이션 (순수 원금 기준)
        target = 20000
        months, temp_seed = 0, NET_SEED
        while temp_seed < target and months < 240:
            temp_seed *= 1.05
            months += 1
        expected_date = (datetime.now() + timedelta(days=months*30)).strftime('%Y-%m-%d')
        report += f"\n🎯 [2억 달성 시뮬]\n도달 예상: {expected_date}\n(순수원금 복리 5% 가정)"
        
        report += "\n------------------\n사령관님, 빚 갚은 셈 치고 '무차입' 정신으로 원칙 매수하십시오!"
        send_telegram(report)
        print(">>> SUCCESS: Net-Asset report sent.")

    except Exception as e:
        print(f">>> [CRITICAL ERROR] {e}")

if __name__ == "__main__":
    main()
