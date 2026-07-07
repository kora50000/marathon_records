import os
import requests
from datetime import datetime, timezone, timedelta
import yfinance as yf
from supabase import create_client

# GitHub Secrets(금고)에서 주입된 환경 변수를 시스템에서 안전하게 읽어옵니다.
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("🚨 필수 환경 변수(SUPABASE_URL 또는 SUPABASE_KEY)가 설정되지 않았습니다. GitHub Secrets를 확인하세요.")

# 수파베이스 클라이언트 초기화
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def send_part1_global_briefing():
    try:
        # 🌐 [타임존 설정] GitHub Actions 서버(UTC) 기준 타임존을 한국 시간(KST, UTC+9)으로 강제 고정
        kst = timezone(timedelta(hours=9))
        now_kst = datetime.now(kst)
        today_str = now_kst.date().isoformat()
        
        print(f"[{now_kst.strftime('%Y-%m-%d %H:%M:%S')}] 나스닥 100 선물 데이터 실시간 수집 및 브리핑 시작...")

        # ==========================================
        # 1. 실시간 나스닥 선물 데이터 수집 & DB 적재 (형님의 기존 로직)
        # ==========================================
        ticker = yf.Ticker("NQ=F")
        
        # 당일 1분 단위 데이터 가져오기
        df = ticker.history(period="1d", interval="1m")
        if df.empty:
            print("⚠️ yfinance 데이터를 가져오지 못했습니다. 장 마감 또는 휴장일일 수 있습니다. 기존 DB 데이터로 브리핑을 시도합니다.")
        else:
            # 현재 가격 (가장 최신 분봉의 종가)
            current_price = float(df['Close'].iloc[-1])
            
            # 아침 7시 개장 가격 (당일 첫 번째 분봉의 시가)
            open_price = float(df['Open'].iloc[0]) 
            
            # 아침 시가 대비 현재 실시간 누적 변동률 (%) 계산
            change_percent = ((current_price - open_price) / open_price) * 100
            
            # 정각 및 30분 단위 셋업을 위한 시간 라벨 처리 (한국 시각 기준 계산)
            if 25 <= now_kst.minute <= 40:
                time_label = now_kst.strftime("%H:30")
            else:
                time_label = now_kst.strftime("%H:00")
                
            insert_data = {
                "time_label": time_label,
                "price": round(current_price, 2),
                "change_percent": round(change_percent, 2),
                "created_at": now_kst.isoformat()  # KST 기준 타임스탬프 삽입
            }
            
            # Supabase 테이블에 실시간 인서트(Insert) 실행
            supabase.table("nasdaq_futures_history").insert(insert_data).execute()
            print(f"✅ Supabase 실시간 적재 완료: {insert_data}")

        # ==========================================
        # 2. 당일 누적 데이터 조회 및 가공 (브리핑 로직)
        # ==========================================
        # '오늘 아침 7시부터 현재까지' 누적된 당일 데이터만 한국 시간 날짜 기준으로 조회
        response = supabase.table("nasdaq_futures_history") \
            .select("time_label, change_percent, created_at") \
            .gte("created_at", today_str) \
            .order("created_at", desc=True) \
            .execute()
            
        if not response.data:
            print(f"⚠️ {today_str} 오늘 누적된 나스닥 선물 데이터가 DB에 존재하지 않습니다. 1부를 건너뜁니다.")
            return

        # 아침부터 오후까지 시간 순서대로 정렬 (07:00 -> 14:35)
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

        # ==========================================
        # 3. 나스닥 최종 변동률 기준 AI 투자 힌트 도출
        # ==========================================
        if last_pct >= 0.4:
            ai_analysis_hint = "오후 장중 나스닥 선물이 견고하게 우상향하고 있습니다. 글로벌 투자 심리가 양호하므로 외인 수급이 뒷받침되는 개별 주도주의 종가 베팅 진입을 긍정적으로 검토하기 좋은 타이밍입니다."
        elif last_pct <= -0.4:
            ai_analysis_hint = "미국 선물의 하락 압력이 거세지고 있습니다. 밤사이 미국 본장의 리스크가 존재하므로 오늘 종가 베팅은 적극적인 진입을 자제하고 보수적으로 비중을 낮추는 것을 추천합니다."
        else:
            ai_analysis_hint = "현재 글로벌 지수가 뚜렷한 방향성 없이 보합권에 머물러 있습니다. 무리한 베팅보다는 곧 발송될 2부 리스트 중 외인/기관 가집계 수급 유입이 확실한 압도적 주도주 위주로만 방어적인 종가 베팅을 고려하세요."

        # 1부 메시지 폼 구성
        message_1 = f"""📊 [종가 매매 가이드] 1부: 글로벌 시장 동향
📅 브리핑 가동일시: {today_str} {now_kst.strftime('%H:%M')} (KST)

───────────────────────
🇺🇸 나스닥 100 선물 당일 누적 추이 (Tech 100)
───────────────────────
{nasdaq_text}

💡 [AI 투자 힌트]
{ai_analysis_hint}
"""

        # ==========================================
        # 4. 텔레그램 발송
        # ==========================================
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
            print("⚠️ 텔레그램 환경 변수가 없습니다. 메시지 발송을 생략합니다.")
            return

        telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message_1}
        
        res = requests.post(telegram_url, json=payload)
        if res.status_code == 200:
            print("📢 1부 글로벌 동향 메시지 텔레그램 발송 완료")
        else:
            print(f"❌ 1부 텔레그램 발송 실패 (상태코드: {res.status_code})")

    except Exception as e:
        print(f"🚨 1부 가동 중 에러 발생했으나 2부 진행을 위해 무시합니다: {e}")

# 메인 실행 영역
if __name__ == "__main__":
    print("🚀 스크립트 메인 엔진 가동")
    send_part1_global_briefing()
