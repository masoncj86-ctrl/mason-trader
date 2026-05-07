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
        requests.post(url, json=payload, timeout=15)
    except Exception as e:
        print(f"발송 실패: {e}")

# --- [정찰 레이더: RSI 계산 엔진] ---
def get_rsi(ticker_symbol):
    try:
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
        return 50

# --- [1. 작전 상황 설정] ---
now = datetime.utcnow() + timedelta(hours=9)
date_header = now.strftime("%Y년 %m월 %d일 %H:%M")

seed = float(os.environ.get("MY_SEED", "4000"))
debt = float(os.environ.get("MY_DEBT", "5000"))
profit = float(os.environ.get("MY_PROFIT", "2088"))
divisions = int(os.environ.get("MY_DIVISIONS", "40"))
holdings_str = os.environ.get("MY_HOLDINGS", "").strip()

total_budget = seed + debt 
investment_per_turn = total_budget / divisions
# [지독한 타격액] 전체 예산의 1/20 (5%)
strike_investment = total_budget / 20

target_goal = 20000 
achievement_rate = (total_budget / target_goal) * 100

total_purchase_krw = 0
holdings_report = []
candidates_report = []

try:
    rate = yf.Ticker("USDKRW=X").history(period="5d")['Close'].iloc[-1]
except:
    rate = 1380.0

# --- [2. 보유 종목 정밀 분석 및 평단 최신화] ---
if holdings_str:
    raw_items = holdings_str.replace("\n", ",").replace(";", ",").split(",")
    for item in raw_items:
        item = item.strip()
        if ":" not in item: continue
        
        try:
            parts = [p.strip() for p in item.split(":")]
            if len(parts) < 3: continue
            
            ticker_symbol = parts[0].upper()
            quantity = float(parts[1])
            avg_price = float(parts[2])
            
            ticker = yf.Ticker(ticker_symbol)
            hist = ticker.history(period="7d")
            
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                purchase_krw = (avg_price * quantity * rate) / 10000
                total_purchase_krw += purchase_krw
                
                profit_rate = (current_price - avg_price) / avg_price * 100
                rsi_val = get_rsi(ticker_symbol)
                
                # [수정 로직] RSI 25 이하 특수 타격 판정
                if rsi_val <= 25:
                    signal = " 🚨[특수타격]"
                    loc_budget_usd = (strike_investment * 10000 / rate)
                else:
                    signal = " 🚨" if rsi_val <= 40 else ""
                    loc_budget_usd = (investment_per_turn * 10000 / rate) / 3
                
                loc_price = current_price * 1.1
                loc_qty = int(loc_budget_usd / loc_price) if loc_price > 0 else 0
                
                holdings_report.append(
                    f"• *{ticker_symbol}*: 현재가 ${current_price:.2f}\n"
                    f"  └ [평단: ${avg_price:.2f}] / [보유: {quantity:.2f}주]\n"
                    f"  └ 수익률: {profit_rate:+.2f}% / RSI: {rsi_val:.1f}{signal}\n"
                    f"  └ LOC: ${int(loc_price)} / {loc_qty}주"
                )
        except Exception as e:
            print(f"종목 분석 오류 ({item}): {e}")
            continue

# --- [3. 핵심 후보 정찰] ---
if len(holdings_report) < 3:
    candidate_tickers = ["TNA", "LABU", "TSLL", "GDXU", "NRGU", "SQQQ", "FNGU", "SOXL", "TQQQ"]
    for ticker_symbol in candidate_tickers:
        if any(ticker_symbol in r for r in holdings_report): continue
        
        rsi_val = get_rsi(ticker_symbol)
        if rsi_val <= 40:
            try:
                ticker = yf.Ticker(ticker_symbol)
                hist = ticker.history(period="5d")
                if not hist.empty:
                    curr = hist['Close'].iloc[-1]
                    l_price = int(curr * 1.1)
                    
                    # [수정 로직] 후보군도 RSI 25 이하일 때 1/20 투입 계산
                    if rsi_val <= 25:
                        c_signal = " 🚨[특수타격]"
                        l_budget_usd = (strike_investment * 10000 / rate)
                    else:
                        c_signal = " 🚨"
                        l_budget_usd = (investment_per_turn * 10000 / rate) / 3
                        
                    l_qty = int(l_budget_usd / l_price)
                    candidates_report.append(
                        f"• *{ticker_symbol}*{c_signal} (RSI: {rsi_val:.1f})\n"
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
• 일반 분할 금액: {investment_per_turn:,.0f}만 원
• RSI 25이하 타격액: {strike_investment:,.0f}만 원
• 남은 가용 시드: {available_seed:,.0f}만 원

📊 **보유 종목**
""" + ("\n".join(holdings_report) if holdings_report else "보유 종목 없음")

if candidates_report:
    final_report += f"\n\n🔍 **핵심 후보 정찰**\n" + "\n".join(candidates_report)

final_report += f"\n\n기준 환율: ₩{rate:.2f}"

send_telegram_message(final_report)
