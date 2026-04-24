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
# 연도 포함 한국 시간(KST) 기준
now = datetime.utcnow() + timedelta(hours=9)
date_header = now.strftime("%Y년 %m월 %d일 %H:%M")

seed = float(os.environ.get("MY_SEED", "4000"))
debt = float(os.environ.get("MY_DEBT", "5000"))
divisions = int(os.environ.get("MY_DIVISIONS", "40"))
holdings_str = os.environ.get("MY_HOLDINGS", "")

# 지독하게 정확한 9,000만 원 예산 (시드+대출)
total_budget = seed + debt 

# [지독한 교정] 회당 투입액 = 총 작전 예산 / 분할수
investment_per_turn = total_budget / divisions

total_purchase_krw = 0
holdings_report = []
candidates_report = []

# 실시간 환율
try:
    rate = yf.Ticker("USDKRW=X").history(period="5d")['Close'].iloc[-1]
except: rate = 1380.0

# --- [2. 보유 종목 정밀 분석 (사령관님 입력순서: 종목:수량:평단)] ---
if holdings_str:
    holdings = [h.strip() for h in holdings_str.split(",") if ":" in h]
    for h in holdings:
        try:
            parts = h.split(":")
            ticker_symbol = parts[0].upper()
            
            # [지독한 확인] 사령관님 입력 방식: GDXU:3:213.677
            quantity = float(parts[1])  # 두 번째 값이 '수량' (예: 3)
            avg_price = float(parts[2]) # 세 번째 값이 '평단' (예: 213.677)
            
            ticker = yf.Ticker(ticker_symbol)
            hist = ticker.history(period="5d")
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                # 투입 원금 계산 (평단 * 수량 * 환율 / 10,000)
                purchase_krw = (avg_price * quantity * rate) / 10000
                total_purchase_krw += purchase_krw
                profit_rate = (current_price - avg_price) / avg_price * 100
                rsi_val = get_rsi(ticker_symbol)
                signal = " 🚨[매수 권고]" if rsi_val <= 40 else ""
                
                # 리포트에서 평단과 수량을 명확하게 구분하여 출력
                holdings_report.append(
                    f"• *{ticker_symbol}*: 현재 ${current_price:.2f}\n"
                    f"  └ [평단: ${avg_price:.2f}] / [보유: {quantity:.2f}주]\n"
                    f"  └ 수익률: {profit_rate:+.2f}% / RSI: {rsi_val:.1f}{signal}"
                )
        except: continue

# --- [3. 후보 종목 RSI 정찰 (TNA, LABU 포함)] ---
candidate_tickers = ["TNA", "LABU", "TSLL", "GDXU", "NRGU", "SQQQ", "FNGU", "SOXL", "TQQQ"]
for ticker_symbol in candidate_tickers:
    rsi_val = get_rsi(ticker_symbol)
    signal = " 🚨[매수 권고]" if rsi_val <= 40 else ""
    candidates_report.append(f"• *{ticker_symbol}*: RSI {rsi_val:.1f}{signal}")

# --- [4. 최종 리포트 구성] ---
available_seed = total_budget - total_purchase_krw

final_report = f"""
📅 **{date_header} 함대 작전 리포트**
---
💰 **총 작전 예산**: {total_budget:,.0f}만 원 (시드+대출)
📉 **현재 투입 원금**: {total_purchase_krw:,.0f}만 원
💵 **남은 가용 시드**: {available_seed:,.0f}만 원

💡 **분할 매수 전략** ({divisions}분할 기준)
• 회당 투입 가능액: *{investment_per_turn:,.0f}만 원* (총 예산 기준)

📊 **보유 종목 현황**
""" + ("\n".join(holdings_report) if holdings_report else "보유 종목 없음") + """

🔍 **핵심 후보 정찰 (RSI 40이하 권고)**
""" + "\n".join(candidates_report) + f"\n\n기준 환율: ₩{rate:.2f}"

send_telegram_message(final_report)
