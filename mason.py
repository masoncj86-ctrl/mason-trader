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

def get_rsi(ticker_symbol):
    try:
        data = yf.Ticker(ticker_symbol).history(period="1mo")
        if len(data) < 15: return 50
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        return (100 - (100 / (1 + rs))).iloc[-1]
    except:
        return 50

# 1. 유동적 자산 설정 (사령관님 공식: 시드(수익포함) + 대출)
# 시크릿에서 실시간으로 가져옵니다. 텔레그램으로 바꾸면 즉시 반영!
seed = float(os.environ.get("MY_SEED", "4000")) 
debt = float(os.environ.get("MY_DEBT", "5000"))
divisions = int(os.environ.get("MY_DIVISIONS", "40"))
holdings_str = os.environ.get("MY_HOLDINGS", "")

# 지독하게 정확한 예산 공식 (14,000만이 안 나오게 profit은 더하지 않습니다!)
total_budget = seed + debt 

total_purchase_krw = 0
report_lines = []

# 실시간 환율
try:
    rate = yf.Ticker("USDKRW=X").history(period="5d")['Close'].iloc[-1]
except:
    rate = 1380.0

# 2. 보유 종목 정밀 분석 (평단/수량 위치 교정)
if holdings_str:
    holdings = [h.strip() for h in holdings_str.split(",") if ":" in h]
    for h in holdings:
        try:
            parts = h.split(":")
            ticker_symbol = parts[0].upper()
            avg_price = float(parts[1]) # 두 번째: 평단 (소수점 보존!)
            quantity = float(parts[2])  # 세 번째: 수량 (3주 등)
            
            ticker = yf.Ticker(ticker_symbol)
            hist = ticker.history(period="5d")
            
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                # 매수 원금 계산
                purchase_krw = (avg_price * quantity * rate) / 10000
                total_purchase_krw += purchase_krw
                
                profit_rate = (current_price - avg_price) / avg_price * 100
                rsi_val = get_rsi(ticker_symbol)
                
                # RSI 40 이하 매수 시그널 및 출력 양식 고정
                signal = " 🚨[매수 권고]" if rsi_val <= 40 else ""
                report_lines.append(
                    f"• *{ticker_symbol}*: 현재 ${current_price:.2f}\n"
                    f"  └ [평단: ${avg_price:.2f}] / [보유: {quantity:.2f}주] | RSI: {rsi_val:.1f}{signal}"
                )
        except:
            continue

# 3. 최종 결과 도출
available_seed = total_budget - total_purchase_krw

final_report = f"""
🚀 **사령관님, 함대 자산 정밀 보고**
---
💰 **총 작전 예산**: {total_budget:,.0f}만 원 (유동 반영)
📉 **현재 투입 원금**: {total_purchase_krw:,.0f}만 원
💵 **남은 가용 시드**: {available_seed:,.0f}만 원

💡 **분할 매수 전략** ({divisions}분할)
• 회당 투입액: *{available_seed/divisions:,.0f}만 원*

📊 **보유 종목 및 RSI 현황**
""" + "\n".join(report_lines) + f"\n\n기준 환율: ₩{rate:.2f}"

send_telegram_message(final_report)
