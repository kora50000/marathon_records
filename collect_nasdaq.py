import os
import datetime
import yfinance as yf
from supabase import create_client

# GitHub Secrets(금고)에서 주입된 환경 변수를 시스템에서 안전하게 읽어옵니다.
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("🚨 필수 환경 변수(SUPABASE_URL 또는 SUPABASE_KEY)가 설정되지 않았습니다. GitHub Secrets를 확인하세요.")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def collect_nasdaq_futures():
    print(f"[{datetime.datetime.now()}] 나스닥 100 선물 데이터 수집 시작...")
    
    # 미니 나스닥 100 선물 티커
    ticker = yf.Ticker("NQ=F")
    
    # 당일 1분 단위 데이터 가져오기
    df = ticker.history(period="1d", interval="1m")
    if df.empty:
        print("데이터를 가져오지 못했습니다. 장 마감 또는 휴장일일 수 있습니다.")
        return
        
    # 현재 가격 (가장 최신 분봉의 종가)
    current_price = float(df['Close'].iloc[-1])
    
    # 아침 7시 개장 가격 (당일 첫 번째 분봉의 시가)
    open_price = float(df['Open'].iloc[0]) 
    
    # 아침 시가 대비 현재 실시간 누적 변동률 (%) 계산
    change_percent = ((current_price - open_price) / open_price) * 100
    
    # 정각 및 30분 단위 셋업을 위한 시간 라벨 처리
    now = datetime.datetime.now()
    if 25 <= now.minute <= 40:
        time_label = now.strftime("%H:30")
    else:
        time_label = now.strftime("%H:00")
        
    data = {
        "time_label": time_label,
        "price": round(current_price, 2),
        "change_percent": round(change_percent, 2)
    }
    
    # Supabase 테이블에 인서트
    supabase.table("nasdaq_futures_history").insert(data).execute()
    print(f"✅ Supabase 적재 완료: {data}")

if __name__ == "__main__":
    collect_nasdaq_futures()
