import yfinance as yf
import requests
import math
import pandas as pd
import threading
import sys
import json
import os
from datetime import datetime

# --- [1. 설정 정보 (클라우드 대응)] ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8278038145:AAFa9Y-RJhcW12SKtGOnqGNQW7w1q9ErPCY")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "5466858773")

DEFAULT_SEED = os.environ.get("MY_SEED", "5500")
DEFAULT_HOLDINGS = os.environ.get("MY_HOLDINGS", "TSLL,LABU")

CANDIDATES = ["LABU", "TNA", "TSLL", "SOXL", "NRGU", "GDXU", "IONX", "FNGU"]
MAX_HOLDINGS = 3    
DIVISIONS = 20      

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(BASE_DIR, "mason_settings.json")

# --- [2. 핵심 로직 클래스] ---
class MasonLogic:
    def __init__(self):
        self.settings = self.load_settings()

    def load_settings(self):
        default = {"seed": DEFAULT_SEED, "holdings": DEFAULT_HOLDINGS, "last_run_date": ""}
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except: return default
        return default

    def save_settings(self, seed, holdings, update_date=False):
        if os.environ.get("GITHUB_ACTIONS") == "true":
            return
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
        return 100 - (100 / (1 + (ma_up / ma_down)))

    def send_telegram(self, message):
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": message}, timeout=10)
        except Exception as e: print(f"Telegram Error: {e}")

    def perform_analysis(self, seed_str, holdings_str, is_auto=False, logger=None):
        try:
            print(f"Start Analysis... Seed: {seed_str}, Holdings: {holdings_str}")
            seed_money = float(str(seed_str).replace(',', ''))
            my_holdings = [t for t in str(holdings_str).upper().replace(' ', '').split(',') if t]
            
            rate = self.get_exchange_rate()
            daily_budget_usd = ((seed_money * 10000) / MAX_HOLDINGS / DIVISIONS) / rate

            if logger: logger(f"SEED: {seed_money:,.0f} MAN-WON | RATE: {rate:.1f}")
            
            date_display = datetime.now().strftime("%Y년 %m월 %d일")
            final_report = f"📅 {date_display}\n🌅 [Mason Daily Report]\nSEED: {seed_money:,.0f}만원 / RATE: {rate:.1f}원\n"
            
            found_cnt = 0
            for ticker in CANDIDATES:
                try:
                    df = yf.download(ticker, period="3mo", progress=False)
                    if df.empty or len(df) < 20: continue
                    close = df['Close'].squeeze()
                    rsi = float(self.calculate_rsi_wilder(close).iloc[-1])
                    last_close = float(close.iloc[-1])
                    buy_qty = math.ceil(daily_budget_usd / last_close)

                    if rsi <= 40:
                        found_cnt += 1
                        final_report += f"\n🚀 [NEW] {ticker}\nRSI: {rsi:.1f} / PRICE: ${last_close:.2f}\nQTY: {buy_qty}\n"
                        if logger: logger(f" [HIT] {ticker} RSI:{rsi:.1f}")
                except Exception as e: print(f"Error checking {ticker}: {e}")

            if found_cnt == 0: final_report += "\n✅ No new candidates (RSI > 40).\n"

            if my_holdings:
                for ticker in my_holdings:
                    try:
                        df = yf.download(ticker, period="3mo", progress=False)
                        if df.empty: continue
                        close = df['Close'].squeeze()
                        rsi = float(self.calculate_rsi_wilder(close).iloc[-1])
                        last_close = float(close.iloc[-1])
                        buy_qty = math.ceil(daily_budget_usd / last_close)
                        loc_price = last_close * 1.10
                        final_report += f"\n📦 [HOLDING] {ticker}\nRSI: {rsi:.1f} / QTY: {buy_qty}\nLOC(10%): ${loc_price:.2f}\n"
                    except Exception as e: print(f"Error checking holding {ticker}: {e}")

            final_report += "\n------------------\nEND OF REPORT."
            self.send_telegram(final_report)
            
            if is_auto:
                self.save_settings(seed_str, holdings_str, update_date=True)
                print("✅ [SUCCESS] Report sent.")

        except Exception as e:
            if logger: logger(f"[ERROR] {e}")
            print(f"[ERROR] {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--auto":
        logic = MasonLogic()
        seed_val = os.environ.get("MY_SEED", logic.settings.get("seed", "4000"))
        holdings_val = os.environ.get("MY_HOLDINGS", logic.settings.get("holdings", ""))
        print(">>> Starting Auto Analysis (Cloud Mode)...")
        logic.perform_analysis(seed_val, holdings_val, is_auto=True)

