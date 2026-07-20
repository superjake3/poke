import urllib.request
import os
import hashlib
import json
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator

url = "https://www.serebii.net/"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
webhook_url = "https://discord.com/api/webhooks/1528643446494068746/JIBzGh-4QDn3jeYZZzDX1HJIIuotYNkOKb9mOuuHeHQzgtW75yTODXgawBVshXZ815kI"

try:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as response:
        html_content = response.read().decode('iso-8859-1', errors='ignore')
    
    # 1. 변경 감지용 해시 체크
    current_hash = hashlib.md5(html_content.encode('utf-8')).hexdigest()
    file_path = "last_hash.txt"
    
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            old_hash = f.read().strip()
    else:
        old_hash = ""
        
    if current_hash != old_hash:
        print("★ [Serebii] 새로운 뉴스 감지! 내용 추출 및 번역 시작 ★")
        
        # 2. 최신 뉴스 텍스트 긁어오기 (Serebii는 메인 뉴스가 'foomain' 클래스 테이블에 들어감)
        soup = BeautifulSoup(html_content, 'html.parser')
        news_table = soup.find('table', class_='foomain')
        
        if news_table:
            news_text = news_table.get_text(separator="\n").strip()
        else:
            news_text = "최신 뉴스 텍스트 파싱에 실패했습니다. 사이트에서 직접 확인해주세요."
        
        # 디스코드 텍스트 제한(2000자) 및 번역 안정성을 위해 글자수 조절
        if len(news_text) > 800:
            news_text = news_text[:800] + "\n...(이하 생략)..."
        
        # 3. 구글 번역기를 이용해 영어를 한글로 번역
        try:
            translated_text = GoogleTranslator(source='en', target='ko').translate(news_text)
        except Exception as translation_error:
            translated_text = f"번역 중 오류가 발생했습니다. 원문을 참고하세요.\n\n[원문 미리보기]\n{news_text}"
        
        # 4. 디스코드 예쁜 박스(Embed) 형태로 메시지 구성
        discord_message = {
            "content": "📢 **Serebii 새로운 포켓몬 뉴스 업데이트!**",
            "embeds": [
                {
                    "title": "포켓몬 최신 소식 (자동 번역)",
                    "description": f"{translated_text}",
                    "url": "https://www.serebii.net/",
                    "color": 65280 # 초록색 포인트 컬러
                }
            ]
        }
        
        payload = json.dumps(discord_message).encode('utf-8')
        req_discord = urllib.request.Request(
            webhook_url, 
            data=payload, 
            headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'}
        )
        urllib.request.urlopen(req_discord)
        
        # 변경된 지문 저장
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(current_hash)
    else:
        print("새로운 업데이트가 없습니다.")

except Exception as e:
    print(f"Serebii 체크 중 에러 발생: {e}")
