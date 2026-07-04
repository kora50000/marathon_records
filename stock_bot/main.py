import os
import datetime
import requests
from supabase import create_client

# 환경 변수 로드
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_part1_global_briefing():
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # [교정] 주말 테스트 및 평일 유연성을 위해 오늘 날짜 대신 '최근 누적된 8개 데이터'를 가져옵니다.
        # 이렇게 하면 오늘 데이터가 없어도 이전 거래일의 흐름을 보여주며 멈추지 않습니다.
        response = supabase.table("nasdaq_futures_history") \
            .select("time_label, change_percent, created_at") \
            .order("created_at", desc=True) \
            .limit(8) \
            .execute()
            
        if not response.data:
            print("⚠️ Supabase에 나스닥 선물 데이터가 아예 비어있습니다. 1부를 건너뜁니다.")
            return

        # 최근 순으로 가져온 데이터를 시간 순서대로 재정렬 (07:00 -> 14:30)
        ordered_data = sorted(response.data, key=lambda x: x.get('created_at', ''))

        nasdaq_lines = []
        last_pct = 0.0

        for row in ordered_data:
            label = row['time_label']
            pct = float(row['change_percent'])
            emoji = "🟩" if pct >= 0 else "🟥"
            sign = "+" if pct > 0 else ""
            nasdaq_lines.append(f"  ⏱️ {label} : {sign}{pct:.2f}% {emoji}")
            last_pct = pct

        nasdaq_text = "\n".join(nasdaq_lines)

        # 투자 전략 한마디 도출
        if last_pct >= 0.4:
            ai_analysis_hint = "오후 장중 나스닥 선물이 견고하게 우상향하고 있습니다. 글로벌 투자 심리가 양호하므로 외인 수급이 뒷받침되는 개별 종목의 종가 베팅 진입을 긍정적으로 검토하기 좋은 타이밍입니다."
        elif last_pct <= -0.4:
            ai_analysis_hint = "미국 선물의 하락 압력이 거세지고 있습니다. 밤사이 미국 본장의 리스크가 존재하므로 오늘 종가 베팅은 적극적인 진입을 자제하고 보수적으로 비중을 낮추는 것을 추천합니다."
        else:
            ai_analysis_hint = "현재 글로벌 지수가 뚜렷한 방향성 없이 보합권에 머물러 있습니다. 무리한 베팅보다는 곧 발송될 2부 리스트 중 외인 가집계 수급 유입이 확실한 압도적 주도주 위주로만 방어적인 종가 베팅을 고려하세요."

        # 1부 메시지 폼 완성
        message_1 = f"""📊 [종가 매매 가이드] 1부: 글로벌 시장 동향
📅 브리핑 가동일시: {datetime.date.today().isoformat()} 14:35

───────────────────────
🇺🇸 나스닥 100 선물 최근 누적 추이 (Tech 100)
───────────────────────
{nasdaq_text}

💡 [AI 투자 힌트]
{ai_analysis_hint}
"""

        # 텔레그램 전송
        telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(telegram_url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message_1})
        print("📢 1부 글로벌 동향 메시지 발송 완료")

    except Exception as e:
        # 혹시나 수파베이스나 1부에서 에러가 나더라도 
        # 전체 프로그램이 뻗지 않고 로그만 남긴 뒤 2부로 넘어가게 만드는 안전장치입니다.
        print(f"🚨 1부 가동 중 예상치 못한 에러 발생: {e}")
        print("정상적인 2부 수급 발송을 위해 계속 진행합니다.")

# 메인 실행 영역
if __name__ == "__main__":
    # 1부: 글로벌 선물 지수 브리핑 먼저 쏘기
    send_part1_global_briefing()
    
    # 2부: 기존 형님이 짜두신 종목투자자 가집계 수급 리스트 코드가 이어서 실행됩니다.
    # (여기에 기존 메인 로직 함수 명을 넣어두시면 됩니다)
    print("이어서 2부 개별 종목 수급 분석을 시작합니다...")
    # 예: send_domestic_stock_supply_list()
