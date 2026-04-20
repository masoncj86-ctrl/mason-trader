import yfinance as yf
import requests
import math
import pandas as pd
import os
from datetime import datetime, timedelta

# --- [사령관 전용 설정] ---
TELEGRAM_TOKEN = "8278038145:AAFa9Y-RJhcW12SKtGOnqGNQW7w1q9ErPCY"
TELEGRAM_CHAT_ID = "5466858773"

# GitHub Secrets에서 가져올 변수들
DIVISIONS = int(os.environ.get("MY_DIVISIONS", "40")) 
# 빚(DEBT)은 이제 별도 관리하여 수익률의 투명성을 확보합니다!
MY_DEBT = float(os.environ.get("MY_DEBT", "0")) 

# [실전 기준] 2026년 1월 1일 자산 (순수 자산 페이스 측정용)
START_DATE = datetime(2026, 1, 1)
START_SEED = 3600  # 사령관님의 순수 현금 시작점

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
        # 1. 자산 데이터 분석 (9,000만 원 체제)
        total_seed = float(os.environ.get("MY_SEED", "9000")) 
        net_assets = total_seed - MY_DEBT # 부채를 제외한 사령관님의 '진짜' 제국 크기
        rate = get_exchange_rate()
        
        # 2. 실전 월평균 수익률 (순수 자산 기반으로 지독하게 측정)
        today = datetime.now()
        elapsed_months = max((today - START_DATE).days / 30.44, 0.1)
        # 빚을 뺀 순수 자산이 얼마나 불어났는지가 진짜 실력입니다!
        actual_monthly_yield = (net_assets / START_SEED) ** (1 / elapsed_months) - 1
        
        # 3. 리포트 헤더
        report = f"📅 {today.strftime('%Y-%m-%d')}\n🌅 [Mason Oil-Nam Strategy]\n"
        report += f"💰 총 가용예수금: {total_seed:,.0f}만\n"
        report += f"ㄴ 순수 자산: {net_assets:,.0f}만\n"
        report += f"ㄴ 상환 예정 부채: {MY_DEBT:,.0f}만\n"
        report += f"------------------\n"
        report += f"📈 순수 월수익률: {actual_monthly_yield*100:+.2f}%\n"
        report += f"🎯 타격 디비전: {DIVISIONS}분할\n"
        
        # 4. 화력 분석 및 LOC 가이드
        daily_budget_usd = ((total_seed * 10000) / 3 / DIVISIONS) / rate
        found_cnt = 0
        for t in CANDIDATES:
            try:
                df = yf.download(t, period="3mo", progress=False)
                c = df['Close'].iloc[:, 0] if isinstance(df['Close'], pd.DataFrame) else df['Close']
                rsi = float(calculate_rsi(c).iloc[-1])
                price = float(c.iloc[-1])
                
                # SQQQ는 RSI 30, 나머지는 40 이하에서 타격
                limit = 30 if t == "SQQQ" else 40
                if rsi <= limit:
                    qty = math.ceil(daily_budget_usd / price)
                    # [지독한 LOC 10% 전략] 현재가 대비 10% 낮은 가격 계산
                    loc_price = price * 0.9 
                    report += f"\n🚀 [TARGET] {t}\n"
                    report += f"RSI: {rsi:.1f} / 현재가: ${price:.2f}\n"
                    report += f"📍 LOC 10% 매수가: ${loc_price:.2f}\n"
                    report += f"📦 권장 수량: {qty}개"
                    found_cnt += 1
            except: continue
        
        if found_cnt == 0: report += "\n✅ 현재 사거리 내 타겟 없음"

        # 5. 2억 대제국 점령 현황
        target = 20000
        progress = (net_assets / target) * 100 # 순수 자산 기준 달성률
        report += f"\n\n🏁 [2억 대제국 점령 현황]"
        report += f"순수 자산 달성률: {progress:,.1f}%"
        
        if actual_monthly_yield > 0:
            months_to_go = math.log(target / net_assets) / math.log(1 + actual_monthly_yield)
            est_date = (today + timedelta(days=months_to_go * 30.44)).strftime('%Y-%m-%d')
            report += f"\n🎯 예상 점령일: {est_date}"
        else:
            report += f"\n🎯 예상 점령일: 지독하게 버티는 중..."

        report += "\n------------------\n회장님, '오일남'처럼 냉정하게 사냥하십시오!"
        
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      data={"chat_id": TELEGRAM_CHAT_ID, "text": report})
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
