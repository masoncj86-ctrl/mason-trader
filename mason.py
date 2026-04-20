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
MY_PURE_SEED = float(os.environ.get("MY_SEED", "3000")) # 현재 순수 자산 (수익 포함)
MY_DEBT = float(os.environ.get("MY_DEBT", "6000"))      # 현재 대출금

# [수정] 수익률 페이스 측정 기준
# 회장님의 '전설의 시작'인 1,000만 원을 기준으로 수익률을 계산합니다.
REAL_START_DATE = datetime(2025, 10, 1) # 대략적인 시작 시점 (필요시 수정)
REAL_START_SEED = 1000  # 진짜 시작 원금 (1,000만 원)

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
        # 1. 자산 합산 (총 시드 기준)
        total_available = MY_PURE_SEED + MY_DEBT 
        rate = get_exchange_rate()
        
        # 2. 실전 수익률 계산 (1,000만 원 대비 현재 순수 자산의 복리 수익률)
        today = datetime.now()
        elapsed_months = max((today - REAL_START_DATE).days / 30.44, 0.1)
        # (현재 순자산 / 시작 원금) 기반의 월평균 복리 수익률
        actual_monthly_yield = (MY_PURE_SEED / REAL_START_SEED) ** (1 / elapsed_months) - 1
        
        # 3. 리포트 생성
        report = f"📅 {today.strftime('%Y-%m-%d')}\n💰 [Mason Asset Report]\n"
        report += f"------------------\n"
        report += f"💵 순수 자산: {MY_PURE_SEED:,.0f}만 (수익포함)\n"
        report += f"🏦 대출 병력: {MY_DEBT:,.0f}만\n"
        report += f"🚀 총 가용시드: {total_available:,.0f}만\n"
        report += f"------------------\n"
        report += f"📈 실전 월수익률: {actual_monthly_yield*100:+.2f}%\n"
        
        # 4. 화력 분석
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
                    loc_price = price * 0.9
                    report += f"\n🎯 [TARGET] {t}\n"
                    report += f"RSI: {rsi:.1f} / 현재가: ${price:.2f}\n"
                    report += f"📍 LOC 10% 매수가: ${loc_price:.2f}\n"
                    report += f"📦 권장 수량: {qty}개\n"
                    found_cnt += 1
            except: continue
        
        if found_cnt == 0: report += "\n✅ 사거리 내 타겟 없음"

        # 5. [수정] 2억 고지 시뮬레이션 (총 가용시드 기준)
        target = 20000 # 대출 포함 2억 목표
        progress = (total_available / target) * 100
        report += f"\n\n🏁 [Goal: 2억 고지(대출포함)]"
        report += f"\n현재 달성률: {progress:,.1f}%"
        
        if actual_monthly_yield > 0:
            # 총 시드가 목표치에 도달하는 날짜 계산
            months_to_go = math.log(target / total_available) / math.log(1 + actual_monthly_yield)
            est_date = (today + timedelta(days=months_to_go * 30.44)).strftime('%Y-%m-%d')
            report += f"\n예상 점령일: {est_date}"

        report += "\n------------------\n지독하게 원칙 매수하십시오."
        
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      data={"chat_id": TELEGRAM_CHAT_ID, "text": report})
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
