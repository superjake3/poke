import json
import os
import re
import requests
from bs4 import BeautifulSoup

# 대상 게시판 URL 및 검색 키워드
TARGET_URL = "https://bbs.ruliweb.com/family/242/board/300017"
KEYWORD = "포켓몬"
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
DATA_FILE = "notified_ids.txt"


def load_notified_ids():
  if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
      return set(f.read().splitlines())
  return set()


def save_notified_ids(notified_ids):
  with open(DATA_FILE, "w", encoding="utf-8") as f:
    f.write("\n".join(notified_ids))


def check_board():
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
          " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
      )
  }

  response = requests.get(TARGET_URL, headers=headers)
  if response.status_code != 200:
    print(f"페이지 로드 실패: {response.status_code}")
    return

  soup = BeautifulSoup(response.text, "html.parser")
  rows = soup.select("tr.table_body")

  notified_ids = load_notified_ids()
  new_notified = False

  for row in reversed(rows):  # 오래된 게시글부터 검사
    title_elem = row.select_one("a.subject_link")
    if not title_elem:
      continue

    title = title_elem.text.strip()
    link = title_elem["href"]

    # 글 번호(ID) 추출
    match = re.search(r"/read/(\d+)", link)
    if not match:
      continue
    post_id = match.group(1)

    # 이미 알림을 보낸 게시글이면 패스
    if post_id in notified_ids:
      continue

    # 키워드 검사 (제목 기준)
    if KEYWORD in title:
      send_discord_message(title, link)
      notified_ids.add(post_id)
      new_notified = True

  if new_notified:
    save_notified_ids(notified_ids)


def send_discord_message(title, url):
  payload = {
      "content": f"🚨 **[포켓몬 관련 새 글 알림]**\n**제목:** {title}\n**링크:** {url}"
  }
  response = requests.post(WEBHOOK_URL, json=payload)
  if response.status_code == 204:
    print(f"알림 전송 성공: {title}")
  else:
    print(f"알림 전송 실패: {response.status_code}")


if __name__ == "__main__":
  check_board()
