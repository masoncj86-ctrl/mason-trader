import yfinance as yf
import requests
import math
import pandas as pd
import os
from datetime import datetime

# --- [사령관 전용 설정] ---
TELEGRAM_TOKEN = "8278038145:AAFa9Y-RJhcW12SKtGOnqGNQW7w1q9ErPCY"
TELEGRAM_CHAT_ID = "5466858773"

# GitHub Secrets 변수
DIVISIONS = int(os.environ.get("MY_DIVISIONS", "40")) 
MY_SEED = float(os.environ.get("MY_SEED", "4000"))   # 현재 나의 순수 자산
MY_DEBT = float(os.environ.get("MY_DEBT", "5000"))   # 현재 나의 대출금
MY_PROFIT = float(os.environ.get("MY_PROFIT", "2088")) # 올해 주식 수익금

# [전설의 데이터] 140일 만에 9배 팽창 (2025.12.01 ~ 2026.04.20 기준)
START_TOTAL_SEED = 1000
START_DATE = datetime(2026, 1, 1) # 사령관님의 140일 전 기준점

CANDIDATES = ["LABU", "TNA", "TSLL", "SOXL", "NRGU", "GDXU", "IONX", "FNGU", "SQQQ"]

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
    rs = ma_up / ma_down.replace(0, 0.001)
    return 100 - (100 / (1 + rs))

def main():
    try:
        # 1. 현재 자산 현황
        current_total = MY_SEED + MY_DEBT
        rate = get_exchange_rate()
        today = datetime.now()
        
        # 2. 월 자산 증가율 매일 업데이트 (일 단위 정밀 계산)
        elapsed_days = max((today - START_DATE).days, 1)
        # 일평균 복리 증가율 계산 후 월 단위(30.44일)로 환산
        daily_rate = (current_total / START_TOTAL_SEED) ** (1 / elapsed_days) - 1
        monthly_growth_rate = ((1 + daily_rate) ** 30.44 - 1) * 100
        
        # 3. 리포트 헤더 생성
        report = f"📅 {today.strftime('%Y-%m-%d')}\n💰 [Mason Asset Report]\n"
        report += f"------------------\n"
        report += f"🚀 총 가용시드: {current_total:,.0f}만\n"
        report += f"💵 순수 자산: {MY_SEED:,.0f}만\n"
        report += f"📈 올해 수익: {MY_PROFIT:,.0f}만\n"
        report += f"🏦 대출 병력: {MY_DEBT:,.0f}만\n"
        report += f"------------------\n"
        report += f"📊 월 자산 증가율: {monthly_growth_rate:+.2f}%\n"
        report += f"ㄴ ({elapsed_days}일간의 데이터 실시간 반영)\n"
        
        # 4. 화력 분석 및 LOC 공격 타겟
        daily_budget_usd = ((current_total * 10000) / 3 / DIVISIONS) / rate
        found_cnt = 0
        
        for t in CANDIDATES:
            try:
                ticker = yf.Ticker(t); df = ticker.history(period="3mo")
                if df.empty: continue
                c = df['Close']; rsi = float(calculate_rsi(c).iloc[-1]); price = float(c.iloc[-1])
                
                limit = 30 if t == "SQQQ" else 40
                if rsi <= limit:
                    qty = math.ceil(daily_budget_usd / price)
                    report += f"\n🎯 [TARGET] {t}\n"
                    report += f"RSI: {rsi:.1f} / 공격가(+10%): ${price*1.1:.2f}\n"
                    report += f"📦 권장 수량: {qty}개\n"
                    found_cnt += 1
            except: continue
            
        if found_cnt == 0: report += "\n✅ 사거리 내 타겟 없음"

        # 5. 달성률 (2억 고지)
        target = 20000 
        progress = (current_total / target) * 100
        report += f"\n\n🏁 [Goal: 2억 고지]\n"
        report += f"🚩 현재 달성률: {progress:,.1f}%"

        report += "\n------------------\n지독하게 원칙 매수하십시오."
        
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      data={"chat_id": TELEGRAM_CHAT_ID, "text": report})
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
