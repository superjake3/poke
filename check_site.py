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
    
    current_hash = hashlib.md5(html_content.encode('utf-8')).hexdigest()
    file_path = "last_hash.txt"
    
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            old_hash = f.read().strip()
    else:
        old_hash = ""
        
    if current_hash != old_hash:
        print("★ [Serebii] 새로운 뉴스 감지! 내용 추출 및 번역 시작 ★")
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # [수정포인트] 특정 클래스를 못 찾더라도, 메인 콘텐츠가 들어있는 중앙 영역을 단계별로 탐색합니다.
        news_text = ""
        
        # 1순위: 기존 foomain 클래스 테이블 찾기
        news_table = soup.find('table', class_='foomain')
        if news_table:
            # 뉴스 테이블 안의 주요 텍스트 단락들을 추출
            paragraphs = news_table.find_all(['p', 'div', 'td'])
            if paragraphs:
                news_text = "\n".join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
            else:
                news_text = news_table.get_text(separator="\n").strip()
        
        # 2순위: foomain이 없을 경우 메인 본문 div 영역 통째로 긁기
        if not news_text or len(news_text) < 10:
            main_div = soup.find('div', id='main') or soup.find('main')
            if main_div:
                news_text = main_div.get_text(separator="\n").strip()
        
        # 3순위: 그것도 실패하면 페이지 전체에서 쓸모없는 태그(스크립트 등)를 지우고 글자만 추출
        if not news_text or len(news_text) < 10:
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.extract()
            news_text = soup.get_text(separator="\n").strip()

        # 줄바꿈이 너무 과도하게 들어간 부분 깔끔하게 정리하기
        lines = [line.strip() for line in news_text.splitlines() if line.strip()]
        news_text = "\n".join(lines[:20]) # 핵심 상위 20줄만 딱 끊어서 가져오기
        
        if not news_text:
            news_text = "사이트 구조 변경으로 텍스트를 추출하지 못했습니다. 링크를 확인해 주세요."
        
        # 글자수 제한 안정권 조절
        if len(news_text) > 700:
            news_text = news_text[:700] + "\n...(이하 생략)..."
        
        # 구글 번역
        try:
            translated_text = GoogleTranslator(source='en', target='ko').translate(news_text)
        except Exception as translation_error:
            translated_text = f"번역 중 오류가 발생했습니다.\n\n[원문 미리보기]\n{news_text}"
        
        # 디스코드 전송
        discord_message = {
            "content": "📢 **Serebii 새로운 포켓몬 뉴스 업데이트!**",
            "embeds": [
                {
                    "title": "포켓몬 최신 소식 (자동 번역)",
                    "description": f"{translated_text}",
                    "url": "https://www.serebii.net/",
                    "color": 65280
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
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(current_hash)
    else:
        print("새로운 업데이트가 없습니다.")

except Exception as e:
    print(f"Serebii 체크 중 에러 발생: {e}")
