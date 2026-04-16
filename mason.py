import yfinance as yf
import requests
import math
import pandas as pd
import os
from datetime import datetime, timedelta

# --- [1. 설정 및 실전 기준점] ---
TELEGRAM_TOKEN = "8278038145:AAFa9Y-RJhcW12SKtGOnqGNQW7w1q9ErPCY"
TELEGRAM_CHAT_ID = "5466858773"
DIVISIONS = int(os.environ.get("MY_DIVISIONS", "40")) 
LOAN_REPAYMENT = 4400 

# [지독한 실전 데이터] 2026년 1월 1일 기준 총 시드 (사령관님 기억 소환 필요)
# 일단 현재 8,000만 원 기준으로 역산하거나 Secret에 저장된 값을 쓰게 세팅합니다.
START_DATE = datetime(2026, 1, 1)
START_SEED = 7000  # 예시: 1월 1일 당시 시드가 7,000만 원이었다면? (수정 가능)

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
        # 1. 현재 자산 파악
        total_seed = float(os.environ.get("MY_SEED", "8000")) 
        net_seed = total_seed - LOAN_REPAYMENT
        rate = get_exchange_rate()
        
        # 2. 실전 월평균 수익률(r) 계산
        today = datetime.now()
        # 경과된 개월 수 계산 (최소 0.1개월 보장)
        elapsed_days = (today - START_DATE).days
        elapsed_months = max(elapsed_days / 30.44, 0.1)
        
        # (현재자산 / 시작자산) ^ (1 / 경과월수) - 1
        monthly_yield = (total_seed / START_SEED) ** (1 / elapsed_months) - 1
        
        # 3. 리포트 생성
        report = f"📅 {today.strftime('%Y-%m-%d')}\n🌅 [Mason Actual Pace Report]\n"
        report += f"운용원금: {net_seed:,.0f}만 (대출상환 반영)\n"
        report += f"실전 월수익률: {monthly_yield*100:+.2f}%\n"
        
        # 4. 종목 분석 (1/40 화력)
        daily_budget_usd = ((net_seed * 10000) / 3 / DIVISIONS) / rate
        found_cnt = 0
        for t in CANDIDATES:
            try:
                df = yf.download(t, period="3mo", progress=False)
                c = df['Close'].iloc[:, 0] if isinstance(df['Close'], pd.DataFrame) else df['Close']
                rsi = float(calculate_rsi(c).iloc[-1])
                price = float(c.iloc[-1])
                
                # SQQQ는 RSI 30, 나머지는 40
                limit = 30 if t == "SQQQ" else 40
                if rsi <= limit:
                    qty = math.ceil(daily_budget_usd / price)
                    report += f"\n🎯 [{t}] RSI: {rsi:.1f} / QTY: {qty}"
                    found_cnt += 1
            except: continue
        
        if found_cnt == 0: report += "\n✅ 사거리 내 타겟 없음"

        # 5. [핵심] 현재 페이스 유지 시 2억 달성 시뮬레이션
        target = 20000
        report += f"\n\n🏁 [2억 고지 점령 시뮬레이션]"
        report += f"\n현재 달성률: {(net_seed/target)*100:,.1f}%"
        
        if monthly_yield > 0:
            months_to_go = math.log(target / net_seed) / math.log(1 + monthly_yield)
            est_date = (today + timedelta(days=months_to_go * 30.44)).strftime('%Y-%m-%d')
            report += f"\n예상 점령일: {est_date}\n(현 페이스 유지 시)"
        else:
            report += f"\n예상 점령일: 측정 불가\n(수익률 반등이 필요합니다, 사령관님!)"

        report += "\n------------------\n지독하게 원칙 매수하십시오!"
        
        # 텔레그램 발송
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      data={"chat_id": TELEGRAM_CHAT_ID, "text": report})
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
