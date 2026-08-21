import requests
from bs4 import BeautifulSoup
import os
import hashlib

# 하입비스트 포켓몬 태그 URL
HYPEBEAST_URL = "https://hypebeast.kr/tags/pokemon"

# 디스코드 웹훅 URL
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1540234633814482964/TfUHMKDYpOZxRAlhReg6gmIYN0Hh71ng0IN0SivBk9b9_arR_Kn9YGx3Tq4lX6MHXrzD"

# 기록용 파일
HASH_FILE = "last_hypebeast_hash.txt"

def get_latest_post():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(HYPEBEAST_URL, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 하입비스트 대표 게시글 카드 구조 탐색
        post = soup.select_one(".post-box, article, .p-list-item, div[data-post-id]")
        
        if not post:
            # fallback: 태그 페이지 내 가장 첫 번째 주요 링크 추출
            links = soup.find_all("a", href=True)
            for link in links:
                href = link['href']
                text = link.get_text(strip=True)
                if "/20" in href and len(text) > 5:
                    return text, href
            return None, None

        # 제목 및 링크 추출
        title_elem = post.select_one(".post-box-title, .title, h2, h3") or post.find("a")
        title = title_elem.get_text(strip=True) if title_elem else "하입비스트 포켓몬 새 글"
        
        link_elem = post if post.name == "a" else post.find("a")
        link = link_elem["href"] if link_elem and "href" in link_elem.attrs else HYPEBEAST_URL
        
        if not link.startswith("http"):
            link = "https://hypebeast.kr" + link

        return title, link

    except Exception as e:
        print(f"하입비스트 크롤링 중 오류 발생: {e}")
        return None, None

def send_discord_alarm(title, link):
    payload = {
        "content": f"🚨 **[하입비스트] 포켓몬 관련 새 글이 등록되었습니다!**\n\n📌 **제목:** {title}\n🔗 **링크:** {link}"
    }
    try:
        res = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        res.raise_for_status()
        print("디스코드 알림 전송 완료!")
    except Exception as e:
        print(f"디스코드 전송 실패: {e}")

def main():
    title, link = get_latest_post()
    
    if not title or not link:
        print("새로운 게시글을 찾을 수 없습니다.")
        return

    # 식별용 해시값 생성 (제목+링크 조합)
    current_hash = hashlib.md5(f"{title}{link}".encode('utf-8')).hexdigest()

    # 기존 해시값 읽기
    last_hash = ""
    if os.path.exists(HASH_FILE):
        with open(HASH_FILE, "r", encoding="utf-8") as f:
            last_hash = f.read().strip()

    # 변경사항 확인
    if current_hash != last_hash:
        print(f"새 게시글 감지: {title}")
        send_discord_alarm(title, link)
        
        # 새로운 해시 저장
        with open(HASH_FILE, "w", encoding="utf-8") as f:
            f.write(current_hash)
    else:
        print("새로운 게시글이 없습니다.")

if __name__ == "__main__":
    main()
