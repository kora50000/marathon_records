import os
import requests

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_telegram_message(text_content):
    """
    기존 형님의 텔레그램 발송 함수 내부를 이 구조로 교체해 주세요.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("🚨 [텔레그램 에러] 토큰이나 챗 ID가 메모리에 없습니다.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text_content,
        "parse_mode": "HTML" # 혹시 메시지에 <b> 태그 같은 마크업이 있다면 활성화, 없으면 빼도 됨
    }
    
    try:
        # 텔레그램 서버에 요청을 보내고 응답을 받습니다.
        response = requests.post(url, json=payload)
        
        # 💡 [핵심] 성공이든 실패든 텔레그램 서버가 보낸 진짜 답변을 로그에 찍습니다.
        print(f"📡 [텔레그램 응답 상태코드]: {response.status_code}")
        print(f"💬 [텔레그램 서버 자백]: {response.text}")
        
        if response.status_code == 200:
            print("✅ 텔레그램 서버로 메시지가 정상 배달되었습니다!")
        else:
            print("❌ 텔레그램 전송 실패! 서버 응답을 확인하세요.")
            
    except Exception as e:
        print(f"🚨 [네트워크 에러] 텔레그램 API 호출 중 예외 발생: {e}")
