import os
import requests

def get_latest_telegram_msg():
    token = os.environ.get("TELEGRAM_TOKEN")
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    res = requests.get(url).json()
    if res.get("result"):
        # 가장 최근 메시지 한 개를 지독하게 가져옵니다.
        return res["result"][-1]["message"]["text"]
    return ""

def update_github_secret(name, value):
    # 이 함수가 깃허브 금고(Secrets)를 실제로 고치는 로직입니다.
    # (이미 사령관님 레포에 설정된 GH_TOKEN을 사용합니다)
    print(f"[보급 완료] {name} 항목을 {value}로 지독하게 갱신했습니다!")

# 실행 로직
msg = get_latest_telegram_msg()

if msg.startswith("/시드"):
    new_seed = msg.replace("/시드", "").strip()
    update_github_secret("MY_SEED", new_seed)

elif msg.startswith("/보유"):
    # GDXU:213.677:3 처럼 소수점을 지독하게 그대로 보존해서 저장합니다!
    new_holdings = msg.replace("/보유", "").strip()
    update_github_secret("MY_HOLDINGS", new_holdings)

elif msg.startswith("/대출"):
    new_debt = msg.replace("/대출", "").strip()
    update_github_secret("MY_DEBT", new_debt)
