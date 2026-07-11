import datetime
import os
import requests


def send_telegram_message():
    # 깃허브 시크릿(환경변수)에서 토큰과 챗 ID를 가져옵니다.
    TOKEN = os.environ.get("TELEGRAM_TOKEN")
    CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

    # 시크릿 값이 제대로 안 들어왔을 경우 예외 처리
    if not TOKEN or not CHAT_ID:
        print(
            "에러: TELEGRAM_TOKEN 또는 TELEGRAM_CHAT_ID 환경변수가 설정되지 않았습니다."
        )
        return

    # 한국 시간 기준 현재 시간 구하기 (UTC+9)
    now = datetime.datetime.now(
        datetime.timezone(datetime.timedelta(hours=9))
    )
    current_time_str = now.strftime("%Y-%m-%d %H:%M:%S")

    message = f"🔔 [시크릿 테스트] 현재 한국 시간은 {current_time_str} 입니다."

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}

    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print("시크릿을 이용한 메시지 발송 성공!")
    else:
        print(f"발송 실패: {response.text}")


if __name__ == "__main__":
    send_telegram_message()
