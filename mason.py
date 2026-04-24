import os
import yfinance as yf
import requests

def send_telegram_message(message):
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

# 1. 자산 데이터 설정 (시드+대출 = 9,000만 원)
seed = float(os.environ.get("MY_SEED", "4000"))
debt = float(os.environ.get("MY_DEBT", "5000"))
holdings_str = os.environ.get("MY_HOLDINGS", "")
total_budget = seed + debt

total_purchase_krw = 0
report_lines = []

# 실시간 환율
try:
    rate = yf.Ticker("USDKRW=X").history(period="5d")['Close'].iloc[-1]
except:
    rate = 1380.0

# 2. 보유 종목 정밀 분석
if holdings_str:
    # 텔레그램 입력 방식: /보유 종목:평단:수량 (예: GDXU:213.677:3)
    holdings = [h.strip() for h in holdings_str.split(",") if ":" in h]
    for h in holdings:
        try:
            parts = h.split(":")
            ticker_symbol = parts[0].upper()
            avg_price = float(parts[1])  # 두 번째 값이 '평단'입니다!
            quantity = float(parts[2])   # 세 번째 값이 '수량'입니다!
            
            ticker = yf.Ticker(ticker_symbol)
            hist = ticker.history(period="5d")
            
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                # 투입 원금 (원화) = 평단 * 수량 * 환율
                purchase_krw = (avg_price * quantity * rate) / 10000
                total_purchase_krw += purchase_krw
                
                profit_rate = (current_price - avg_price) / avg_price * 100
                
                # [지독한 교정] 리포트에서 평단과 수량을 명확히 구분하여 출력
                report_lines.append(
                    f"• *{ticker_symbol}*: 현재 ${current_price:.2f}\n"
                    f"  (평단: ${avg_price:.2f} / 보유: {quantity:.3f}주) | 수익: {profit_rate:+.2f}%"
                )
        except:
            continue

# 3. 최종 리포트 구성
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
