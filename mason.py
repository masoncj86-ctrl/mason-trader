import yfinance as yf
import requests
import math
import pandas as pd
import os
from datetime import datetime, timedelta

# --- [사령관 전용 설정] ---
TELEGRAM_TOKEN = "8278038145:AAFa9Y-RJhcW12SKtGOnqGNQW7w1q9ErPCY"
TELEGRAM_CHAT_ID = "5466858773"

# GitHub Secrets 변수 (이름을 아래와 같이 맞추시면 됩니다)
DIVISIONS = int(os.environ.get("MY_DIVISIONS", "40")) 
MY_SEED = float(os.environ.get("MY_SEED", "4000"))   # 현재 나의 순수 자산 (수입+수익)
MY_DEBT = float(os.environ.get("MY_DEBT", "5000"))   # 현재 나의 대출금
MY_PROFIT = float(os.environ.get("MY_PROFIT", "0")) # 올해 주식 실제 수익금

# [수익률 측정 기준] 2026년 1월 1일 "전설의 시작"
REAL_START_DATE = datetime(2026, 1, 1) 
REAL_START_SEED = 1000  # 1월 1일 당시 시작 원금

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
        # 1. 자산 데이터 분석 (합산 로직)
        total_available = MY_SEED + MY_DEBT # 총 가용 시드
        rate = get_exchange_rate()
        
        # 2. 실전 수익률 계산 (2026.1.1 대비 현재 순수 자산 증가율)
        today = datetime.now()
        elapsed_months = max((today - REAL_START_DATE).days / 30.44, 0.1)
        # 월평균 복리 수익률
        actual_monthly_yield = (MY_SEED / REAL_START_SEED) ** (1 / elapsed_months) - 1
        
        # 3. 리포트 헤더 생성
        report = f"📅 {today.strftime('%Y-%m-%d')}\n💰 [Mason Asset Report]\n"
        report += f"------------------\n"
        report += f"💵 순수 자산: {MY_SEED:,.0f}만\n"
        report += f"📈 올해 수익: {MY_PROFIT:,.0f}만\n"
        report += f"🏦 대출 병력: {MY_DEBT:,.0f}만\n"
        report += f"🚀 총 가용시드: {total_available:,.0f}만\n"
        report += f"------------------\n"
        report += f"📊 실전 월수익률: {actual_monthly_yield*100:+.2f}%\n"
        
        # 4. 화력 분석 및 LOC 가이드 (총 가용시드 기준)
        daily_budget_usd = ((total_available * 10000) / 3 / DIVISIONS) / rate
        found_cnt = 0
        
        for t in CANDIDATES:
            try:
                ticker = yf.Ticker(t)
                df = ticker.history(period="3mo")
                if df.empty: continue
                
                c = df['Close']
                rsi = float(calculate_rsi(c).iloc[-1])
                price = float(c.iloc[-1])
                
                limit = 30 if t == "SQQQ" else 40
                if rsi <= limit:
                    qty = math.ceil(daily_budget_usd / price)
                    loc_buy_price = price * 1.1 # 공격적 LOC (+10%)
                    
                    report += f"\n🎯 [TARGET] {t}\n"
                    report += f"RSI: {rsi:.1f} / 현재가: ${price:.2f}\n"
                    report += f"📍 LOC 공격가(+10%): ${loc_buy_price:.2f}\n"
                    report += f"📦 권장 수량: {qty}개\n"
                    found_cnt += 1
            except: continue
        
        if found_cnt == 0: report += "\n✅ 사거리 내 타겟 없음"

        # 5. 목표 달성 현황 (총 시드 기준 2억 고지)
        target = 20000 
        progress = (total_available / target) * 100
        report += f"\n\n🏁 [Goal: 2억 고지]"
        report += f"현재 달성률: {progress:,.1f}%"
        
        if actual_monthly_yield > 0:
            months_to_go = math.log(target / total_available) / math.log(1 + actual_monthly_yield)
            est_date = (today + timedelta(days=months_to_go * 30.44)).strftime('%Y-%m-%d')
            report += f"\n🎯 예상 점령일: {est_date}"

        report += "\n------------------\n지독하게 원칙 매수하십시오."
        
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      data={"chat_id": TELEGRAM_CHAT_ID, "text": report}, timeout=10)
        
    except Exception as e:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      data={"chat_id": TELEGRAM_CHAT_ID, "text": f"❌ 에러: {str(e)}"})

if __name__ == "__main__":
    main()
