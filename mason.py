import os
import yfinance as yf
import requests
import pandas as pd
from datetime import datetime, timedelta

def send_telegram_message(message):
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

def get_rsi(ticker_symbol):
    try:
        # 최근 2개월 데이터를 가져와 EMA 방식으로 정밀 RSI 계산
        data = yf.Ticker(ticker_symbol).history(period="2mo")
        if len(data) < 20: return 50
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0))
        loss = (-delta.where(delta < 0, 0))
        avg_gain = gain.ewm(com=13, min_periods=14).mean()
        avg_loss = loss.ewm(com=13, min_periods=14).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1]
    except: return 50

# --- [1. 날짜 및 자산 설정] ---
now = datetime.utcnow() + timedelta(hours=9)
date_header = now.strftime("%Y년 %m월 %d일 %H:%M")

seed = float(os.environ.get("MY_SEED", "4000"))
debt = float(os.environ.get("MY_DEBT", "5000"))
profit = float(os.environ.get("MY_PROFIT", "2088")) # 사령관님의 전리품
divisions = int(os.environ.get("MY_DIVISIONS", "40"))
holdings_str = os.environ.get("MY_HOLDINGS", "")

total_budget = seed + debt 
investment_per_turn = total_budget / divisions # 분할 매수 금액
target_goal = 20000 
achievement_rate = (total_budget / target_goal) * 100

total_purchase_krw = 0
holdings_report = []
candidates_report = []

# 실시간 환율
try:
    rate = yf.Ticker("USDKRW=X").history(period="5d")['Close'].iloc[-1]
except: rate = 1380.0

# --- [2. 보유 종목 분석 및 LOC 계산] ---
if holdings_str:
    holdings = [h.strip() for h in holdings_str.split(",") if ":" in h]
    for h in holdings:
        try:
            parts = h.split(":")
            ticker_symbol = parts[0].upper()
            quantity = float(parts[1])
            avg_price = float(parts[2])
            
            ticker = yf.Ticker(ticker_symbol)
            hist = ticker.history(period="5d")
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                purchase_krw = (avg_price * quantity * rate) / 10000
                total_purchase_krw += purchase_krw
                profit_rate = (current_price - avg_price) / avg_price * 100
                rsi_val = get_rsi(ticker_symbol)
                
                # 시그널: RSI 40 이하 시 사이렌만 표시
                signal = " 🚨" if rsi_val <= 40 else ""
                
                # LOC 계산: 현재가+10%, 수량은 정수로 올림(int)
                loc_price = current_price * 1.1
                loc_budget_usd = (investment_per_turn * 10000 / rate) / 3
                loc_qty = int(loc_budget_usd / loc_price)
                
                holdings_report.append(
                    f"• *{ticker_symbol}*: 현재가 ${current_price:.2f}\n"
                    f"  └ [평단: ${avg_price:.2f}] / [보유: {quantity:.2f}주]\n"
                    f"  └ 수익률: {profit_rate:+.2f}% / RSI: {rsi_val:.1f}{signal}\n"
                    f"  └ LOC: ${int(loc_price)} / {loc_qty}주"
                )
        except: continue

# --- [3. 후보 종목 정찰 (3종목 미만 보유 시에만 작동)] ---
if len(holdings_report) < 3:
    candidate_tickers = ["TNA", "LABU", "TSLL", "GDXU", "NRGU", "SQQQ", "FNGU", "SOXL", "TQQQ"]
    for ticker_symbol in candidate_tickers:
        rsi_val = get_rsi(ticker_symbol)
        if rsi_val <= 40: # 조건 만족하는 것만 리포트 포함
            ticker = yf.Ticker(ticker_symbol)
            hist = ticker.history(period="5d")
            if not hist.empty:
                curr = hist['Close'].iloc[-1]
                l_price = int(curr * 1.1)
                l_qty = int(((investment_per_turn * 10000 / rate) / 3) / l_price)
                candidates_report.append(f"• *{ticker_symbol}* 🚨 (RSI: {rsi_val:.1f})\n  └ LOC: ${l_price} / {l_qty}주")

# --- [4. 최종 리포트 구성] ---
available_seed = total_budget - total_purchase_krw

final_report = f"""
📅 **{date_header} MASON STOCK REPORT**
---
🏁 **2억 목표 달성률**: {achievement_rate:.1f}%

💰 **작전 예산 상세**
• 총 예산: {total_budget:,.0f}만 원
  └ 💵 순수 시드: {seed:,.0f}만 원
  └ 🏦 대출 병력: {debt:,.0f}만 원
  └ 🏆 수익: {profit:,.0f}만
• 분할 매수 금액: {investment_per_turn:,.0f}만 원
• 남은 가용 시드: {available_seed:,.0f}만 원

📊 **보유 종목**
""" + ("\n".join(holdings_report) if holdings_report else "보유 종목 없음")

if candidates_report:
    final_report += f"\n\n🔍 **핵심 후보 정찰 (RSI 40이하)**\n" + "\n".join(candidates_report)

final_report += f"\n\n기준 환율: ₩{rate:.2f}"

send_telegram_message(final_report)
