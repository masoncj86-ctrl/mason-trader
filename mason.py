import yfinance as yf
import requests
import math
import pandas as pd
import os
from datetime import datetime, timedelta

# --- [환경 변수 로드 및 방어 로직] ---
def get_env(key, default):
    val = os.environ.get(key, "").strip()
    # 값이 없거나, NONE이거나, 공백이면 기본값을 지독하게 주입!
    if not val or val.upper() == "NONE":
        return default
    return val

TOKEN = get_env("TELEGRAM_TOKEN", "8278038145:AAFa9Y-RJhcW12SKtGOnqGNQW7w1q9ErPCY")
CHAT_ID = get_env("TELEGRAM_CHAT_ID", "5466858773")
# 시드값이 비어있으면 사령관님의 현재 자산인 8000으로 강제 세팅!
RAW_SEED = get_env("MY_SEED", "8000")
RAW_HOLDINGS = get_env("MY_HOLDINGS", "TSLL,FNGU")
RAW_DIVS = get_env("MY_DIVISIONS", "40")

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
    except: pass

def main():
    try:
        seed_val = float(RAW_SEED.replace(',', ''))
        divs = int(RAW_DIVS)
        holdings = [t.strip().upper() for t in RAW_HOLDINGS.split(',') if t.strip()]
        
        rate = get_exchange_rate()
        budget_usd = ((seed_val * 10000) / 3 / divs) / rate

        report = f"📅 {datetime.now().strftime('%Y-%m-%d')}\n🌅 [Mason Final Report]\nSEED: {seed_val:,.0f}만 / DIV: {divs}\n"
        
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
                close = df['Close'].iloc[:, 0] if isinstance(df['Close'], pd.DataFrame) else df['Close']
                rsi = float(calculate_rsi(close).iloc[-1])
                price = float(close.iloc[-1])
                report += f"\n📦 [HOLDING] {t}\nRSI: {rsi:.1f} / QTY: {math.ceil(budget_usd/price)}\n"
            except: continue

        # 2억 달성 시뮬레이션 (순수 복리)
        target = 20000
        months = 0
        temp_s = seed_val
        while temp_s < target and months < 120:
            temp_s *= 1.05
            months += 1
        report += f"\n🎯 [2억 달성 예상일]\n{ (datetime.now() + timedelta(days=months*30)).strftime('%Y-%m-%d') }\n"
        
        report += "\n------------------\n사령관님, 지독하게 원칙 매수하십시오!"
        send_telegram(report)
        print("Report Sent!")

    except Exception as e:
        print(f"Error in main: {e}")

if __name__ == "__main__":
    main()
