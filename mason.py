import yfinance as yf
import requests
import math
import pandas as pd
import os
import json
import sys
from datetime import datetime, timedelta

# --- [1. 설정 정보 (클라우드 대응)] ---
# 기본값을 "NONE"으로 변경하여, 변수가 설정되지 않았을 때의 중복 실행을 방지합니다.
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8278038145:AAFa9Y-RJhcW12SKtGOnqGNQW7w1q9ErPCY")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "5466858773")

# [수정] 기본값을 "NONE"으로 설정하여 가짜 데이터(5500) 생성을 차단합니다.
DEFAULT_SEED = os.environ.get("MY_SEED", "NONE")
DEFAULT_HOLDINGS = os.environ.get("MY_HOLDINGS", "NONE")

CANDIDATES = ["LABU", "TNA", "TSLL", "SOXL", "NRGU", "GDXU", "IONX", "FNGU"]
MAX_HOLDINGS = 3    
DIVISIONS = 20      

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(BASE_DIR, "mason_settings.json")

class MasonLogic:
    def __init__(self):
        self.settings = self.load_settings()

    def load_settings(self):
        default = {"seed": "NONE", "holdings": "NONE", "last_run_date": ""}
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except: return default
        return default

    def save_settings(self, seed, holdings, update_date=False):
        if os.environ.get("GITHUB_ACTIONS") == "true": return
        data = {
            "seed": seed,
            "holdings": holdings,
            "last_run_date": datetime.now().strftime("%Y-%m-%d") if update_date else self.settings.get("last_run_date", "")
        }
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
        except: pass

    def get_exchange_rate(self):
        try:
            res = requests.get("https://open.er-api.com/v6/latest/USD", timeout=5).json()
            return float(res['rates']['KRW'])
        except: return 1450.0

    def calculate_rsi_wilder(self, series, period=14):
        delta = series.diff()
        up = delta.clip(lower=0)
        down = -1 * delta.clip(upper=0)
        ma_up = up.ewm(com=period - 1, adjust=False).mean()
        ma_down = down.ewm(com=period - 1, adjust=False).mean()
        ma_down = ma_down.replace(0, 0.001) # 0 나누기 방지
        return 100 - (100 / (1 + (ma_up / ma_down)))

    def send_telegram(self, message):
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": message}, timeout=10)
        except Exception as e: print(f"Telegram Error: {e}")

    def perform_analysis(self, seed_str, holdings_str, is_auto=False):
        # [핵심 로직] 변수가 "NONE"이거나 기본값이면 실행하지 않고 종료합니다.
        if seed_str == "NONE" or seed_str == "5500":
            print(">>> [SKIP] Real Variable not set. Skipping report.")
            return

        try:
            seed_money = float(str(seed_str).replace(',', ''))
            my_holdings = [t for t in str(holdings_str).upper().replace(' ', '').split(',') if t and t != "NONE"]
            
            rate = self.get_exchange_rate()
            # 1일 매수 예산 산출
            daily_budget_usd = ((seed_money * 10000) / MAX_HOLDINGS / DIVISIONS) / rate

            date_display = datetime.now().strftime("%Y년 %m월 %d일")
            final_report = f"📅 {date_display}\n🌅 [Mason Real-Time Report]\nSEED: {seed_money:,.0f}만원 / DIV: {DIVISIONS}\nRATE: {rate:.1f}원\n"
            
            # 신규 후보군 분석
            found_cnt = 0
            for ticker in CANDIDATES:
                try:
                    df = yf.download(ticker, period="3mo", progress=False)
                    if df.empty or len(df) < 20: continue
                    close = df['Close'].iloc[:, 0] if isinstance(df['Close'], pd.DataFrame) else df['Close']
                    
                    rsi = float(self.calculate_rsi_wilder(close).iloc[-1])
                    last_close = float(close.iloc[-1])
                    buy_qty = math.ceil(daily_budget_usd / last_close)

                    if rsi <= 40:
                        found_cnt += 1
                        final_report += f"\n🚀 [NEW] {ticker}\nRSI: {rsi:.1f} / PRICE: ${last_close:.2f}\nQTY: {buy_qty}\n"
                except: continue

            if found_cnt == 0: final_report += "\n✅ 신규 진입 후보 없음 (RSI > 40)\n"

            # 현재 보유 종목 분석
            if my_holdings:
                for ticker in my_holdings:
                    try:
                        df = yf.download(ticker, period="3mo", progress=False)
                        if df.empty: continue
                        close = df['Close'].iloc[:, 0] if isinstance(df['Close'], pd.DataFrame) else df['Close']
                        rsi = float(self.calculate_rsi_wilder(close).iloc[-1])
                        last_close = float(close.iloc[-1])
                        buy_qty = math.ceil(daily_budget_usd / last_close)
                        loc_price = last_close * 1.10
                        final_report += f"\n📦 [HOLDING] {ticker}\nRSI: {rsi:.1f} / QTY: {buy_qty}\nLOC(10%): ${loc_price:.2f}\n"
                    except: continue

            # [2억 목표 달성 시뮬레이션]
            target_goal = 20000 
            if seed_money < target_goal:
                # 월 5% 복리 + 월 600만 보급 적용 시뮬레이션 (사령관님 맞춤형)
                months = 0
                temp_seed = seed_money
                while temp_seed < target_goal and months < 120:
                    temp_seed = (temp_seed * 1.05) + 600
                    months += 1
                
                expected_date = datetime.now() + timedelta(days=months * 30)
                achievement_rate = (seed_money / target_goal) * 100
                
                final_report += f"\n🎯 [2억 달성 프로젝트]\n현재 달성률: {achievement_rate:.1f}%\n예상 달성일: {expected_date.strftime('%Y년 %m월 %d일')}\n(월 5% 수익 + 600만 보급 가정)\n"
            
            final_report += "\n------------------\n사령관님, 지독하게 원칙 매수하십시오!"
            self.send_telegram(final_report)
            
            if is_auto:
                self.save_settings(seed_str, holdings_str, update_date=True)

        except Exception as e:
            print(f"[ERROR] {e}")

if __name__ == "__main__":
    logic = MasonLogic()
    # 1. 환경 변수(Variable) 최우선
    # 2. 없으면 로컬 설정파일
    # 3. 둘 다 없으면 "NONE"
    seed_val = os.environ.get("MY_SEED", logic.settings.get("seed", "NONE"))
    holdings_val = os.environ.get("MY_HOLDINGS", logic.settings.get("holdings", "NONE"))
    
    # --auto 인자가 있든 없든, 실제 데이터가 있을 때만 실행하도록 통합
    logic.perform_analysis(seed_val, holdings_val, is_auto=True)
