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
    
    # Serebii에서 가장 위에 있는 첫 번째 뉴스 테이블(최신 요일)만 정확히 타겟팅
    first_news_table = soup.find('table', class_='foomain')
    
    if first_news_table:
        # 주요 텍스트 태그들을 줄바꿈 단위로 정밀 추출
        paragraphs = first_news_table.find_all(['p', 'div', 'td'])
        if paragraphs:
            news_text = "\n".join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
        else:
            news_text = first_news_table.get_text(separator="\n").strip()
    else:
        news_text = ""

    # 텍스트 라인 정리 및 스팸성 문구 필터링
    lines = [line.strip() for line in news_text.splitlines() if line.strip()]
    cleaned_lines = []
    
    for line in lines:
        # 상단 반복 안내 텍스트 제거
        if "This update will be amended" in line:
            continue
        cleaned_lines.append(line)
        
    # 핵심 상위 25줄 조립
    final_news = "\n".join(cleaned_lines[:25])

    if not final_news or len(final_news) < 10:
        final_news = "최신 뉴스 텍스트를 추출하는 데 실패했습니다. 사이트 구조를 확인해 주세요."

    # 변경 감지용 해시 (가장 최신 뉴스 덩어리의 내용 기준으로만 비교)
    current_hash = hashlib.md5(final_news.encode('utf-8')).hexdigest()
    file_path = "last_hash.txt"
    
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            old_hash = f.read().strip()
    else:
        old_hash = ""
        
    if current_hash != old_hash:
        print("★ [Serebii] 최신 뉴스 박스 감지! 번역 및 전송 시작 ★")
        
        # 글자수 제한 안정권 조절
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
