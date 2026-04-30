import os
import requests
import base64
from nacl import encoding, public
import time

# [지독한 보안] 토큰은 깃허브 Secrets(TELEGRAM_TOKEN)에 넣으셨죠? ㅋㅋㅋ
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

    # [지독한 서치 로직] 봇에게 온 모든 메시지를 가져옵니다.
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    try:
        updates = requests.get(url).json()
    except:
        return

    if updates.get("result"):
        # 가장 마지막 업데이트 ID (청소용)
        last_update_id = updates["result"][-1]["update_id"]
        
        # 최신 메시지부터 거꾸로 뒤집어서(reversed) 서치!
        for item in reversed(updates["result"]):
            msg_obj = item.get("message", {})
            sender_id = str(msg_obj.get("from", {}).get("id", ""))
            msg_text = msg_obj.get("text", "").strip()

            # 1. 사령관님이 보낸 메시지인가?
            if sender_id != MY_CHAT_ID:
                continue

            # 2. 명령어 키워드가 포함되어 있는가?
            target_secret = ""
            command_key = ""
            if "/보유" in msg_text: 
                target_secret = "MY_HOLDINGS"
                command_key = "/보유"
            elif "/시드" in msg_text: 
                target_secret = "MY_SEED"
                command_key = "/시드"

            if target_secret:
                # [정밀 추출] 명령어 이후의 데이터만 지독하게 발라냅니다.
                # 예: "/보유 LABU:2..." -> "LABU:2..."
                new_data = msg_text.split(command_key)[-1].strip()
                
                if new_data:
                    status = update_secret(target_secret, new_data)
                    
                    if status in [201, 204]:
                        # 성공 시 사령관님께 즉시 보고!
                        confirm_text = f"✅ [함대 보급 완료]\n📦 {target_secret} 갱신\n🚀 데이터: {new_data}"
                        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                                      json={"chat_id": MY_CHAT_ID, "text": confirm_text})
                        
                        time.sleep(3) # 동기화 대기
                        # 즉시 리포트 발사!
                        requests.post(f"https://api.github.com/repos/{REPO}/actions/workflows/{WORKFLOW_FILE}/dispatches",
                                      headers={"Authorization": f"token {GH_TOKEN}"}, json={"ref": "main"})
                        
                        # [핵심] 성공했으면 더 이상 예전 메시지를 뒤지지 않고 종료!
                        break

        # [소탕] 처리가 끝났으니, 읽은 메시지들은 텔레그램 서버에서 지독하게 비웁니다.
        requests.get(f"{url}?offset={last_update_id + 1}")

if __name__ == "__main__":
    main()
