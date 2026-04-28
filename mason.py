import os
import yfinance as yf
import requests
import pandas as pd
from datetime import datetime, timedelta

# --- [사령관 지휘 계통: 텔레그램 발송] ---
def send_telegram_message(message):
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"발송 실패: {e}")

# --- [정찰 레이더: RSI 계산 엔진] ---
def get_rsi(ticker_symbol):
    try:
        # 데이터 누락 방지를 위해 넉넉하게 3개월치 조회
        ticker = yf.Ticker(ticker_symbol)
        data = ticker.history(period="3mo")
        if len(data) < 20: return 50
        
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0))
        loss = (-delta.where(delta < 0, 0))
        
        avg_gain = gain.ewm(com=13, min_periods=14).mean()
        avg_loss = loss.ewm(com=13, min_periods=14).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1]
    except:
        return 50 # 에러 발생 시 중립 수치 반환

# --- [1. 작전 상황 설정] ---
now = datetime.utcnow() + timedelta(hours=9)
date_header = now.strftime("%Y년 %m월 %d일 %H:%M")

# 예산 데이터 (환경 변수에서 호출)
seed = float(os.environ.get("MY_SEED", "4000"))
debt = float(os.environ.get("MY_DEBT", "5000"))
profit = float(os.environ.get("MY_PROFIT", "2088"))
divisions = int(os.environ.get("MY_DIVISIONS", "40"))
holdings_str = os.environ.get("MY_HOLDINGS", "").strip()

total_budget = seed + debt 
investment_per_turn = total_budget / divisions
target_goal = 20000 
achievement_rate = (total_budget / target_goal) * 100

total_purchase_krw = 0
holdings_report = []
candidates_report = []

# 실시간 환율 (USDKRW)
try:
    rate = yf.Ticker("USDKRW=X").history(period="5d")['Close'].iloc[-1]
except:
    rate = 1380.0 # 환율 서버 비상 시 고정 환율 적용

# --- [2. 보유 종목 정밀 분석] ---
if holdings_str:
    # 쉼표(,)나 세미콜론(;)으로 구분된 종목들을 지독하게 분리
    raw_items = holdings_str.replace(";", ",").split(",")
    for item in raw_items:
        if ":" not in item: continue
        try:
            # 티커, 수량, 평단에서 모든 잡음(공백, 콤마 등) 제거
            parts = item.split(":")
            ticker_symbol = parts[0].strip().upper()
            quantity = float(parts[1].strip())
            avg_price = float(parts[2].strip())
            
            ticker = yf.Ticker(ticker_symbol)
            # NRGU 등 특정 종목의 지연 방지를 위해 최근 1주일치 중 가장 최신 데이터 확보
            hist = ticker.history(period="7d")
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                # 원화 환산 투입 금액 계산
                purchase_krw = (avg_price * quantity * rate) / 10000
                total_purchase_krw += purchase_krw
                
                profit_rate = (current_price - avg_price) / avg_price * 100
                rsi_val = get_rsi(ticker_symbol)
                
                # 시그널: RSI 40 이하 시 사이렌만 표시
                signal = " 🚨" if rsi_val <= 40 else ""
                
                # [LOC 전략 가이드]
                # 가격: 현재가 + 10% (무조건 체결), 예산: 회당 투입액의 1/3 (달러 환산)
                loc_price = current_price * 1.1
                loc_budget_usd = (investment_per_turn * 10000 / rate) / 3
                loc_qty = int(loc_budget_usd / loc_price)
                
                holdings_report.append(
                    f"• *{ticker_symbol}*: 현재가 ${current_price:.2f}\n"
                    f"  └ [평단: ${avg_price:.2f}] / [보유: {quantity:.2f}주]\n"
                    f"  └ 수익률: {profit_rate:+.2f}% / RSI: {rsi_val:.1f}{signal}\n"
                    f"  └ LOC: ${int(loc_price)} / {loc_qty}주"
                )
        except Exception as e:
            print(f"{item} 처리 중 오류: {e}")
            continue

# --- [3. 핵심 후보 정찰 (3종목 미만 보유 시 작동)] ---
current_holding_count = len(holdings_report)
if current_holding_count < 3:
    candidate_tickers = ["TNA", "LABU", "TSLL", "GDXU", "NRGU", "SQQQ", "FNGU", "SOXL", "TQQQ"]
    for ticker_symbol in candidate_tickers:
        # 이미 보유 중인 종목은 후보군에서 제외
        if any(ticker_symbol in r for r in holdings_report): continue
        
        rsi_val = get_rsi(ticker_symbol)
        if rsi_val <= 40: # 매수 기회인 녀석들만 골라냄
            try:
                ticker = yf.Ticker(ticker_symbol)
                hist = ticker.history(period="5d")
                if not hist.empty:
                    curr = hist['Close'].iloc[-1]
                    l_price = int(curr * 1.1)
                    l_qty = int(((investment_per_turn * 10000 / rate) / 3) / l_price)
                    candidates_report.append(
                        f"• *{ticker_symbol}* 🚨 (RSI: {rsi_val:.1f})\n"
                        f"  └ LOC: ${l_price} / {l_qty}주"
                    )
            except: continue

# --- [4. 최종 리포트 구성 및 발송] ---
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
