import os
import requests
import base64
from nacl import encoding, public

# --- [사령관 기밀 데이터] ---
TOKEN = "8278038145:AAFa9Y-RJhcW12SKtGOnqGNQW7w1q9ErPCY"
CHAT_ID = "5466858773"
REPO = "masoncj86-ctrl/mason-trader"
GH_TOKEN = os.environ.get("GH_TOKEN")

def send_telegram_confirm(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, data=payload)

def update_secret(secret_name, new_value):
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    key_url = f"https://api.github.com/repos/{REPO}/actions/secrets/public-key"
    res_key = requests.get(key_url, headers=headers).json()
    
    public_key = public.PublicKey(res_key['key'].encode("utf-8"), encoding.Base64Encoder())
    sealed_box = public.SealedBox(public_key)
    encrypted_value = base64.b64encode(sealed_box.encrypt(new_value.encode("utf-8"))).decode("utf-8")
    
    secret_url = f"https://api.github.com/repos/{REPO}/actions/secrets/{secret_name}"
    data = {"encrypted_value": encrypted_value, "key_id": res_key['key_id']}
    res = requests.put(secret_url, headers=headers, json=data)
    return res.status_code

def main():
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    updates = requests.get(url).json()
    
    if updates.get("result"):
        # 최근 메시지 10개부터 거꾸로 훑으며 명령어 탐색
        for item in reversed(updates["result"]):
            message_obj = item.get("message", {})
            msg = message_obj.get("text", "")
            
            if not msg: continue

            target_secret = ""
            if msg.startswith("/보유"): target_secret = "MY_HOLDINGS"
            elif msg.startswith("/시드"): target_secret = "MY_SEED"
            elif msg.startswith("/대출"): target_secret = "MY_DEBT"
            elif msg.startswith("/수익"): target_secret = "MY_PROFIT" # 수익 업데이트도 추가!

            if target_secret:
                new_data = msg.split(" ", 1)[1] if " " in msg else ""
                if not new_data: # 공백 없이 붙여 쓴 경우 대비
                    new_data = msg.replace(f"/{target_secret.split('_')[1].lower()}", "").strip()
                
                status = update_secret(target_secret, new_data)
                
                if status in [201, 204]:
                    confirm = f"✅ [함대 최신화 성공]\n📦 항목: {target_secret}\n🚀 데이터: {new_data}"
                else:
                    confirm = f"❌ 업데이트 실패 (코드: {status})\nGH_TOKEN 권한을 지독하게 확인하십시오!"
                
                send_telegram_confirm(confirm)
                break # 최신 명령 하나만 처리 후 종료

if __name__ == "__main__":
    main()
