import os
import requests
import base64
from nacl import encoding, public
import time

# [보안] 텔레그램 토큰과 깃허브 토큰은 Secrets에서 안전하게!
TOKEN = os.environ.get("TELEGRAM_TOKEN") 
MY_CHAT_ID = "5466858773" 
REPO = "masoncj86-ctrl/mason-trader"
GH_TOKEN = os.environ.get("GH_TOKEN")
WORKFLOW_FILE = "main.yml" 

def update_secret(secret_name, new_value):
    clean_value = new_value.strip()
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
    if not TOKEN: return
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    updates = requests.get(url).json()
    
    if updates.get("result"):
        last_update_id = updates["result"][-1]["update_id"]
        for item in reversed(updates["result"]):
            msg_obj = item.get("message", {})
            sender_id = str(msg_obj.get("from", {}).get("id", ""))
            msg_text = msg_obj.get("text", "").strip()

            if sender_id != MY_CHAT_ID: continue
            
            target_secret = ""
            cmd = ""
            if "/보유" in msg_text: 
                target_secret, cmd = "MY_HOLDINGS", "/보유"
            elif "/시드" in msg_text: 
                target_secret, cmd = "MY_SEED", "/시드"

            if target_secret:
                new_data = msg_text.split(cmd)[-1].strip()
                status = update_secret(target_secret, new_data)
                
                if status in [201, 204]:
                    # 1. 먼저 보급 완료 보고!
                    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                                  json={"chat_id": MY_CHAT_ID, "text": f"✅ [함대 보급 완료] {target_secret} 갱신되었습니다!"})
                    
                    # 2. [지독한 핵심] 금고 정보가 리포트 서버에 전달될 시간을 줍니다! (5초 대기)
                    print("🔄 데이터 동기화 대기 중 (5초)...")
                    time.sleep(5) 
                    
                    # 3. 즉시 리포트 강제 발사! (이제는 최신 정보가 나갑니다 ㅋㅋㅋ)
                    requests.post(f"https://api.github.com/repos/{REPO}/actions/workflows/{WORKFLOW_FILE}/dispatches",
                                  headers={"Authorization": f"token {GH_TOKEN}"}, json={"ref": "main"})
                break 

        requests.get(f"{url}?offset={last_update_id + 1}")

if __name__ == "__main__":
    main()
