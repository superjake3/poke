import urllib.request
import os
import json
from bs4 import BeautifulSoup

# 설정값
url = "https://pokemongolive.com/ko/news"
# 디스코드 웹훅 주소는 원하시는 채널에 맞춰 새로 생성해서 넣어주세요
webhook_url = "여기에_포켓몬GO_전용_웹훅_주소를_넣으세요"
id_file = "pogo_last_id.txt"

try:
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as res:
        soup = BeautifulSoup(res, 'html.parser')
    
    # 포켓몬 GO 뉴스 페이지 구조에 맞춘 카드 추출
    # 가장 최신 카드는 항상 첫 번째 a 태그입니다.
    first_card = soup.find('a', href=lambda href: href and href.startswith('/ko/news/'))
    
    if not first_card:
        print("뉴스를 찾을 수 없습니다.")
        exit()

    # 링크(URL)를 고유 ID로 사용 (뉴스마다 고유하므로 가장 확실함)
    news_link = "https://pokemongolive.com" + first_card['href']
    news_title = first_card.get_text(strip=True)
    
    # 이전 기록과 비교
    if os.path.exists(id_file):
        with open(id_file, "r") as f:
            last_link = f.read().strip()
    else:
        last_link = ""

    if news_link != last_link:
        print(f"새 소식 발견: {news_title}")
        
        # 디스코드 전송
        discord_message = {
            "content": "📢 **포켓몬 GO 새로운 소식이 올라왔습니다!**",
            "embeds": [
                {
                    "title": news_title,
                    "description": "아래 링크에서 상세 내용을 확인하세요.",
                    "url": news_link,
                    "color": 16776960 # 포켓몬 GO 컬러
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
        
        # ID 저장
        with open(id_file, "w") as f:
            f.write(news_link)
    else:
        print("새로운 업데이트가 없습니다.")

except Exception as e:
    print(f"포켓몬 GO 체크 중 에러: {e}")
