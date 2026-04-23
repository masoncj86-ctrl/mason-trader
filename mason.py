import os
import yfinance as yf
import requests
import pandas as pd

def send_telegram_message(message):
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

# 1. 자산 데이터 설정 (사령관님 공식: 시드+대출 = 9,000만 고정)
seed = float(os.environ.get("MY_SEED", "4000"))
debt = float(os.environ.get("MY_DEBT", "5000"))
divisions = int(os.environ.get("MY_DIVISIONS", "40"))
holdings_str = os.environ.get("MY_HOLDINGS", "")
total_budget = seed + debt # 14,000만 원 원천 차단! ㅋㅋㅋ

total_purchase_krw = 0
report_lines = []
buy_signals = []

# 실시간 환율 및 RSI 계산 함수
try:
    rate = yf.Ticker("USDKRW=X").history(period="1d")['Close'].iloc[-1]
except:
    rate = 1380.0

def get_rsi(ticker_symbol):
    try:
        data = yf.Ticker(ticker_symbol).history(period="1mo")
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs)).iloc[-1]
    except:
        return 50 # 에러 시 중립

# 2. 보유 종목 분석
if holdings_str:
    holdings = [h.strip() for h in holdings_str.split(",") if h.strip()]
    for h in holdings:
        try:
            ticker_symbol, avg_price_str, qty_str = h.split(":")
            avg_price = float(avg_price_str) # 소수점(34.89 등) 지독하게 유지!
            quantity = float(qty_str)
            
            ticker = yf.Ticker(ticker_symbol)
            hist = ticker.history(period="5d")
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                purchase_krw = (avg_price * quantity * rate) / 10000
                total_purchase_krw += purchase_krw
                
                profit_rate = (current_price - avg_price) / avg_price * 100
                rsi_val = get_rsi(ticker_symbol)
                
                # RSI 40 이하 매수 시그널 포착!
                signal_tag = "🚨 [매수 추천]" if rsi_val <= 40 else ""
                report_lines.append(f"• *{ticker_symbol}*: ${current_price:.2f} (평단 ${avg_price:.2f}) | {profit_rate:+.2f}% (RSI: {rsi_val:.1f}) {signal_tag}")
        except Exception as e:
            continue

# 3. 가용 시드 계산
available_seed = total_budget - total_purchase_krw

final_report = f"""
🚀 **사령관님, 함대 자산 정밀 보고**
---
💰 **총 작전 예산**: {total_budget:,.0f}만 원 (고정)
📉 **현재 투입 원금**: {total_purchase_krw:,.0f}만 원
💵 **남은 가용 시드**: {available_seed:,.0f}만 원

💡 **분할 매수 전략** ({divisions}분할)
• 회당 투입액: *{available_seed/divisions:,.0f}만 원*

📊 **보유 종목 및 RSI 현황**
""" + "\n".join(report_lines) + f"\n\n기준 환율: ₩{rate:.2f}"

send_telegram_message(final_report)
