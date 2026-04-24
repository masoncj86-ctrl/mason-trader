import os
import yfinance as yf
import requests

def send_telegram_message(message):
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

# 1. 자산 데이터 설정
seed = float(os.environ.get("MY_SEED", "4000"))
debt = float(os.environ.get("MY_DEBT", "5000"))
divisions = int(os.environ.get("MY_DIVISIONS", "40"))
holdings_str = os.environ.get("MY_HOLDINGS", "")

total_budget = seed + debt  # 9,000만 원 고정
total_purchase_krw = 0
report_lines = []

# 실시간 환율
try:
    rate = yf.Ticker("USDKRW=X").history(period="5d")['Close'].iloc[-1]
except:
    rate = 1380.0

# 2. 보유 종목 정밀 분석
if holdings_str:
    holdings = [h.strip() for h in holdings_str.split(",") if ":" in h]
    for h in holdings:
        try:
            # [지독한 확인] 사령관님 입력: Ticker:평단:수량
            parts = h.split(":")
            ticker_symbol = parts[0].upper()
            avg_price = float(parts[1])  # 평단 (213.677 또는 34.89)
            quantity = float(parts[2])   # 수량 (3주 등)
            
            ticker = yf.Ticker(ticker_symbol)
            hist = ticker.history(period="5d")
            
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                # 매수 원금 계산 (평단 * 수량 * 환율 / 1만)
                purchase_krw = (avg_price * quantity * rate) / 10000
                total_purchase_krw += purchase_krw
                
                profit_rate = (current_price - avg_price) / avg_price * 100
                
                # 리포트 출력 양식 수정: 평단과 수량을 지독하게 구분!
                report_lines.append(f"• *{ticker_symbol}*: 현재 ${current_price:.2f} (평단: ${avg_price:.2f} / 보유: {quantity:.1f}주) | 수익률: {profit_rate:+.2f}%")
        except:
            continue

# 3. 가용 시드 계산
available_seed = total_budget - total_purchase_krw

final_report = f"""
🚀 **사령관님, 함대 자산 정밀 보고**
---
💰 **총 작전 예산**: {total_budget:,.0f}만 원
📉 **현재 투입 원금**: {total_purchase_krw:,.0f}만 원
💵 **남은 가용 시드**: {available_seed:,.0f}만 원

📊 **보유 종목 현황**
""" + "\n".join(report_lines) + f"\n\n기준 환율: ₩{rate:.2f}"

send_telegram_message(final_report)
