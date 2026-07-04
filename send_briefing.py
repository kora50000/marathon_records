import os
import datetime
import requests
from supabase import create_client

# 한국투자증권 키를 포함한 모든 보안 키를 환경 변수에서 안전하게 수신합니다.
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# 필요 시 한국투자증권 연동을 위한 변수 유지
KIS_APP_KEY = os.environ.get("KIS_APP_KEY")
KIS_APP_SECRET = os.environ.get("KIS_APP_SECRET")

if not all([SUPABASE_URL, SUPABASE_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID]):
    raise ValueError("🚨 필수 환경 변수가 누락되었습니다. GitHub Secrets 설정을 재확인하세요.")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def send_part1_global_briefing():
    # 1. 금일 날짜 기준으로 Supabase에서 시간대별 나스닥 선물 기록 로드
    today_str = datetime.date.today().isoformat()
    response = supabase.table("nasdaq_futures_history") \
        .select("time_label, change_percent") \
        .gte("created_at", today_str) \
        .order("created_at") \
        .execute()
        
    if not response.data:
        print("오늘 누적된 나스닥 선물 데이터가 데이터베이스에 존재하지 않습니다.")
        return

    nasdaq_lines = []
    last_pct = 0.0

    for row in response.data:
        label = row['time_label']
        pct = float(row['change_percent'])
        emoji = "🟩" if pct >= 0 else "🟥"
        sign = "+" if pct > 0 else ""
        nasdaq_lines.append(f"  ⏱️ {label} : {sign}{pct:.2f}% {emoji}")
        last_pct = pct

    nasdaq_text = "\n".join(nasdaq_lines)

    # 2. 나스닥 최종 퍼센트 기준 투자 전략 한마디 도출 (알고리즘형 Fallback 전략)
    if last_pct >= 0.4:
        ai_analysis_hint = "오후 장중 나스닥 선물이 견고하게 우상향하고 있습니다. 글로벌 투자 심리가 양호하므로 실적 기대주나 외인 수급이 뒷받침되는 개별 종목의 종가 베팅 진입을 긍정적으로 검토하기 좋은 타이밍입니다."
    elif last_pct <= -0.4:
        ai_analysis_hint = "미국 선물의 하락 압력이 거세지고 있습니다. 밤사이 미국 본장의 리스크가 존재하므로 오늘 종가 베팅은 적극적인 진입을 자제하고 보수적으로 비중을 낮추는 것을 추천합니다."
    else:
        ai_analysis_hint = "현재 글로벌 지수가 뚜렷한 방향성 없이 보합권에 머물러 있습니다. 무리한 베팅보다는 곧 발송될 2부 리스트 중 외인 가집계 수급 유입이 확실한 압도적 주도주 위주로만 방어적인 종가 베팅을 고려하세요."

    # 3. 1부 메시지 폼 완성
    message_1 = f"""📊 [종가 매매 가이드] 1부: 글로벌 시장 동향
📅 기준일시: {today_str} 14:35

───────────────────────
🇺🇸 나스닥 100 선물 실시간 누적 추이 (Tech 100)
───────────────────────
{nasdaq_text}

💡 [AI 투자 힌트]
{ai_analysis_hint}
"""

    # 4. 안전하게 수신한 토큰과 방 번호로 1부 브리핑 전송
    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message_1
    }
    requests.post(telegram_url, json=payload)
    print("📢 1부 글로벌 동향 메시지 발송 완료")

# 14:35에 작동하는 기존 전체 실행 흐름 최상단에 이식합니다.
if __name__ == "__main__":
    # 1부 브리핑 발송 (나스닥 100 중심)
    send_part1_global_briefing()
    
    # 2부: 기존에 형님이 구현해 두신 개별 기업 수급 리스트 발송 로직이 이어서 실행됩니다.
    # send_domestic_stock_supply_list()
  
