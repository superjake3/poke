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
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # [핵심 수정] table 태그로 제한하지 않고, Serebii가 사용하는 모든 뉴스 클래스(div, td, table 등 불문)를 싹 다 찾습니다.
    news_elements = soup.find_all(class_=['foomain', 'dextable', 'post'])
    news_text = ""
    
    if news_elements:
        # 상위 3개 블록의 텍스트를 모아서 오늘의 최신 뉴스 내용을 넉넉하게 확보합니다.
        extracted_texts = []
        for elem in news_elements[:3]:
            text = elem.get_text(separator="\n").strip()
            if len(text) > 20:  # 너무 짧은 자투리 텍스트는 제외
                extracted_texts.append(text)
        news_text = "\n\n".join(extracted_texts)
    
    # 만약 위 방식으로도 놓칠 경우를 대비한 최후의 백업 (메인 본문 영역 통째로 추출)
    if not news_text or len(news_text) < 20:
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.extract()
        main_area = soup.find(id=['content', 'main', 'page']) or soup.find('main')
        if main_area:
            news_text = main_area.get_text(separator="\n").strip()
        else:
            news_text = soup.get_text(separator="\n").strip()

    # 줄바꿈 및 불필요한 반복 안내문 정제
    lines = [line.strip() for line in news_text.splitlines() if line.strip()]
    cleaned_lines = []
    for line in lines:
        if "This update will be amended" in line:
            continue
        cleaned_lines.append(line)
        
    # 디스코드 전송을 위해 핵심 상위 30줄만 딱 잘라내기
    final_news = "\n".join(cleaned_lines[:30])

    if not final_news or len(final_news) < 10:
        final_news = "최신 뉴스 텍스트를 추출하는 데 실패했습니다. 사이트 구조를 확인해 주세요."

    # 변경 감지용 해시
    current_hash = hashlib.md5(final_news.encode('utf-8')).hexdigest()
    file_path = "last_hash.txt"
    
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            old_hash = f.read().strip()
    else:
        old_hash = ""
        
    if current_hash != old_hash:
        print("★ [Serebii] 최신 뉴스 감지 성공! 번역 및 전송 시작 ★")
        
        # 글자수 제한 안정권 조절 (디스코드 텍스트 제한 2000자 대비 안전하게 800자)
        if len(final_news) > 800:
            final_news = final_news[:800] + "\n...(이하 생략)..."
        
        # 구글 번역
        try:
            translated_text = GoogleTranslator(source='en', target='ko').translate(final_news)
        except Exception as translation_error:
            translated_text = f"번역 중 오류가 발생했습니다.\n\n[원문 미리보기]\n{final_news}"
        
        # 디스코드 전송
        discord_message = {
            "content": "📢 **Serebii 최신 포켓몬 뉴스 업데이트!**",
            "embeds": [
                {
                    "title": "오늘의 최신 소식 (자동 번역)",
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
        print("새로운 업데이트 소식이 없습니다.")

except Exception as e:
    print(f"Serebii 체크 중 에러 발생: {e}")
