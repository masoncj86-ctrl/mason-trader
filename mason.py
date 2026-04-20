import yfinance as yf
import requests
import math
import pandas as pd
import os
from datetime import datetime, timedelta

# --- [설정] ---
TELEGRAM_TOKEN = "8278038145:AAFa9Y-RJhcW12SKtGOnqGNQW7w1q9ErPCY"
TELEGRAM_CHAT_ID = "5466858773"

# GitHub Secrets 변수
DIVISIONS = int(os.environ.get("MY_DIVISIONS", "40")) 
MY_PURE_SEED = float(os.environ.get("MY_SEED", "4000")) # 내 순수 자산
MY_DEBT = float(os.environ.get("MY_DEBT", "5000"))    # 대출금

# 실전 페이스 측정 기준
START_DATE = datetime(2026, 1, 1)
START_SEED = 3600  # 1월 1일 당시 순수 자산

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
    return 100 - (100 / (1 + (ma_up / ma_down.replace(0, 0.001))))

def main():
    try:
        # 1. 자산 합산 로직 (순자산 + 대출 = 총 가용 시드)
        total_available = MY_PURE_SEED + MY_DEBT 
        rate = get_exchange_rate()
        
        # 2. 수익률 계산 (순수 자산 증가분 기준)
        today = datetime.now()
        elapsed_months = max((today - START_DATE).days / 30.44, 0.1)
        actual_monthly_yield = (MY_PURE_SEED / START_SEED) ** (1 / elapsed_months) - 1
        
        # 3. 리포트 생성
        report = f"📅 {today.strftime('%Y-%m-%d')}\n💰 [Mason Asset Report]\n"
        report += f"------------------\n"
        report += f"💵 순수 자산: {MY_PURE_SEED:,.0f}만\n"
        report += f"🏦 대출 병력: {MY_DEBT:,.0f}만\n"
        report += f"🚀 총 가용시드: {total_available:,.0f}만\n"
        report += f"------------------\n"
        report += f"📈 순수 월수익률: {actual_monthly_yield*100:+.2f}%\n"
        
        # 4. 화력 분석 (총 가용시드 기준 타격)
        daily_budget_usd = ((total_available * 10000) / 3 / DIVISIONS) / rate
        found_cnt = 0
        for t in CANDIDATES:
            try:
                df = yf.download(t, period="3mo", progress=False)
                c = df['Close'].iloc[:, 0] if isinstance(df['Close'], pd.DataFrame) else df['Close']
                rsi = float(calculate_rsi(c).iloc[-1])
                price = float(c.iloc[-1])
                
                limit = 30 if t == "SQQQ" else 40
                if rsi <= limit:
                    qty = math.ceil(daily_budget_usd / price)
                    loc_price = price * 0.9 # LOC 10% 하단가
                    report += f"\n🎯 [TARGET] {t}\n"
                    report += f"RSI: {rsi:.1f} / 현재가: ${price:.2f}\n"
                    report += f"📍 LOC 10% 매수가: ${loc_price:.2f}\n"
                    report += f"📦 권장 수량: {qty}개\n"
                    found_cnt += 1
            except: continue
        
        if found_cnt == 0: report += "\n✅ 사거리 내 타겟 없음"

        # 5. 목표 달성 현황 (순자산 2억 기준)
        target = 20000
        progress = (MY_PURE_SEED / target) * 100
        report += f"\n\n🏁 [Goal: 2억 고지]"
        report += f"\n현재 달성률: {progress:,.1f}%"
        
        if actual_monthly_yield > 0:
            months_to_go = math.log(target / MY_PURE_SEED) / math.log(1 + actual_monthly_yield)
            est_date = (today + timedelta(days=months_to_go * 30.44)).strftime('%Y-%m-%d')
            report += f"\n예상 점령일: {est_date}"

        report += "\n------------------\n지독하게 원칙 매수하십시오."
        
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      data={"chat_id": TELEGRAM_CHAT_ID, "text": report})
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
