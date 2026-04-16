import yfinance as yf
import requests
import math
import pandas as pd
import os
from datetime import datetime, timedelta

# --- [사령관 전용 설정] ---
TELEGRAM_TOKEN = "8278038145:AAFa9Y-RJhcW12SKtGOnqGNQW7w1q9ErPCY"
TELEGRAM_CHAT_ID = "5466858773"

DIVISIONS = int(os.environ.get("MY_DIVISIONS", "40")) 
LOAN_AMOUNT = 4400  # 지독한 대출 병력

# [실전 기준] 2026년 1월 1일 자산 (페이스 측정용)
START_DATE = datetime(2026, 1, 1)
START_SEED = 5400 

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
        # 1. 자산 데이터 분석
        total_seed = float(os.environ.get("MY_SEED", "8000")) # 실제 예수금
        net_seed = total_seed - LOAN_AMOUNT # 순수 원금
        rate = get_exchange_rate()
        
        # 2. 실전 월평균 수익률 계산
        today = datetime.now()
        elapsed_months = max((today - START_DATE).days / 30.44, 0.1)
        actual_monthly_yield = (total_seed / START_SEED) ** (1 / elapsed_months) - 1
        
        # 3. 리포트 헤더 (자산 이원화 브리핑)
        report = f"📅 {today.strftime('%Y-%m-%d')}\n🌅 [Mason Actual Assets Report]\n"
        report += f"💰 실제 예수금: {total_seed:,.0f}만\n"
        report += f"ㄴ 순수 원금: {net_seed:,.0f}만\n"
        report += f"ㄴ 대출 병력: {LOAN_AMOUNT:,.0f}만\n"
        report += f"------------------\n"
        report += f"📈 실전 월수익률: {actual_monthly_yield*100:+.2f}%\n"
        report += f"🎯 설정 디비전: {DIVISIONS}분할\n"
        
        # 4. 화력 분석 (실제 예수금 기준 1/40 타격)
        # 사령관님, 예수금 전체를 굴려야 화력이 나오므로 total_seed 기준으로 계산합니다.
        daily_budget_usd = ((total_seed * 10000) / 3 / DIVISIONS) / rate
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
                    report += f"\n🚀 [TARGET] {t}\nRSI: {rsi:.1f} / QTY: {qty}"
                    found_cnt += 1
            except: continue
        
        if found_cnt == 0: report += "\n✅ 현재 사거리 내 타겟 없음"

        # 5. [수정] 대출 포함 2억 고지 시뮬레이션
        target = 20000
        progress = (total_seed / target) * 100
        report += f"\n\n🏁 [2억 대제국 점령 현황]"
        report += f"\n현재 달성률: {progress:,.1f}%"
        
        if actual_monthly_yield > 0:
            # 전체 예수금이 복리로 불어나서 2억이 되는 날짜
            months_to_go = math.log(target / total_seed) / math.log(1 + actual_monthly_yield)
            est_date = (today + timedelta(days=months_to_go * 30.44)).strftime('%Y-%m-%d')
            report += f"\n예상 점령일: {est_date}\n(현 페이스 유지 시)"
        else:
            report += f"\n예상 점령일: 측정 불가"

        report += "\n------------------\n사령관님, 지독하게 원칙 매수하십시오!"
        
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      data={"chat_id": TELEGRAM_CHAT_ID, "text": report})
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
