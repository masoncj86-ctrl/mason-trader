import os
import requests
import base64
from nacl import encoding, public

# --- [사령관 기밀 데이터] ---
TOKEN = "8278038145:AAFa9Y-RJhcW12SKtGOnqGNQW7w1q9ErPCY"
CHAT_ID = "5466858773"
REPO = "masoncj86-ctrl/mason-trader"
GH_TOKEN = os.environ.get("GH_TOKEN")

def update_secret(secret_name, new_value):
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    key_url = f"https://api.github.com/repos/{REPO}/actions/secrets/public-key"
    res_key = requests.get(key_url, headers=headers).json()
    
    public_key = public.PublicKey(res_key['key'].encode("utf-8"), encoding.Base64Encoder())
    sealed_box = public.SealedBox(public_key)
    encrypted_value = base64.b64encode(sealed_box.encrypt(new_value.encode("utf-8"))).decode("utf-8")
    
    secret_url = f"https://api.github.com/repos/{REPO}/actions/secrets/{secret_name}"
    data = {"encrypted_value": encrypted_value, "key_id": res_key['key_id']}
    return requests.put(secret_url, headers=headers, json=data).status_code

def main():
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    updates = requests.get(url).json()
    
    if updates.get("result"):
        # [지독한 교정] 최근 메시지부터 거꾸로 훑으며 명령어를 찾습니다!
        for item in reversed(updates["result"]):
            msg = item.get("message", {}).get("text", "")
            
            if msg.startswith("/보유"):
                new_data = msg.replace("/보유", "").strip()
                status = update_secret("MY_HOLDINGS", new_data)
                print(f"보유 현황 업데이트 완료: {status}")
                break # 최신 명령 하나만 처리하고 지독하게 종료!

            elif msg.startswith("/시드"):
                new_seed = msg.replace("/시드", "").strip()
                update_secret("MY_SEED", new_seed)
                break

            elif msg.startswith("/대출"):
                new_debt = msg.replace("/대출", "").strip()
                update_secret("MY_DEBT", new_debt)
                break

if __name__ == "__main__":
    main()
