import os
import datetime
import requests
from supabase import create_client

# 금고에서 값 꺼내오기
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# 🚨 [보안 검증용 로그 추출]
print("🔍 [보안 체크] GitHub 금고 연결 상태를 점검합니다...")
print(f"  - SUPABASE_URL 존재 여부: {'⭕ 연결됨' if SUPABASE_URL else '❌ 비어있음'}")
print(f"  - SUPABASE_KEY 존재 여부: {'⭕ 연결됨' if SUPABASE_KEY else '❌ 비어있음'}")
print(f"  - TELEGRAM_CHAT_ID 존재 여부: {'⭕ 연결됨' if TELEGRAM_CHAT_ID else '❌ 비어있음'}")

if TELEGRAM_BOT_TOKEN:
    # 토큰이 있으면 앞 4글자만 찍어서 진짜 값이 들어왔는지 확인 (보안 안전)
    print(f"  - TELEGRAM_BOT_TOKEN 확인: ⭕ 정상 로드됨 (앞글자: {TELEGRAM_BOT_TOKEN[:4]}...)")
else:
    print("  - TELEGRAM_BOT_TOKEN 확인: ❌ 값이 비어있습니다!")

if not all([SUPABASE_URL, SUPABASE_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID]):
    print("🚨 [위험] 필수 보안 키 중 일부가 누락되어 텔레그램 발송을 중단합니다.")
