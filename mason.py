import yfinance as yf
import requests
import math
import pandas as pd
import os
from datetime import datetime, timedelta

# --- [1. 지독한 실전 설정] ---
TELEGRAM_TOKEN = "8278038145:AAFa9Y-RJhcW12SKtGOnqGNQW7w1q9ErPCY"
TELEGRAM_CHAT_ID = "5466858773"

# Secret에서 가져오되, 실패하면 40분할로 지독하게 고정!
DIVISIONS = int(os.environ.get("MY_DIVISIONS", "40")) 
LOAN_REPAYMENT = 4400 

# [사령관 지침] 2026년 1월 1일 기준 데이터
START_DATE = datetime(2026, 1, 1)
START_SEED = 5400 # 1월 1일 자산 (사령관님이 직접 수정 가능!)

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
        # 1. 자산 데이터 획득
        total_seed = float(os.environ.get("MY_SEED", "8000")) 
        net_seed = total_seed - LOAN_REPAYMENT
        rate = get_exchange_rate()
        
        # 2. [핵심] 실전 월평균 수익률 계산 (보급로 차단!)
        today = datetime.now()
        elapsed_months = max((today - START_DATE).days / 30.44, 0.1)
        # 실전 월수익률(r) 공식
        actual_monthly_yield = (total_seed / START_SEED) ** (1 / elapsed_months) - 1
        
        # 3. 리포트 헤더 (보급 관련 문구 지독하게 삭제)
        report = f"📅 {today.strftime('%Y-%m-%d')}\n🌅 [Mason Actual Performance]\n"
        report += f"운용원금: {net_seed:,.0f}만 (대출상환 반영)\n"
        report += f"실전 월수익률: {actual_monthly_yield*100:+.2f}%\n"
        report += f"설정 디비전: {DIVISIONS}분할\n"
        
        # 4. 화력 분석 (NET_SEED 기준 1/40 타격)
        daily_budget_usd = ((net_seed * 10000) / 3 / DIVISIONS) / rate
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
                    report += f"\n🎯 [{t}] RSI: {rsi:.1f} / QTY: {qty}"
                    found_cnt += 1
            except: continue
        
        if found_cnt == 0: report += "\n✅ 현재 사거리 내 타겟 없음"

        # 5. [수정] 순수 실전 페이스 기반 2억 시뮬레이션
        target = 20000
        report += f"\n\n🏁 [2억 고지 점령 시뮬레이션]"
        report += f"\n현재 달성률: {(net_seed/target)*100:,.1f}%"
        
        if actual_monthly_yield > 0:
            # 보급 없이 순수 복리로 2억 도달 개월수 계산
            months_to_go = math.log(target / net_seed) / math.log(1 + actual_monthly_yield)
            est_date = (today + timedelta(days=months_to_go * 30.44)).strftime('%Y-%m-%d')
            report += f"\n예상 점령일: {est_date}\n(추가보급 없이 현 페이스 유지 시)"
        else:
            report += f"\n예상 점령일: 측정 불가 (수익률 반등 필요)"

        report += "\n------------------\n사령관님, 오직 실력으로 승리하십시오!"
        
        # 텔레그램 전송
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      data={"chat_id": TELEGRAM_CHAT_ID, "text": report})
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
