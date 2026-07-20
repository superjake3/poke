import urllib.request
import os
import hashlib
import json

url = "https://www.serebii.net/"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
# 보내주신 디스코드 웹훅 주소
webhook_url = "https://discord.com/api/webhooks/1528643446494068746/JIBzGh-4QDn3jeYZZzDX1HJIIuotYNkOKb9mOuuHeHQzgtW75yTODXgawBVshXZ815kI"

try:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as response:
        html_content = response.read().decode('iso-8859-1', errors='ignore')
    
    current_hash = hashlib.md5(html_content.encode('utf-8')).hexdigest()
    file_path = "last_hash.txt"
    
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            old_hash = f.read().strip()
    else:
        old_hash = ""
        
    if current_hash != old_hash:
        print("★ [Serebii] 새로운 뉴스가 업데이트되었습니다! ★")
        
        # 디스코드 웹훅으로 보낼 메시지 구성
        message = {
            "content": "📢 **Serebii 새로운 포켓몬 뉴스 업데이트!**\n지금 세레비 네트에 새로운 소식이 올라왔습니다. 확인해보세요!\n👉 https://www.serebii.net/"
        }
        payload = json.dumps(message).encode('utf-8')
        
        req_discord = urllib.request.Request(
            webhook_url, 
            data=payload, 
            headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'}
        )
        # 디스코드로 알림 전송 실행
        urllib.request.urlopen(req_discord)
        
        # 변경된 지문 저장
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(current_hash)
    else:
        print("새로운 업데이트가 없습니다.")

except Exception as e:
    print(f"Serebii 체크 중 에러 발생: {e}")
