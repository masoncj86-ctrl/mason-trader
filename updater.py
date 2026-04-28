import os
import requests
import base64
from nacl import encoding, public
import time

# --- [사령관 기밀 데이터] ---
TOKEN = "8278038145:AAFa9Y-RJhcW12SKtGOnqGNQW7w1q9ErPCY"
CHAT_ID = "5466858773"
REPO = "masoncj86-ctrl/mason-trader"
GH_TOKEN = os.environ.get("GH_TOKEN")
WORKFLOW_FILE = "main.yml" 

def send_telegram_confirm(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, data=payload)

def trigger_report_workflow():
    # 보급 완료 후 새 보고서를 뽑기 위한 지독한 연쇄 호출
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    url = f"https://api.github.com/repos/{REPO}/actions/workflows/{WORKFLOW_FILE}/dispatches"
    requests.post(url, headers=headers, json={"ref": "main"})

def update_secret(secret_name, new_value):
    # [지독한 정밀화] NRGU 등 티커의 숨은 공백과 콤마를 싹 제거합니다.
    clean_value = new_value.strip().replace(" ", "")
    
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    key_url = f"https://api.github.com/repos/{REPO}/actions/secrets/public-key"
    res_key = requests.get(key_url, headers=headers).json()
    
    public_key = public.PublicKey(res_key['key'].encode("utf-8"), encoding.Base64Encoder())
    sealed_box = public.SealedBox(public_key)
    encrypted_value = base64.b64encode(sealed_box.encrypt(clean_value.encode("utf-8"))).decode("utf-8")
    
    secret_url = f"https://api.github.com/repos/{REPO}/actions/secrets/{secret_name}"
    data = {"encrypted_value": encrypted_value, "key_id": res_key['key_id']}
    res = requests.put(secret_url, headers=headers, json=data)
    return res.status_code

def main():
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    updates = requests.get(url).json()
    
    if updates.get("result"):
        for item in reversed(updates["result"]):
            msg = item.get("message", {}).get("text", "").strip()
            if not msg: continue

            # [1] 즉시 보고 명령어
            if msg == "/보고":
                trigger_report_workflow()
                send_telegram_confirm("🚀 [즉시 보고 체계 가동] 최신 데이터를 불러옵니다...")
                break

            # [2] 보급 명령어 처리
            target_secret = ""
            if msg.startswith("/보유"): target_secret = "MY_HOLDINGS"
            elif msg.startswith("/시드"): target_secret = "MY_SEED"
            elif msg.startswith("/대출"): target_secret = "MY_DEBT"
            elif msg.startswith("/수익"): target_secret = "MY_PROFIT"

            if target_secret:
                new_data = msg.split(" ", 1)[1] if " " in msg else msg[3:].strip()
                status = update_secret(target_secret, new_data)
                
                if status in [201, 204]:
                    send_telegram_confirm(f"✅ [보급 성공] {target_secret} 갱신 완료!")
                    # [지독한 자동화] 보급 성공 즉시 보고서 생성 트리거!
                    time.sleep(2) # 금고가 닫힐 시간을 잠시 줍니다.
                    trigger_report_workflow()
                break

if __name__ == "__main__":
    main()
