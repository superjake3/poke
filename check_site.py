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
    
    # 1. 사이트 전체 텍스트 추출 및 줄바꿈 정리
    raw_text = soup.get_text(separator='\n')
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    
    # 요일 키워드 목록
    days = ["Monday:", "Tuesday:", "Wednesday:", "Thursday:", "Friday:", "Saturday:", "Sunday:"]
    
    start_idx = -1
    end_idx = len(lines)
    
    # 2. 가장 첫 번째로 등장하는 요일(오늘 뉴스 시작점) 찾기
    for i, line in enumerate(lines):
        if any(line.startswith(day) for day in days):
            start_idx = i
            break
            
    # 3. 두 번째로 등장하는 요일(어제 뉴스 시작점)을 찾아 오늘 하루 치 영역만 정확히 잘라내기
    if start_idx != -1:
        for i in range(start_idx + 1, len(lines)):
            if any(lines[i].startswith(day) for day in days):
                end_idx = i
                break
        
        # 오늘 요일 섹션의 모든 라인을 가져옴 (15줄/30줄 등의 줄 수 제한 없음!)
        today_lines = lines[start_idx : end_idx]
        cleaned_lines = []
        
        for line in today_lines:
            # 뉴스와 상관없는 사이트 관리용 반복 문구, 부서명 태그만 깔끔하게 제거
            if "This update will be amended" in line: continue
            if line.startswith("Last Update:"): continue
            if line.startswith("Edit @"): continue
            if "In The Games Department" in line: continue
            if "In The Anime Department" in line: continue
            if "In The Manga Department" in line: continue
            cleaned_lines.append(line)
            
        # 가독성을 위해 문단 사이를 넉넉하게 띄워서 합치기
        final_news = "\n\n".join(cleaned_lines)
    else:
        final_news = ""

    if not final_news or len(final_news) < 10:
        final_news = "뉴스 콘텐츠를 스캔하지 못했습니다. 사이트를 직접 확인해 주세요."

    # 4. 디스코드 최대 글자 수 한계선(4096자) 에러를 방지하기 위한 넉넉한 안전장치 (3800자)
    if len(final_news) > 3800:
        final_news = final_news[:3800] + "\n\n...(디스코드 글자 수 제한으로 이하 생략)..."

    # 변경 감지용 해시 (오늘 자 전체 뉴스 데이터 기준)
    current_hash = hashlib.md5(final_news.encode('utf-8')).hexdigest()
    file_path = "last_hash.txt"
    
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            old_hash = f.read().strip()
    else:
        old_hash = ""
        
    if current_hash != old_hash:
        print("★ [Serebii] 오늘 하루 치 전체 뉴스 감지 성공! 번역 시작 ★")
        
        # 구글 번역 (대용량 텍스트 번역 수행)
        try:
            translated_text = GoogleTranslator(source='en', target='ko').translate(final_news)
        except Exception as translation_error:
            translated_text = f"번역 중 오류가 발생했습니다.\n\n[원문 미리보기]\n{final_news}"
        
        discord_message = {
            "content": "📢 **Serebii 오늘 자 포켓몬 뉴스 전체 업데이트!**",
            "embeds": [
                {
                    "title": "오늘의 최신 뉴스 전체 (자동 번역)",
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
