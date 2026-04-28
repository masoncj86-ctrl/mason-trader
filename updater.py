import os
import requests
import base64
from nacl import encoding, public
import time

TOKEN = "8278038145:AAFa9Y-RJhcW12SKtGOnqGNQW7w1q9ErPCY"
CHAT_ID = "5466858773"
REPO = "masoncj86-ctrl/mason-trader"
GH_TOKEN = os.environ.get("GH_TOKEN")
WORKFLOW_FILE = "main.yml" 

def update_secret(secret_name, new_value):
    # [지독한 교정] 양끝 공백만 제거하고 내부 구조는 절대 건드리지 않습니다.
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
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    updates = requests.get(url).json()
    
    if updates.get("result"):
        for item in reversed(updates["result"]):
            msg = item.get("message", {}).get("text", "").strip()
            if not msg: continue

            target_secret = ""
            if msg.startswith("/보유"): target_secret = "MY_HOLDINGS"
            elif msg.startswith("/시드"): target_secret = "MY_SEED"
            # ... (중략)

            if target_secret:
                # [핵심] 명령어 뒤의 데이터를 통째로 정확하게 분리합니다.
                new_data = msg.replace("/보유", "").replace("/시드", "").strip()
                status = update_secret(target_secret, new_data)
                
                if status in [201, 204]:
                    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                                  json={"chat_id": CHAT_ID, "text": f"✅ [함대 최신화] {target_secret}가 '{new_data}'로 지독하게 갱신되었습니다!"})
                    time.sleep(3) # 금고 동기화 대기
                    # 리포트 자동 실행
                    requests.post(f"https://api.github.com/repos/{REPO}/actions/workflows/{WORKFLOW_FILE}/dispatches",
                                  headers={"Authorization": f"token {GH_TOKEN}"}, json={"ref": "main"})
                break

if __name__ == "__main__":
    main()
