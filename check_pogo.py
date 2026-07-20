import urllib.request
import os
import json
from bs4 import BeautifulSoup

# 설정값
url = "https://pokemongolive.com/ko/news"
# 알려주신 웹훅 주소 적용
webhook_url = "https://discord.com/api/webhooks/1528660768319602728/lD0pEeYLtLTgJrJDj2f4ZcBTLiEbcfFBUREPaXwN-Jnie8McL9a6HWq3-rGLA6H1XgJg"
id_file = "pogo_last_id.txt"

try:
    # 1. 포켓몬 GO 뉴스 페이지 접속
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as res:
        soup = BeautifulSoup(res, 'html.parser')
    
    # 2. 첫 번째 뉴스 카드 찾기
    first_card = soup.find('a', href=lambda href: href and href.startswith('/ko/news/'))
    
    if not first_card:
        print("뉴스를 찾을 수 없습니다.")
        exit()

    # 3. 뉴스 고유 링크 및 제목 추출
    news_link = "https://pokemongolive.com" + first_card['href']
    news_title = first_card.get_text(strip=True)
    
    # 4. 이전 기록과 비교하여 새로운 소식인지 확인
    if os.path.exists(id_file):
        with open(id_file, "r") as f:
            last_link = f.read().strip()
    else:
        last_link = ""

    if news_link != last_link:
        print(f"새 소식 발견: {news_title}")
        
        # 디스코드 알림 메시지 구성
        discord_message = {
            "content": "📢 **포켓몬 GO 새로운 소식이 올라왔습니다!**",
            "embeds": [
                {
                    "title": news_title,
                    "description": "아래 링크에서 상세 내용을 확인하세요.",
                    "url": news_link,
                    "color": 16776960
                }
            ]
        }
        
        # 웹훅 전송
        payload = json.dumps(discord_message).encode('utf-8')
        req_discord = urllib.request.Request(
            webhook_url, 
            data=payload, 
            headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'}
        )
        urllib.request.urlopen(req_discord)
        
        # 확인된 링크를 파일에 저장
        with open(id_file, "w") as f:
            f.write(news_link)
    else:
        print("새로운 업데이트가 없습니다.")

except Exception as e:
    print(f"포켓몬 GO 체크 중 에러: {e}")
