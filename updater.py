import os
import requests
import base64
from nacl import encoding, public
import time

# [보안 1순위] 토큰은 반드시 깃허브 시크릿에서 가져와야 합니다!
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
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    updates = requests.get(url).json()
    
    if updates.get("result"):
        # 가장 최신 메시지 ID 기억 (플러시용)
        last_update_id = updates["result"][-1]["update_id"]
        
        for item in reversed(updates["result"]):
            msg_obj = item.get("message", {})
            sender_id = str(msg_obj.get("from", {}).get("id", "")) # 보낸 사람 ID 추출
            msg = msg_obj.get("text", "").strip()
            
            if not msg: continue

            # [지독한 방화벽] 사령관님 ID가 아니면 러시아 해커든 누구든 즉시 무시!
            if sender_id != MY_CHAT_ID:
                print(f"⚠️ 침입자(ID: {sender_id})의 명령을 지독하게 차단했습니다.")
                continue

            target_secret = ""
            if msg.startswith("/보유"): target_secret = "MY_HOLDINGS"
            elif msg.startswith("/시드"): target_secret = "MY_SEED"
            elif msg.startswith("/매수"): target_secret = "MY_HOLDINGS" # 증분 로직용 (필요시)

            if target_secret:
                new_data = msg.replace("/보유", "").replace("/시드", "").replace("/매수", "").strip()
                status = update_secret(target_secret, new_data)
                
                if status in [201, 204]:
                    # 사령관님께만 성공 보고 발송
                    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                                  json={"chat_id": MY_CHAT_ID, "text": f"✅ [함대 최신화] {target_secret} 갱신 완료! 리포트 발포합니다!"})
                    
                    time.sleep(3) # 금고 동기화 대기
                    
                    # [공격력 유지] 리포트 즉시 실행 명령!
                    requests.post(f"https://api.github.com/repos/{REPO}/actions/workflows/{WORKFLOW_FILE}/dispatches",
                                  headers={"Authorization": f"token {GH_TOKEN}"}, json={"ref": "main"})
                break

        # [지독한 소탕] 처리한 메시지까지 서버에서 지워버려 유령 명령 방지!
        requests.get(f"{url}?offset={last_update_id + 1}")

if __name__ == "__main__":
    main()
