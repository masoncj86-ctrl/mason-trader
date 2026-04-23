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

total_budget = seed + debt
total_purchase_krw = 0
report_lines = []

# 실시간 환율 가져오기
try:
    rate = yf.Ticker("USDKRW=X").history(period="1d")['Close'].iloc[-1]
except:
    rate = 1380.0

if holdings_str:
    holdings = [h.strip() for h in holdings_str.split(",") if h.strip()]
    for h in holdings:
        try:
            ticker_symbol, avg_price_str, qty_str = h.split(":")
            avg_price = float(avg_price_str)
            quantity = float(qty_str)
            
            # [방어 로직] 데이터가 없을 경우를 대비해 period를 5d로 늘려 최신값을 찾습니다.
            ticker = yf.Ticker(ticker_symbol)
            hist = ticker.history(period="5d")
            
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
            else:
                # 야후가 끝까지 안 주면 '정보 없음'으로 처리
                current_price = 0
            
            if current_price > 0:
                purchase_krw = (avg_price * quantity * rate) / 10000
                total_purchase_krw += purchase_krw
                profit_rate = (current_price - avg_price) / avg_price * 100
                report_lines.append(f"• *{ticker_symbol}*: ${current_price:.2f} (평단 ${avg_price:.2f}) | {profit_rate:+.2f}%")
            else:
                report_lines.append(f"• *{ticker_symbol}*: 데이터 호출 실패 (티커 확인 필요)")
        except Exception as e:
            report_lines.append(f"• 데이터 분석 오류: {str(e)}")

# 2. 자산 계산
available_seed = total_budget - total_purchase_krw

final_report = f"""
🚀 **사령관님, 함대 자산 정밀 보고**
---
💰 **총 작전 예산**: {total_budget:,.0f}만 원
📉 **현재 투입 원금**: {total_purchase_krw:,.0f}만 원
💵 **남은 가용 시드**: {available_seed:,.0f}만 원

💡 **분할 매수 전략** ({divisions}분할)
• 회당 투입액: *{available_seed/divisions:,.0f}만 원*

📊 **보유 종목 현황**
""" + "\n".join(report_lines) + f"\n\n기준 환율: ₩{rate:.2f}"

send_telegram_message(final_report)
