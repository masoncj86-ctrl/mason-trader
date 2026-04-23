import yfinance as yf
import requests
import math
import os
from datetime import datetime

# --- [사령관 기밀 데이터 직결] ---
TELEGRAM_TOKEN = "8278038145:AAFa9Y-RJhcW12SKtGOnqGNQW7w1q9ErPCY"
TELEGRAM_CHAT_ID = "5466858773"

# GitHub Secrets 데이터 호출
DIVISIONS = int(os.environ.get("MY_DIVISIONS", "40")) 
MY_SEED = float(os.environ.get("MY_SEED", "4000"))   
MY_DEBT = float(os.environ.get("MY_DEBT", "5000"))   
MY_PROFIT = float(os.environ.get("MY_PROFIT", "2088"))
MY_HOLDINGS_RAW = os.environ.get("MY_HOLDINGS", "") # updater.py가 관리하는 데이터

# [전설의 기점] 2026.01.01 함대 창설일
START_TOTAL_SEED = 1000
START_DATE = datetime(2026, 1, 1)
CANDIDATES = ["LABU", "TNA", "TSLL", "SOXL", "NRGU", "GDXU", "IONX", "FNGU", "SQQQ"]

def get_exchange_rate():
    try:
        res = requests.get("https://open.er-api.com/v6/latest/USD", timeout=5).json()
        return float(res['rates']['KRW'])
    except: return 1450.0

def calculate_rsi(series, period=14):
    delta = series.diff()
    up = delta.clip(lower=0).ewm(com=period-1, adjust=False).mean()
    down = -1 * delta.clip(upper=0).ewm(com=period-1, adjust=False).mean()
    return 100 - (100 / (1 + (up / down.replace(0, 0.001))))

def main():
    try:
        current_total = MY_SEED + MY_DEBT
        rate = get_exchange_rate()
        today = datetime.now()
        
        # 1. 실시간 월 자산 증가율 계산
        elapsed_days = max((today - START_DATE).days, 1)
        daily_rate = (current_total / START_TOTAL_SEED) ** (1 / elapsed_days) - 1
        monthly_growth_rate = ((1 + daily_rate) ** 30.44 - 1) * 100
        
        # 2. 리포트 헤더
        report = f"📅 {today.strftime('%Y-%m-%d')}\n💰 [Mason Asset Report v4.5]\n"
        report += f"------------------\n"
        report += f"🚀 총 가용시드: {current_total:,.0f}만\n"
        report += f"📊 월 자산 증가율: {monthly_growth_rate:+.2f}%\n"
        report += f"ㄴ ({elapsed_days}일간의 지독한 성장 기록)\n"
        report += f"------------------\n"

        # 3. 보유 함대 분석
        daily_budget_usd = ((current_total * 10000) / 3 / DIVISIONS) / rate
        
        if MY_HOLDINGS_RAW:
            report += "⚔️ [보유 함대 교전 상황]\n"
            holdings = MY_HOLDINGS_RAW.split(",")
            for h in holdings:
                try:
                    symbol, avg_p, qty = h.strip().split(":")
                    ticker = yf.Ticker(symbol); df = ticker.history(period="3mo")
                    cur_p = float(df['Close'].iloc[-1])
                    profit_pct = (cur_p - float(avg_p)) / float(avg_p) * 100
                    loc_p = cur_p * 1.1 # 사령관의 10% LOC 전술
                    buy_count = math.ceil(daily_budget_usd / cur_p)
                    
                    report += f"📍 {symbol} ({profit_pct:+.1f}%)\n"
                    report += f"ㄴ 평단: ${float(avg_p):.2f} / 현재: ${cur_p:.2f}\n"
                    report += f"🔥 LOC(+10%): ${loc_p:.2f} ({buy_count}개)\n\n"
                except: continue

        # 4. 신규 정찰 (RSI 기준)
        report += "📡 [신규 타겟 정찰]\n"
        found_cnt = 0
        for t in CANDIDATES:
            if MY_HOLDINGS_RAW and t in MY_HOLDINGS_RAW: continue 
            try:
                ticker = yf.Ticker(t); df = ticker.history(period="3mo")
                rsi = float(calculate_rsi(df['Close']).iloc[-1])
                if rsi <= (30 if t == "SQQQ" else 40):
                    price = float(df['Close'].iloc[-1])
                    buy_count = math.ceil(daily_budget_usd / price)
                    report += f"🎯 {t} (RSI: {rsi:.1f})\n"
                    report += f"ㄴ LOC가(+10%): ${price*1.1:.2f} ({buy_count}개)\n"
                    found_cnt += 1
            except: continue
        if found_cnt == 0: report += "✅ 사거리 내 신규 타겟 없음\n"

        # 5. 달성률
        target = 20000
        progress = (current_total / target) * 100
        report += f"\n🏁 [Goal: 2억 고지]\n🚩 현재 달성률: {progress:,.1f}%\n"
        report += "------------------\n지독하게 원칙 매수하십시오."
        
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      data={"chat_id": TELEGRAM_CHAT_ID, "text": report})
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
