import urllib.request
import os
import hashlib
import json
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
from datetime import datetime
import zoneinfo

url = "https://www.serebii.net/"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
webhook_url = "https://discord.com/api/webhooks/1528643446494068746/JIBzGh-4QDn3jeYZZzDX1HJIIuotYNkOKb9mOuuHeHQzgtW75yTODXgawBVshXZ815kI"

try:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as response:
        html_content = response.read().decode('iso-8859-1', errors='ignore')
    
    # 한국 시간(KST) 기준으로 현재 요일 계산 (Monday, Tuesday...)
    kst = zoneinfo.ZoneInfo("Asia/Seoul")
    current_day_str = datetime.now(kst).strftime('%A')
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Serebii의 요일별 헤더(foomain클래스의 td태그 내부 앵커 등) 찾기
    # 캡처화면 기준 각 요일의 시작점은 'Monday:', 'Sunday:' 등의 텍스트를 포함하는 영역입니다.
    target_news_html = ""
    
    # foomain 테이블들을 순회하며 오늘 요일의 뉴스 박스 찾기
    tables = soup.find_all('table', class_='foomain')
    
    for table in tables:
        table_text = table.get_text()
        # 오늘 요일(예: Monday)로 시작하는 뉴스 섹션을 조준
        if current_day_str in table_text:
            # 해당 요일 테이블 내부의 실제 텍스트 내용들을 정제해서 결합
            paragraphs = table.find_all(['p', 'div', 'td'])
            if paragraphs:
                target_news_html = "\n".join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
            else:
                target_news_html = table.get_text(separator="\n").strip()
            break
            
    # 만약 요일 매칭에 실패하면 백업으로 첫 번째 foomain 사용
    if not target_news_html and tables:
        target_news_html = tables[0].get_text(separator="\n").strip()

    # 줄바꿈 정제 및 텍스트 슬라이싱
    lines = [line.strip() for line in target_news_html.splitlines() if line.strip()]
    
    # 불필요한 상단 요일 타이틀이나 반복 안내문이 있다면 일부 필터링하고 핵심 내용 조립
    cleaned_lines = []
    for line in lines:
        if "This update will be amended" in line or "In The Games Department" in line or "In The Anime Department" in line:
            continue
        cleaned_lines.append(line)
        
    news_text = "\n".join(cleaned_lines[:30]) # 오늘 뉴스 내용 최대 30줄 확보

    if not news_text:
        news_text = "오늘 날짜의 뉴스 콘텐츠를 추출하지 못했습니다. 사이트에서 직접 확인해주세요."

    # 변경 감지용 해시 (오늘 요일의 뉴스 텍스트 기준으로만 비교하여 불필요한 전체 알림 방지)
    current_hash = hashlib.md5(news_text.encode('utf-8')).hexdigest()
    file_path = "last_hash.txt"
    
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            old_hash = f.read().strip()
    else:
        old_hash = ""
        
    if current_hash != old_hash:
        print(f"★ [Serebii] {current_day_str} 새로운 내용 감지! 번역 시작 ★")
        
        # 글자수 제한 안정권 조절
        if len(news_text) > 800:
            news_text = news_text[:800] + "\n...(이하 생략)..."
        
        # 구글 번역
        try:
            translated_text = GoogleTranslator(source='en', target='ko').translate(news_text)
        except Exception as translation_error:
            translated_text = f"번역 중 오류가 발생했습니다.\n\n[원문 미리보기]\n{news_text}"
        
        # 디스코드 전송
        discord_message = {
            "content": f"📢 **Serebii {current_day_str} 포켓몬 뉴스 업데이트!**",
            "embeds": [
                {
                    "title": f"오늘의 최신 소식 (자동 번역)",
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
        print("오늘 업데이트된 새로운 소식이 없습니다.")

except Exception as e:
    print(f"Serebii 체크 중 에러 발생: {e}")
