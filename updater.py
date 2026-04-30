import os
import requests
import base64
from nacl import encoding, public
import time

# [보안] 새 봇 토큰은 깃허브 Secrets(TELEGRAM_TOKEN)에 반드시 넣으셔야 합니다!
TOKEN = os.environ.get("TELEGRAM_TOKEN") 
MY_CHAT_ID = "5466858773" # 사령관님 전용 ID
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
        # [핵심] 가장 최신 메시지 ID를 기억하여 중복 처리를 방지합니다.
        last_update_id = updates["result"][-1]["update_id"]
        
        # [지독한 서치 시작] 거꾸로 훑으며 사령관님의 명령을 찾습니다!
        for item in reversed(updates["result"]):
            msg_obj = item.get("message", {})
            sender_id = str(msg_obj.get("from", {}).get("id", ""))
            msg_text = msg_obj.get("text", "").strip()

            # 보안: 사령관님 ID가 아니면 지독하게 패스!
            if sender_id != MY_CHAT_ID: continue
            
            target_secret = ""
            # 명령어가 포함되어 있는지 지독하게 서치합니다.
            if msg_text.startswith("/보유"): target_secret = "MY_HOLDINGS"
            elif msg_text.startswith("/시드"): target_secret = "MY_SEED"
            elif msg_text.startswith("/매수"): target_secret = "MY_HOLDINGS" # 매수는 보유 현황 갱신

            if target_secret:
                # 명령어 부분을 떼어내고 순수 데이터만 추출합니다.
                new_data = msg_text.replace("/보유", "").replace("/시드", "").replace("/매수", "").strip()
                status = update_secret(target_secret, new_data)
                
                if status in [201, 204]:
                    # 사령관님께만 성공 보고 전송!
                    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                                  json={"chat_id": MY_CHAT_ID, "text": f"✅ [함대 보급 성공]\n📦 항목: {target_secret}\n🚀 데이터: {new_data}"})
                    
                    time.sleep(3) # 동기화 대기
                    # 리포트 즉시 발포!
                    requests.post(f"https://api.github.com/repos/{REPO}/actions/workflows/{WORKFLOW_FILE}/dispatches",
                                  headers={"Authorization": f"token {GH_TOKEN}"}, json={"ref": "main"})
                break # 최신 명령어 하나를 처리했으면 루프 종료!

        # [소탕] 처리한 메시지까지 지워버려 해커의 잔상을 소탕합니다!
        requests.get(f"{url}?offset={last_update_id + 1}")

if __name__ == "__main__":
    main()
