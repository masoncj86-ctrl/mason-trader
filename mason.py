import os
import yfinance as yf
import requests

def send_telegram_message(message):
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

# 1. 자산 데이터 설정 (사령관님의 공식 적용!)
seed = float(os.environ.get("MY_SEED", "4000")) # 수익금이 포함된 순수 자산
debt = float(os.environ.get("MY_DEBT", "5000")) # 대출 병력
divisions = int(os.environ.get("MY_DIVISIONS", "40"))
holdings_str = os.environ.get("MY_HOLDINGS", "")

total_budget = seed + debt  # 딱 9,000만 원으로 고정! ㅋㅋㅋ
total_purchase_krw = 0      # 주식을 살 때 들어간 원화 총액
report_lines = []

# 실시간 환율 (원화 환산을 위해 필요)
try:
    rate = yf.Ticker("USDKRW=X").history(period="1d")['Close'].iloc[-1]
except:
    rate = 1380.0 # 환율 통신 실패 시 기본값

if holdings_str:
    holdings = holdings_str.split(",")
    for h in holdings:
        ticker_symbol, avg_price_str, qty_str = h.split(":")
        avg_price = float(avg_price_str) # 소수점 평단 지독하게 인식!
        quantity = float(qty_str)        # 수량 인식
        
        # 현재가 정보
        ticker = yf.Ticker(ticker_symbol)
        current_price = ticker.history(period="1d")['Close'].iloc[-1]
        
        # 원화 매수 금액 계산 (평단 * 수량 * 환율 / 1만)
        purchase_krw = (avg_price * quantity * rate) / 10000
        total_purchase_krw += purchase_krw
        
        # 수익률 및 종목 보고서
        profit_rate = (current_price - avg_price) / avg_price * 100
        report_lines.append(f"• *{ticker_symbol}*: 현재 ${current_price:.2f} (평단 ${avg_price:.2f}) | 수익률: {profit_rate:+.2f}%")

# 2. 지독하게 정확한 가용 시드 계산
available_seed = total_budget - total_purchase_krw

final_report = f"""
🚀 **사령관님, 함대 자산 정밀 보고**
---
💰 **총 작전 예산**: {total_budget:,.0f}만 원
📉 **현재 투입 원금**: {total_purchase_krw:,.0f}만 원
💵 **남은 가용 시드**: {available_seed:,.0f}만 원

💡 **분할 매수 전략** ({divisions}분할 기준)
• 회당 투입 가능액: *{available_seed/divisions:,.0f}만 원*

📊 **보유 종목 현황**
""" + "\n".join(report_lines) + f"\n\n기준 환율: ₩{rate:.2f}"

send_telegram_message(final_report)
