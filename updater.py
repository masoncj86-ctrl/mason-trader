import requests
import base64
import os
from nacl import encoding, public

# --- [사령관 기밀 데이터 및 경로 직결] ---
TOKEN = "8278038145:AAFa9Y-RJhcW12SKtGOnqGNQW7w1q9ErPCY"
CHAT_ID = "5466858773"
REPO = "masoncj86-ctrl/mason-trader"
GH_TOKEN = os.environ.get("GH_TOKEN") # 깃허브 시크릿에 등록한 마스터키

def update_secret(secret_name, new_value):
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    # 1. 레포 공개키 획득
    key_url = f"https://api.github.com/repos/{REPO}/actions/secrets/public-key"
    res_key = requests.get(key_url, headers=headers).json()
    
    # 2. 값 암호화 (나트륨 암호화)
    public_key = public.PublicKey(res_key['key'].encode("utf-8"), encoding.Base64Encoder())
    sealed_box = public.SealedBox(public_key)
    encrypted_value = base64.b64encode(sealed_box.encrypt(new_value.encode("utf-8"))).decode("utf-8")
    
    # 3. 깃허브 시크릿 금고에 저장
    secret_url = f"https://api.github.com/repos/{REPO}/actions/secrets/{secret_name}"
    data = {"encrypted_value": encrypted_value, "key_id": res_key['key_id']}
    return requests.put(secret_url, headers=headers, json=data).status_code

def main():
    # 텔레그램 명령 정찰
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    updates = requests.get(url).json()
    
    if updates.get("result"):
        last_msg = updates["result"][-1]["message"]["text"]
        
        # 사령관님의 "/보유" 명령 포착 (예: /보유 TSLL:12.5:1500)
        if last_msg.startswith("/보유"):
            new_data = last_msg.replace("/보유", "").strip()
            status = update_secret("MY_HOLDINGS", new_data)
            
            if status in [201, 204]:
                confirm = f"✅ [함대 최신화 성공]\n📦 지독하게 반영된 데이터: {new_data}"
            else:
                confirm = f"❌ 업데이트 실패 (코드: {status})\n지독하게 GH_TOKEN 권한을 확인하십시오!"
                
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                          data={"chat_id": CHAT_ID, "text": confirm})

if __name__ == "__main__":
    main()
