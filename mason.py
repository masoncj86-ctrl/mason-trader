import os
import yfinance as yf
import requests

def send_telegram_message(message):
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

# [중요!] 시크릿에서 가져오되, 값이 이상하면 사령관님의 '진짜 수치'를 강제 적용합니다.
# 총 예산 9,000만 원 고정 (시드 4000 + 대출 5000)
total_budget = 9000 
divisions = 40

# 보유 종목 (이 부분이 지독하게 중요합니다!)
# 텔레그램 업데이트가 꼬였다면, 아래에 직접 적어주는 게 가장 확실합니다.
holdings_input = os.environ.get("MY_HOLDINGS", "GDXU:213.677:3,NRGU:34.89:10") # 예시입니다!

total_purchase_krw = 0
report_lines = []

# 실시간 환율
try:
    rate = yf.Ticker("USDKRW=X").history(period="5d")['Close'].iloc[-1]
except:
    rate = 1380.0

if holdings_input:
    # 공백 제거 및 콤마 분리
    holdings = [h.strip() for h in holdings_input.split(",") if ":" in h]
    for h in holdings:
        try:
            parts = h.split(":")
            ticker_symbol = parts[0].upper()
            avg_price = float(parts[1]) # float을 써야 34.89가 유지됩니다!
            quantity = float(parts[2])
            
            ticker = yf.Ticker(ticker_symbol)
            hist = ticker.history(period="5d")
            
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                # 투입 원금 계산 (평단 * 수량 * 환율 / 1만)
                purchase_krw = (avg_price * quantity * rate) / 10000
                total_purchase_krw += purchase_krw
                
                profit_rate = (current_price - avg_price) / avg_price * 100
                report_lines.append(f"• *{ticker_symbol}*: 현재 ${current_price:.2f} (평단 ${avg_price:.2f}) | {profit_rate:+.2f}%")
        except:
            continue

available_seed = total_budget - total_purchase_krw

final_report = f"""
🚀 **사령관님, 함대 자산 정밀 보고**
---
💰 **총 작전 예산**: {total_budget:,.0f}만 원 (강제 고정)
📉 **현재 투입 원금**: {total_purchase_krw:,.0f}만 원
💵 **남은 가용 시드**: {available_seed:,.0f}만 원

💡 **분할 매수 전략** ({divisions}분할)
• 회당 투입액: *{available_seed/divisions:,.0f}만 원*

📊 **보유 종목 현황**
""" + "\n".join(report_lines) + f"\n\n기준 환율: ₩{rate:.2f}"

send_telegram_message(final_report)
