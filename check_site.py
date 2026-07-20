import urllib.request

print("--- 사이트 감시 시스템 가동 ---")

try:
    url = "https://www.naver.com"
    status = urllib.request.urlopen(url).getcode()
    print(f"[{url}] 접속 성공! (상태 코드: {status})")
except Exception as e:
    print(f"사이트 접속 중 에러 발생: {e}")
