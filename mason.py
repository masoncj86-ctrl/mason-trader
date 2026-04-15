import yfinance as yf
import requests
import math
import pandas as pd
import os
from datetime import datetime, timedelta

# --- [환경 변수 로드 및 지독한 방어 로직] ---
def get_env_safe(key, default_value):
    # 시스템에서 값을 가져온 뒤 앞뒤 공백을 지독하게 제거합니다.
    val = os.environ.get(key, "")
    if val is None:
        return str(default_value)
    val = val.strip()
    # 값이 비어있거나 'NONE'이면 사령관님이 정한 기본값을 씁니다.
    if not val or val.upper() == "NONE":
        return str(default_value)
    return val

# 텔레그램 설정 (보안상 시크릿 권장이나 실패 시 기본값 작동)
TOKEN = get_env_safe("TELEGRAM_TOKEN", "8278038145:AAFa9Y-RJhcW12SKtGOnqGNQW7w1q9ErPCY")
CHAT_ID = get_env_safe("TELEGRAM_CHAT_ID", "5466858773")

# 사령관님의 현재 실전 데이터 (시크릿이 비어있을 때를 대비한 8,000만 원 보루)
RAW_SEED = get_env_safe("MY_SEED", "8000")
RAW_HOLDINGS = get_env_safe("MY_HOLDINGS", "TSLL,FNGU")
RAW_DIVS = get_env_safe("MY_DIVISIONS", "40")

CANDIDATES = ["LABU", "TNA", "TSLL", "SOXL", "NRGU", "GDXU", "IONX", "FNGU"]

def get_exchange_rate():
    try:
        res = requests.get("https://open.er-api.com/v6/latest/USD", timeout=5).json()
        return float(res['rates']['KRW'])
    except: return 1450.0

def calculate_rsi(series, period=14):
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ma_up = up.ewm(com=period - 1, adjust=False).mean()
    ma_down = down.ewm(com=period - 1, adjust=False).mean()
    return 100 - (100 / (1 + (ma_up / ma_down.replace(0, 0.001))))

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, timeout=10)
    except Exception as e:
        print(f"Telegram Send Error: {e}")

def main():
    try:
        # 지독하게 안전한 숫자 변환 (쉼표 제거 포함)
        seed_val = float(str(RAW_SEED).replace(',', ''))
        divs = int(str(RAW_DIVS))
        holdings = [t.strip().upper() for t in str(RAW_HOLDINGS).split(',') if t.strip() and t.upper() != "NONE"]
        
        rate = get_exchange_rate()
        budget_usd = ((seed_val * 10000) / 3 / divs) / rate

        report = f"📅 {datetime.now().strftime('%Y-%m-%d')}\n🌅 [Mason Classic-V2 Report]\nSEED: {seed_val:,.0f}만 / DIV: {divs}\nRATE: {rate:.1f}원\n"
        
        # 신규 사냥감 분석
        found = 0
        for t in CANDIDATES:
            try:
                df = yf.download(t, period="3mo", progress=False)
                if df.empty: continue
                close = df['Close'].iloc[:, 0] if isinstance(df['Close'], pd.DataFrame) else df['Close']
                rsi = float(calculate_rsi(close).iloc[-1])
                price = float(close.iloc[-1])
                if rsi <= 40:
                    found += 1
                    report += f"\n🚀 [NEW] {t}\nRSI: {rsi:.1f} / QTY: {math.ceil(budget_usd/price)}\n"
            except: continue
        if found == 0: report += "\n✅ 신규 진입 후보 없음\n"

        # 보유 종목 분석
        for t in holdings:
            try:
                df = yf.download(t, period="3mo", progress=False)
                if df.empty: continue
                close = df['Close'].iloc[:, 0] if isinstance(df['Close'], pd.DataFrame) else df['Close']
                rsi = float(calculate_rsi(close).iloc[-1])
                price = float(close.iloc[-1])
                report += f"\n📦 [HOLDING] {t}\nRSI: {rsi:.1f} / QTY: {math.ceil(budget_usd/price)}\n"
            except: continue

        # 2억 달성 시뮬레이션 (보급 없이 순수 복리 5%)
        target = 20000
        months = 0
        temp_s = seed_val
        while temp_s < target and months < 240:
            temp_s *= 1.05
            months += 1
        expected_date = (datetime.now() + timedelta(days=months*30)).strftime('%Y년 %m월 %d일')
        report += f"\n🎯 [2억 달성 예상일]\n{expected_date}\n"
        
        report += "\n------------------\n사령관님, 지독하게 원칙 매수하십시오!"
        send_telegram(report)
        print(">>> SUCCESS: Report Sent to Telegram.")

    except Exception as e:
        print(f">>> CRITICAL ERROR: {e}")

if __name__ == "__main__":
    main()
